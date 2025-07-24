#!/usr/bin/env python3
"""Utility functions for the hooks module."""

import sys
import threading
from pathlib import Path
from typing import Optional


class VenvFinder:
    """Centralized virtual environment finder with thread-safe caching."""

    _cached_venv: Optional[Path] = None
    _lock = threading.Lock()

    @classmethod
    def find_venv(cls) -> Optional[Path]:
        """Find the appropriate Python virtual environment (thread-safe).

        Priority order:
        1. .claude/venv in any parent directory
        2. .venv in hook directory
        3. .venv in project root
        4. System Python (returns None)

        Returns:
            Path to Python executable in venv, or None for system Python
        """
        # Quick check without lock for performance
        if cls._cached_venv is not None:
            return cls._cached_venv
        
        # Acquire lock for cache modification
        with cls._lock:
            # Double-check pattern to avoid race conditions
            if cls._cached_venv is not None:
                return cls._cached_venv

            # 1. Check for .claude/venv in parent directories
            current = Path.cwd()
            while current != current.parent:
                claude_venv = current / ".claude" / "venv" / "bin" / "python"
                if claude_venv.exists():
                    cls._cached_venv = claude_venv
                    return claude_venv
                current = current.parent

            # 2. Check for .venv in current directory
            local_venv = Path(".venv") / "bin" / "python"
            if local_venv.exists():
                cls._cached_venv = local_venv
                return local_venv

            # 3. Check for .venv in project root
            project_root = cls._find_project_root()
            if project_root:
                root_venv = project_root / ".venv" / "bin" / "python"
                if root_venv.exists():
                    cls._cached_venv = root_venv
                    return root_venv

            # 4. No venv found, use system Python
            return None

    @staticmethod
    def _find_project_root() -> Optional[Path]:
        """Find project root by looking for git directory."""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        return None

    @classmethod
    def get_python_executable(cls) -> str:
        """Get the Python executable path."""
        venv = cls.find_venv()
        return str(venv) if venv else sys.executable

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the cached venv path (thread-safe)."""
        with cls._lock:
            cls._cached_venv = None


class ConfigLoader:
    """Centralized configuration loader for hooks."""

    @staticmethod
    def load_config(config_path: Path) -> dict:
        """Load configuration from a JSON file.

        Args:
            config_path: Path to config.json file

        Returns:
            Configuration dictionary or empty dict if not found
        """
        if not config_path.exists():
            return {}

        try:
            import json

            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Handle both direct config and settings nested structure
                if "settings" in data:
                    return data["settings"]
                return data
        except (json.JSONDecodeError, IOError):
            return {}

    @staticmethod
    def find_hook_config(hook_path: Path) -> dict:
        """Find and load configuration for a hook.

        Looks for config.json in:
        1. Same directory as hook
        2. Parent directory

        Args:
            hook_path: Path to hook file

        Returns:
            Configuration dictionary
        """
        # Check same directory
        config_path = hook_path.parent / "config.json"
        if config_path.exists():
            return ConfigLoader.load_config(config_path)

        # Check parent directory
        config_path = hook_path.parent.parent / "config.json"
        if config_path.exists():
            return ConfigLoader.load_config(config_path)

        return {}
