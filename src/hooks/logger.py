#!/usr/bin/env python3
"""Logging configuration for hooks module."""

import logging
import sys
from pathlib import Path
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the hooks module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Create handler
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Check for debug mode
        import os
        if os.environ.get("CLAUDE_DEBUG"):
            logger.setLevel(logging.DEBUG)
    
    return logger


def log_exception(logger: logging.Logger, message: str, exc: Exception) -> None:
    """Log an exception with context.
    
    Args:
        logger: Logger instance
        message: Context message
        exc: Exception to log
    """
    logger.error(f"{message}: {type(exc).__name__}: {str(exc)}", exc_info=True)


# Create module-level logger
_module_logger = get_logger(__name__)


def set_log_file(log_path: Optional[Path] = None) -> None:
    """Set up file logging for hooks.
    
    Args:
        log_path: Path to log file (default: .claude/logs/hooks.log)
    """
    if log_path is None:
        # Find .claude directory
        current = Path.cwd()
        while current != current.parent:
            claude_dir = current / ".claude"
            if claude_dir.exists():
                log_path = claude_dir / "logs" / "hooks.log"
                break
            current = current.parent
        
        if log_path is None:
            _module_logger.warning("Could not find .claude directory for logs")
            return
    
    # Create log directory
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create file handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    
    # Use same formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Add to all existing loggers
    for name in logging.Logger.manager.loggerDict:
        if name.startswith("hooks.") or name == __name__:
            logger = logging.getLogger(name)
            logger.addHandler(file_handler)
    
    _module_logger.info(f"Logging to file: {log_path}")