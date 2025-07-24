#!/usr/bin/env python3
"""Unified logging system for all Claude Buddy components."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from enum import Enum
import threading
import queue

class LogLevel(Enum):
    """Log levels for different types of events."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"

class ComponentType(Enum):
    """Component types for better organization."""
    POST_TOOL_LINTER = "post_tool_linter"
    CONTEXT7 = "context7"
    TDD_GUARD = "tdd_guard"
    CONCURRENCY = "concurrency"
    SYSTEM = "system"

class UnifiedLogger:
    """Unified logger that streams readable logs for all components."""
    
    def __init__(self, base_dir: Path = None):
        """Initialize the unified logger."""
        self.base_dir = base_dir or Path("logs")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create unified log file
        today = datetime.now().strftime("%Y-%m-%d")
        self.unified_file = self.base_dir / f"claude_buddy_{today}.log"
        self.json_file = self.base_dir / f"claude_buddy_{today}.jsonl"
        
        # Stream queue for real-time display
        self.stream_queue = queue.Queue()
        self.streaming = False
        self.stream_thread = None
        
        # Component-specific files
        self.component_files = {}
        
    def log(self, 
            component: ComponentType, 
            level: LogLevel, 
            message: str, 
            operation_id: str = None,
            metadata: Dict[str, Any] = None):
        """Log a message with unified formatting."""
        
        timestamp = datetime.now()
        
        # Create log entry
        entry = {
            "timestamp": timestamp.isoformat(),
            "component": component.value,
            "level": level.value,
            "message": message,
            "operation_id": operation_id,
            "metadata": metadata or {}
        }
        
        # Format human-readable log line
        time_str = timestamp.strftime("%H:%M:%S")
        component_str = f"[{component.value.upper()}]".ljust(18)
        level_icon = self._get_level_icon(level)
        op_str = f"({operation_id})" if operation_id else ""
        
        readable_line = f"{time_str} {level_icon} {component_str} {message} {op_str}"
        
        # Write to files
        self._write_readable(readable_line)
        self._write_json(entry)
        self._write_component_file(component, readable_line)
        
        # Add to stream queue
        if self.streaming:
            self.stream_queue.put(readable_line)
    
    def _get_level_icon(self, level: LogLevel) -> str:
        """Get emoji icon for log level."""
        icons = {
            LogLevel.DEBUG: "🔍",
            LogLevel.INFO: "ℹ️ ",
            LogLevel.WARNING: "⚠️ ",
            LogLevel.ERROR: "❌",
            LogLevel.SUCCESS: "✅"
        }
        return icons.get(level, "📝")
    
    def _write_readable(self, line: str):
        """Write readable log line."""
        with open(self.unified_file, "a", encoding="utf-8") as f:
            f.write(f"{line}\n")
    
    def _write_json(self, entry: Dict[str, Any]):
        """Write JSON log entry."""
        with open(self.json_file, "a", encoding="utf-8") as f:
            f.write(f"{json.dumps(entry)}\n")
    
    def _write_component_file(self, component: ComponentType, line: str):
        """Write to component-specific file."""
        if component not in self.component_files:
            component_dir = self.base_dir / component.value
            component_dir.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            self.component_files[component] = component_dir / f"{today}.log"
        
        with open(self.component_files[component], "a", encoding="utf-8") as f:
            f.write(f"{line}\n")
    
    def start_streaming(self):
        """Start real-time log streaming to console."""
        if self.streaming:
            return
            
        self.streaming = True
        self.stream_thread = threading.Thread(target=self._stream_worker, daemon=True)
        self.stream_thread.start()
        print(f"🚀 Claude Buddy log streaming started → {self.unified_file}")
    
    def stop_streaming(self):
        """Stop real-time log streaming."""
        self.streaming = False
        if self.stream_thread:
            self.stream_thread.join(timeout=1)
    
    def _stream_worker(self):
        """Worker thread for streaming logs to console."""
        while self.streaming:
            try:
                # Get log line with timeout
                line = self.stream_queue.get(timeout=0.1)
                print(line)
                self.stream_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Stream error: {e}")
    
    def log_operation_start(self, component: ComponentType, operation: str, operation_id: str, metadata: Dict = None):
        """Log the start of an operation."""
        self.log(component, LogLevel.INFO, f"🚀 Starting {operation}", operation_id, metadata)
    
    def log_operation_success(self, component: ComponentType, operation: str, operation_id: str, duration: float = None):
        """Log successful completion of an operation."""
        duration_str = f" ({duration:.1f}s)" if duration else ""
        self.log(component, LogLevel.SUCCESS, f"✅ Completed {operation}{duration_str}", operation_id)
    
    def log_operation_error(self, component: ComponentType, operation: str, operation_id: str, error: str):
        """Log operation error."""
        self.log(component, LogLevel.ERROR, f"❌ Failed {operation}: {error}", operation_id)
    
    def log_concurrency_wait(self, component: ComponentType, resource: str, operation_id: str):
        """Log concurrency waiting."""
        self.log(component, LogLevel.INFO, f"⏳ Waiting for {resource} resource", operation_id)
    
    def log_concurrency_acquired(self, component: ComponentType, resource: str, operation_id: str):
        """Log resource acquisition."""
        self.log(component, LogLevel.SUCCESS, f"🔒 Acquired {resource} resource", operation_id)
    
    def log_claude_agent_call(self, component: ComponentType, operation_id: str, prompt_preview: str):
        """Log Claude agent invocation."""
        preview = prompt_preview[:100] + "..." if len(prompt_preview) > 100 else prompt_preview
        self.log(component, LogLevel.INFO, f"🤖 Calling Claude agent: {preview}", operation_id)
    
    def log_claude_agent_result(self, component: ComponentType, operation_id: str, success: bool, duration: float):
        """Log Claude agent result."""
        status = "✅ Success" if success else "❌ Failed"
        self.log(component, LogLevel.SUCCESS if success else LogLevel.ERROR, 
                f"🤖 Claude agent {status} ({duration:.1f}s)", operation_id)
    
    def tail_logs(self, lines: int = 50):
        """Show recent log lines."""
        if not self.unified_file.exists():
            print("No logs found")
            return
            
        with open(self.unified_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
        print(f"\n📄 Last {len(recent_lines)} log entries:")
        print("=" * 80)
        for line in recent_lines:
            print(line.strip())

# Global logger instance
_global_logger: Optional[UnifiedLogger] = None

def get_unified_logger() -> UnifiedLogger:
    """Get the global unified logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = UnifiedLogger()
    return _global_logger

def init_unified_logging(base_dir: Path = None, enable_streaming: bool = False):
    """Initialize unified logging system."""
    global _global_logger
    _global_logger = UnifiedLogger(base_dir)
    
    if enable_streaming:
        _global_logger.start_streaming()
    
    # Log system startup
    _global_logger.log(ComponentType.SYSTEM, LogLevel.INFO, "🌟 Claude Buddy unified logging initialized")
    
    return _global_logger

# Convenience functions for each component
def log_post_tool_linter(level: LogLevel, message: str, operation_id: str = None, metadata: Dict = None):
    """Log Post-Tool Linter event."""
    get_unified_logger().log(ComponentType.POST_TOOL_LINTER, level, message, operation_id, metadata)

def log_context7(level: LogLevel, message: str, operation_id: str = None, metadata: Dict = None):
    """Log Context7 event."""
    get_unified_logger().log(ComponentType.CONTEXT7, level, message, operation_id, metadata)

def log_tdd_guard(level: LogLevel, message: str, operation_id: str = None, metadata: Dict = None):
    """Log TDD-Guard event."""
    get_unified_logger().log(ComponentType.TDD_GUARD, level, message, operation_id, metadata)

# Example usage and testing
if __name__ == "__main__":
    # Demo the unified logging system
    logger = init_unified_logging(enable_streaming=True)
    
    # Simulate some operations
    import uuid
    op_id = str(uuid.uuid4())[:8]
    
    logger.log_operation_start(ComponentType.POST_TOOL_LINTER, "code fixing", op_id)
    time.sleep(0.5)
    logger.log_concurrency_wait(ComponentType.POST_TOOL_LINTER, "agent", op_id)
    time.sleep(0.3)
    logger.log_concurrency_acquired(ComponentType.POST_TOOL_LINTER, "agent", op_id)
    logger.log_claude_agent_call(ComponentType.POST_TOOL_LINTER, op_id, "Fix linting issues in test.py")
    time.sleep(1.0)
    logger.log_claude_agent_result(ComponentType.POST_TOOL_LINTER, op_id, True, 2.5)
    logger.log_operation_success(ComponentType.POST_TOOL_LINTER, "code fixing", op_id, 3.3)
    
    # Show recent logs
    time.sleep(0.1)
    logger.tail_logs(10)