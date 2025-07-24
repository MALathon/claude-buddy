"""Claude Buddy Hooks System.

This package provides the hook interface and infrastructure for extending
Claude Code with custom behavior.
"""

from .base import BaseHook, ClaudeHook, ExternalHookAdapter, validate_hook
from .logger import get_logger, log_exception, set_log_file
from .manager import HookManager, get_manager, create_hook, list_available_hooks
from .utils import VenvFinder, ConfigLoader

__all__ = [
    "BaseHook",
    "ClaudeHook",
    "ExternalHookAdapter",
    "HookManager",
    "VenvFinder",
    "ConfigLoader",
    "get_logger",
    "log_exception",
    "set_log_file",
    "get_manager",
    "validate_hook",
    "create_hook",
    "list_available_hooks",
]

__version__ = "1.0.0"
