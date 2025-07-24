#!/usr/bin/env python3
"""Centralized timeout management for external processes.

This module provides a single source of truth for all subprocess timeouts,
ensuring consistent timeout behavior across all Claude Buddy components.
"""

import os
from typing import Optional


class ProcessTimeouts:
    """Centralized timeout management for external processes."""
    
    def __init__(self):
        """Initialize timeout values from environment variables with sensible defaults."""
        # Core external tool timeouts
        self.tdd_guard = int(os.environ.get('TDD_GUARD_TIMEOUT_SECONDS', '300'))
        self.external_check = int(os.environ.get('EXTERNAL_TOOL_CHECK_TIMEOUT_SECONDS', '30'))
        self.mcp_call = int(os.environ.get('MCP_CALL_TIMEOUT_SECONDS', '20'))
        self.claude_agent = int(os.environ.get('CLAUDE_AGENT_TIMEOUT_SECONDS', '300'))
        
        # Additional process timeouts
        self.npm_install = int(os.environ.get('NPM_INSTALL_TIMEOUT_SECONDS', '300'))
        self.linter_process = int(os.environ.get('LINTER_PROCESS_TIMEOUT_SECONDS', '60'))
    
    def for_claude_call(self, complexity_factor: float = 1.0, min_timeout: int = 60, max_timeout: int = 600) -> int:
        """Get timeout for Claude CLI calls with complexity scaling.
        
        Args:
            complexity_factor: Multiplier based on complexity (e.g., number of issues)
            min_timeout: Minimum timeout in seconds
            max_timeout: Maximum timeout in seconds
            
        Returns:
            Timeout in seconds, scaled by complexity but within bounds
        """
        base = self.claude_agent
        scaled = int(base * complexity_factor)
        return max(min_timeout, min(scaled, max_timeout))
    
    def for_mcp_server(self) -> int:
        """Get timeout for MCP server calls (Context7, etc.)."""
        return self.mcp_call
    
    def for_external_tool_check(self) -> int:
        """Get timeout for checking if external tools exist."""
        return self.external_check
    
    def for_tdd_guard_validation(self) -> int:
        """Get timeout for TDD-Guard validation calls."""
        return self.tdd_guard
    
    def for_npm_operations(self) -> int:
        """Get timeout for npm install/list operations."""
        return self.npm_install
    
    def for_linter_execution(self) -> int:
        """Get timeout for linter tool execution (black, flake8, etc.)."""
        return self.linter_process
    
    def get_all_timeouts(self) -> dict:
        """Get all configured timeouts for debugging/logging."""
        return {
            'tdd_guard': self.tdd_guard,
            'external_check': self.external_check,
            'mcp_call': self.mcp_call,
            'claude_agent': self.claude_agent,
            'npm_install': self.npm_install,
            'linter_process': self.linter_process,
        }


# Global instance - import this in other modules
TIMEOUTS = ProcessTimeouts()


def get_timeouts() -> ProcessTimeouts:
    """Get the global timeout manager instance."""
    return TIMEOUTS


if __name__ == "__main__":
    # Demo the timeout system
    timeouts = get_timeouts()
    print("🕐 Claude Buddy Process Timeouts:")
    print("=" * 40)
    
    for name, value in timeouts.get_all_timeouts().items():
        print(f"  {name:<20}: {value:>3}s")
    
    print("\n🔧 Dynamic Examples:")
    print(f"  Simple Claude call  : {timeouts.for_claude_call(1.0)}s")
    print(f"  Complex Claude call : {timeouts.for_claude_call(2.5)}s")
    print(f"  MCP server call     : {timeouts.for_mcp_server()}s")
    print(f"  Tool availability   : {timeouts.for_external_tool_check()}s")