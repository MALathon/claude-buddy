#!/usr/bin/env python3
"""Base interface for Claude Buddy hooks."""

from abc import ABC, abstractmethod
from typing import (
    Any,
    ContextManager,
    Dict,
    Optional,
    Protocol,
    Tuple,
    runtime_checkable,
)


@runtime_checkable
class ConcurrencyManager(Protocol):
    """Protocol for concurrency manager that hooks can use."""

    def can_acquire_resource(self, pool_name: str) -> bool:
        """Check if a resource can be acquired."""
        ...

    def acquire_resource(
        self,
        pool_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> ContextManager[bool]:
        """Acquire a resource for exclusive use."""
        ...


@runtime_checkable
class ClaudeHook(Protocol):
    """Standard interface for all Claude Buddy hooks.

    This protocol defines the required methods that all hooks must implement,
    whether they're built-in, adapted from external tools, or custom implementations.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        concurrency_manager: Optional[ConcurrencyManager] = None,
    ) -> None:
        """Initialize hook with configuration.

        Args:
            config: Hook-specific configuration from config.json
            concurrency_manager: Optional concurrency manager for resource control
        """
        ...

    def process_event(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Process a Claude Code event.

        Args:
            event_data: Event information including:
                - tool_name: Name of the tool (Edit, Write, etc.)
                - tool_input: Tool parameters (file_path, etc.)
                - event_type: PreToolUse or PostToolUse
                - metadata: Additional context (timestamp, etc.)

        Returns:
            Tuple of (should_continue, message):
                - should_continue: True to allow operation, False to block
                - message: User-facing message (can be empty string)
        """
        ...

    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema for configuration validation.

        Returns:
            JSON schema dictionary describing valid configuration options
        """
        ...
    
    def cleanup(self) -> None:
        """Clean up any resources (subprocesses, connections, etc.).
        
        This method is called when the hook is being destroyed.
        It MUST properly terminate any subprocesses or connections.
        """
        ...


class BaseHook(ABC):
    """Abstract base class for hooks that provides common functionality."""

    def __init__(
        self,
        config: Dict[str, Any],
        concurrency_manager: Optional[ConcurrencyManager] = None,
    ) -> None:
        """Initialize hook with configuration and optional concurrency manager."""
        self.config = config
        self.enabled = config.get("enabled", True)
        self.concurrency_manager = concurrency_manager

    @abstractmethod
    def process_event(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Process a Claude Code event."""
        pass

    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema for configuration validation."""
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Whether this hook is enabled",
                    "default": True,
                }
            },
        }
    
    def cleanup(self) -> None:
        """Clean up any resources. Override if needed."""
        pass

    def is_applicable(self, event_data: Dict[str, Any]) -> bool:
        """Check if this hook should process the given event.

        Override this method to add custom filtering logic.

        Args:
            event_data: Event information

        Returns:
            True if hook should process this event
        """
        return self.enabled


class ExternalHookAdapter(BaseHook):
    """Base adapter class for integrating external tools."""

    def __init__(
        self,
        config: Dict[str, Any],
        concurrency_manager: Optional[ConcurrencyManager] = None,
    ) -> None:
        """Initialize adapter with configuration."""
        super().__init__(config, concurrency_manager)
        self.external_tool = self._initialize_external_tool(config)

    @abstractmethod
    def _initialize_external_tool(self, config: Dict[str, Any]) -> Any:  # type: ignore[ANN401]
        """Initialize the external tool with translated configuration.

        Args:
            config: Claude Buddy configuration

        Returns:
            Initialized external tool instance
        """
        pass

    @abstractmethod
    def _translate_event(self, event_data: Dict[str, Any]) -> Any:  # type: ignore[ANN401]
        """Translate Claude event to external tool format.

        Args:
            event_data: Claude Buddy event data

        Returns:
            Data in external tool's expected format
        """
        pass

    @abstractmethod
    def _translate_response(self, response: Any) -> Tuple[bool, str]:  # type: ignore[ANN401]
        """Translate external tool response to Claude format.

        Args:
            response: External tool's response

        Returns:
            Tuple of (should_continue, message)
        """
        pass

    def process_event(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Process event by delegating to external tool."""
        if not self.is_applicable(event_data):
            return True, ""

        # Translate event
        external_format = self._translate_event(event_data)

        # Call external tool
        response = self._call_external_tool(external_format)

        # Translate response
        return self._translate_response(response)

    @abstractmethod
    def _call_external_tool(self, data: Any) -> Any:  # type: ignore[ANN401]
        """Call the external tool with translated data.

        Args:
            data: Data in external tool's format

        Returns:
            External tool's response
        """
        pass


def load_hook(hook_path: str, config: Dict[str, Any]) -> Optional[ClaudeHook]:
    """Dynamically load a hook from a Python file.

    Args:
        hook_path: Path to hook Python file
        config: Hook configuration

    Returns:
        Initialized hook instance or None if loading fails
    """
    import importlib.util
    import sys
    from pathlib import Path

    try:
        # Load the module
        module_name = f"hook_{Path(hook_path).stem}"
        spec = importlib.util.spec_from_file_location(module_name, hook_path)
        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Find ClaudeHook implementation
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            # Check if it's a class that could be a hook
            if isinstance(attr, type) and hasattr(attr, "process_event"):
                # Try to instantiate it
                try:
                    instance = attr(config)
                    # Verify it has the required methods
                    if hasattr(instance, "process_event") and callable(
                        instance.process_event
                    ):
                        return instance
                except Exception:
                    # Not a valid hook class
                    continue

        return None

    except Exception:
        return None


def validate_hook(hook: Any) -> bool:  # type: ignore[ANN401]
    """Validate that an object implements the ClaudeHook interface.

    Args:
        hook: Object to validate

    Returns:
        True if object implements ClaudeHook protocol
    """
    return isinstance(hook, ClaudeHook)
