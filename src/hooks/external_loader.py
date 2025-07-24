#!/usr/bin/env python3
"""External tool loader and availability manager."""

import json
import os
import subprocess
import threading
from pathlib import Path
from typing import Dict, Optional, Any

from .logger import get_logger
from process_timeouts import TIMEOUTS

logger = get_logger(__name__)


class ExternalToolLoader:
    """Manages external tool availability and initialization."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize external tool loader.
        
        Args:
            project_root: Path to project root (auto-detected if None)
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.tools_status: Dict[str, Dict[str, Any]] = {}
        self._check_tool_availability()
        
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if external tool is available and ready.
        
        Args:
            tool_name: Name of the tool (tdd_guard, context7)
            
        Returns:
            True if tool is available
        """
        return self.tools_status.get(tool_name, {}).get("available", False)
        
    def get_tool_path(self, tool_name: str) -> Optional[Path]:
        """Get path to external tool executable.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Path to tool executable or None
        """
        return self.tools_status.get(tool_name, {}).get("path")
        
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get complete tool information.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool information dictionary
        """
        return self.tools_status.get(tool_name, {})
        
    def _check_tool_availability(self):
        """Check which external tools are available."""
        # Check TDD-Guard submodule
        self._check_tdd_guard()
        
        # Check Context7 MCP server
        self._check_context7_mcp()
        
        # Check global CLI tools
        self._check_global_tools()
        
    def _check_tdd_guard(self):
        """Check TDD-Guard availability."""
        # Check local node_modules installation first (in src directory)
        src_local_path = self.project_root / "src" / "node_modules" / ".bin" / "tdd-guard"
        
        if src_local_path.exists():
            # Verify it's executable
            try:
                result = subprocess.run(
                    [str(src_local_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUTS.for_external_tool_check()
                )
                if result.returncode == 0:
                    self.tools_status["tdd_guard"] = {
                        "available": True,
                        "path": src_local_path,
                        "type": "local_npm",
                        "version": result.stdout.strip(),
                        "source": "local"
                    }
                    logger.info(f"TDD-Guard local npm installation available: {result.stdout.strip()}")
                    return
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, PermissionError):
                pass
        
        # Check src/node_modules first (where npm install happens)
        src_path = self.project_root / "src" / "node_modules" / ".bin" / "tdd-guard"
        if src_path.exists():
            local_path = src_path
        else:
            # Check root node_modules as fallback
            local_path = self.project_root / "node_modules" / ".bin" / "tdd-guard"
        
        if local_path.exists():
            # Verify it's executable by testing with empty input
            try:
                result = subprocess.run(
                    [str(local_path)],
                    input="{}",
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUTS.for_external_tool_check()
                )
                # TDD-Guard should return JSON response even for empty input
                if result.returncode == 0 or (result.stdout and "{" in result.stdout):
                    self.tools_status["tdd_guard"] = {
                        "available": True,
                        "path": local_path,
                        "type": "local_npm",
                        "version": "0.5.3",  # Known version from package.json
                        "source": "local"
                    }
                    logger.info(f"TDD-Guard local npm installation available: {local_path}")
                    return
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, PermissionError):
                pass
        
        # Check submodule path second
        submodule_path = self.project_root / "external" / "tdd-guard" / "dist" / "cli" / "tdd-guard.js"
        
        if submodule_path.exists():
            # Verify it's executable
            try:
                result = subprocess.run(
                    ["node", str(submodule_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUTS.for_external_tool_check()
                )
                if result.returncode == 0:
                    self.tools_status["tdd_guard"] = {
                        "available": True,
                        "path": submodule_path,
                        "type": "submodule_cli",
                        "version": result.stdout.strip(),
                        "source": "submodule"
                    }
                    logger.info(f"TDD-Guard submodule available: {result.stdout.strip()}")
                    return
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, PermissionError):
                pass
                
        # Fallback to global installation
        try:
            result = subprocess.run(
                ["tdd-guard", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.tools_status["tdd_guard"] = {
                    "available": True,
                    "path": None,  # Global command
                    "type": "global_cli",
                    "version": result.stdout.strip(),
                    "source": "global"
                }
                logger.info(f"TDD-Guard global installation available: {result.stdout.strip()}")
                return
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, PermissionError, MemoryError):
            pass
            
        # Not available
        self.tools_status["tdd_guard"] = {
            "available": False,
            "reason": "TDD-Guard not found as submodule or global installation"
        }
        logger.warning("TDD-Guard not available")
        
    def _check_context7_mcp(self):
        """Check Context7 MCP server availability."""
        # Check if npx can run it
        try:
            result = subprocess.run(
                ["npx", "--yes", "@upstash/context7-mcp", "--help"],
                capture_output=True,
                text=True,
                timeout=TIMEOUTS.for_external_tool_check()
            )
            if result.returncode == 0:
                self.tools_status["context7"] = {
                    "available": True,
                    "path": None,
                    "type": "mcp_server",
                    "source": "npx",
                    "mcp_config": {
                        "transport": "stdio",
                        "command": "npx",
                        "args": ["--yes", "@upstash/context7-mcp"]
                    }
                }
                logger.info("Context7 MCP server available via npx")
                return
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, PermissionError, MemoryError):
            pass
        
        # Check submodule path
        submodule_path = self.project_root / "external" / "context7-mcp" / "dist" / "index.js"
        
        if submodule_path.exists():
            self.tools_status["context7"] = {
                "available": True,
                "path": submodule_path,
                "type": "mcp_server",
                "source": "submodule",
                "mcp_config": {
                    "command": "node",
                    "args": [str(submodule_path)],
                    "cwd": str(self.project_root)
                }
            }
            logger.info("Context7 MCP server submodule available")
            return
            
        # Check global installation
        try:
            result = subprocess.run(
                ["npx", "@upstash/context7-mcp", "--version"],
                capture_output=True,
                text=True,
                timeout=TIMEOUTS.for_external_tool_check()
            )
            if result.returncode == 0:
                self.tools_status["context7"] = {
                    "available": True,
                    "path": None,
                    "type": "mcp_server",
                    "source": "global",
                    "mcp_config": {
                        "command": "npx",
                        "args": ["@upstash/context7-mcp"]
                    }
                }
                logger.info("Context7 MCP server global installation available")
                return
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, PermissionError, MemoryError):
            pass
            
        # Not available
        self.tools_status["context7"] = {
            "available": False,
            "reason": "Context7 MCP server not configured. Run: claude mcp add --transport http context7 https://mcp.context7.com/mcp"
        }
        logger.warning("Context7 MCP server not available")
        
    def _check_global_tools(self):
        """Check other global CLI tools."""
        # This can be extended for other tools like black, ruff, etc.
        pass
        
    def get_status_report(self) -> str:
        """Get human-readable status report of all tools.
        
        Returns:
            Formatted status report
        """
        lines = ["External Tools Status:"]
        
        for tool_name, status in self.tools_status.items():
            if status and status.get("available"):
                source = status.get("source", "unknown")
                version = status.get("version", "")
                version_str = f" ({version})" if version else ""
                lines.append(f"  ✅ {tool_name}: Available from {source}{version_str}")
            else:
                reason = status.get("reason", "Unknown reason") if status else "Malformed status"
                lines.append(f"  ❌ {tool_name}: {reason}")
                
        return "\n".join(lines)
        
    def setup_submodules_if_missing(self) -> Dict[str, bool]:
        """Attempt to set up missing submodules.
        
        Returns:
            Dictionary of tool_name -> success status
        """
        results = {}
        
        # This would contain logic to add submodules if they're missing
        # For now, just return current status
        for tool_name, status in self.tools_status.items():
            results[tool_name] = status.get("available", False)
            
        return results


# Global instance and lock for thread safety
_external_loader = None
_loader_lock = threading.Lock()

def get_external_loader() -> ExternalToolLoader:
    """Get global external tool loader instance (thread-safe singleton)."""
    global _external_loader
    if _external_loader is None:
        with _loader_lock:
            # Double-check locking pattern
            if _external_loader is None:
                _external_loader = ExternalToolLoader()
    return _external_loader