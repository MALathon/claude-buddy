#!/usr/bin/env python3
"""Unified hook manager that consolidates loading and registry functionality."""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from .base import ClaudeHook, ConcurrencyManager, validate_hook
from .logger import get_logger, log_exception
from .utils import ConfigLoader

logger = get_logger(__name__)


class HookManager:
    """Unified manager for hook loading, registration, and instantiation."""

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        """Initialize the hook manager.

        Args:
            registry_path: Path to registry.json file
        """
        self.registry_path = registry_path or (Path(__file__).parent / "registry.json")
        self.registry_data: Dict[str, Any] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Load the registry.json file."""
        if self.registry_path.exists():
            with open(self.registry_path, "r", encoding="utf-8") as f:
                self.registry_data = json.load(f)
        else:
            self.registry_data = {"version": "1.0.0", "hooks": {}, "categories": {}}

    def create_hook(
        self,
        identifier: Union[str, Path],
        config: Optional[Dict[str, Any]] = None,
        concurrency_manager: Optional[ConcurrencyManager] = None,
    ) -> Optional[ClaudeHook]:
        """Create a hook instance from registry name, file path, or module path.

        Args:
            identifier: Registry name, file path, or module path
            config: Hook configuration (if None, loads from default location)
            concurrency_manager: Optional concurrency manager

        Returns:
            Initialized hook instance or None if loading fails
        """
        # Check if it's a registry hook
        if isinstance(identifier, str) and identifier in self.registry_data.get(
            "hooks", {}
        ):
            return self._create_from_registry(identifier, config, concurrency_manager)

        # Check if it's a file path
        path = Path(identifier) if isinstance(identifier, str) else identifier
        if path.exists() and path.suffix == ".py":
            return self._create_from_path(path, config, concurrency_manager)

        # Try as module path
        if isinstance(identifier, str) and "." in identifier:
            return self._create_from_module(identifier, config, concurrency_manager)

        logger.warning(f"Failed to create hook '{identifier}': no matching loader found")
        return None

    def _create_from_registry(
        self,
        name: str,
        config: Optional[Dict[str, Any]],
        concurrency_manager: Optional[ConcurrencyManager],
    ) -> Optional[ClaudeHook]:
        """Create hook from registry entry."""
        hook_info = self.registry_data["hooks"][name]

        # Load configuration if not provided
        if config is None:
            config_file = hook_info.get("config_file")
            if config_file:
                config_path = Path(__file__).parent / config_file
                config = ConfigLoader.load_config(config_path)
            else:
                config = {}

        # Load the module
        entry_point = hook_info.get("entry_point")
        if not entry_point:
            return None

        # Handle different entry point formats
        if entry_point.endswith(".py"):
            # Direct Python file
            module_path = Path(__file__).parent / entry_point
        else:
            # Module path without .py extension
            module_path = Path(__file__).parent / f"{entry_point}.py"
            
        module = self._load_module(f"registry_{name}", module_path)
        if not module:
            logger.error(f"Failed to load module for {name} from {module_path}")
            return None

        return self._instantiate_hook(module, config, concurrency_manager)

    def _create_from_path(
        self,
        hook_path: Path,
        config: Optional[Dict[str, Any]],
        concurrency_manager: Optional[ConcurrencyManager],
    ) -> Optional[ClaudeHook]:
        """Create hook from file path."""
        # Load configuration if not provided
        if config is None:
            config = ConfigLoader.find_hook_config(hook_path)

        # Load the module
        module = self._load_module(f"path_{hook_path.stem}", hook_path)
        if not module:
            return None

        return self._instantiate_hook(module, config, concurrency_manager)

    def _create_from_module(
        self,
        module_path: str,
        config: Optional[Dict[str, Any]],
        concurrency_manager: Optional[ConcurrencyManager],
    ) -> Optional[ClaudeHook]:
        """Create hook from module path."""
        try:
            module = importlib.import_module(module_path)
            self.loaded_modules[module_path] = module
            return self._instantiate_hook(module, config or {}, concurrency_manager)
        except ImportError:
            return None

    def _load_module(self, name: str, path: Path) -> Any:
        """Load a Python module from file."""
        # Check cache
        cache_key = str(path)
        if cache_key in self.loaded_modules:
            return self.loaded_modules[cache_key]

        if not path.exists():
            logger.error(f"Module path does not exist: {path}")
            return None

        try:
            spec = importlib.util.spec_from_file_location(name, str(path))
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)

            # Cache the module
            self.loaded_modules[cache_key] = module
            return module

        except Exception as e:
            logger.error(f"Exception loading module {name} from {path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _instantiate_hook(
        self,
        module: Any,
        config: Dict[str, Any],
        concurrency_manager: Optional[ConcurrencyManager],
    ) -> Optional[ClaudeHook]:
        """Instantiate a hook from a loaded module."""
        # First check for factory function
        if hasattr(module, "create_hook") and callable(module.create_hook):
            try:
                hook = module.create_hook(config, concurrency_manager)
                if validate_hook(hook):
                    return hook
            except TypeError:
                # Try without concurrency manager
                try:
                    hook = module.create_hook(config)
                    if validate_hook(hook):
                        return hook
                except Exception:
                    pass

        # Look for hook class
        hook_class = self._find_hook_class(module)
        if hook_class:
            try:
                # Try with concurrency manager
                hook = hook_class(config, concurrency_manager)
                if validate_hook(hook):
                    return hook
            except TypeError:
                # Try without concurrency manager
                try:
                    hook = hook_class(config)
                    if validate_hook(hook):
                        return hook
                except Exception:
                    pass

        return None

    def _find_hook_class(self, module: Any) -> Optional[Type[ClaudeHook]]:
        """Find a hook class in a module."""
        excluded_names = ["BaseHook", "ClaudeHook", "ExternalHookAdapter"]

        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue

            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and hasattr(attr, "process_event")
                and hasattr(attr, "__init__")
                and attr.__name__ not in excluded_names
            ):
                return attr

        return None

    def list_hooks(self) -> Dict[str, Dict[str, Any]]:
        """List all registered hooks."""
        return self.registry_data.get("hooks", {})

    def get_hook_info(self, name: str) -> Dict[str, Any]:
        """Get metadata for a specific hook."""
        hooks = self.registry_data.get("hooks", {})
        if name not in hooks:
            raise KeyError(f"Hook '{name}' not found in registry")
        return hooks[name]

    def find_hooks_in_directory(self, directory: Union[str, Path]) -> List[str]:
        """Find available hooks in a directory."""
        directory = Path(directory)
        if not directory.is_dir():
            return []

        hook_files = []

        # Look for hook.py files
        for hook_file in directory.glob("**/hook.py"):
            if not any(part.startswith(".") for part in hook_file.parts):
                hook_files.append(str(hook_file))

        # Look for *_hook.py files
        for hook_file in directory.glob("**/*_hook.py"):
            if not any(part.startswith(".") for part in hook_file.parts):
                hook_files.append(str(hook_file))

        return sorted(hook_files)

    def reload_registry(self) -> None:
        """Reload the registry from disk."""
        self.loaded_modules.clear()
        self._load_registry()


# Global manager instance
_manager: Optional[HookManager] = None


def get_manager() -> HookManager:
    """Get the global hook manager instance."""
    global _manager
    if _manager is None:
        _manager = HookManager()
    return _manager


def create_hook(
    identifier: Union[str, Path],
    config: Optional[Dict[str, Any]] = None,
    concurrency_manager: Optional[ConcurrencyManager] = None,
) -> Optional[ClaudeHook]:
    """Create a hook instance using the global manager."""
    return get_manager().create_hook(identifier, config, concurrency_manager)


def list_available_hooks(directory: Union[str, Path] = ".") -> List[str]:
    """List available hooks in a directory."""
    return get_manager().find_hooks_in_directory(directory)
