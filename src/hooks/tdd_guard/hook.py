#!/usr/bin/env python3
"""TDD-Guard hook that validates TDD practices before code changes."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from ..base import BaseHook, ConcurrencyManager
    from ..logger import get_logger
    from ..external_loader import get_external_loader
    from process_timeouts import TIMEOUTS
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from hooks.base import BaseHook, ConcurrencyManager
    from hooks.logger import get_logger
    from hooks.external_loader import get_external_loader
    from process_timeouts import TIMEOUTS

logger = get_logger(__name__)


class TDDGuardHook(BaseHook):
    """Hook that enforces TDD practices using TDD-Guard."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        concurrency_manager: Optional[ConcurrencyManager] = None,
    ) -> None:
        """Initialize TDD-Guard hook."""
        super().__init__(config, concurrency_manager)
        
        # TDD-Guard configuration
        self.strict_mode = config.get("strict_mode", False)
        self.model = config.get("model", "claude")
        self.test_runner = config.get("test_runner", "pytest")
        self.timeout = config.get("timeout", TIMEOUTS.for_tdd_guard_validation())
        
        # Resource pool for concurrency management
        self.resource_pool = config.get("resource_pool", "testing")
        
        # External tool management
        self.external_loader = get_external_loader()
        
    def process_event(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Process event by validating TDD compliance."""
        if not self.enabled:
            return True, ""
            
        # Only process PreToolUse events for code operations
        if not self.is_applicable(event_data):
            return True, ""
            
        # Use concurrency management if available
        if self.concurrency_manager:
            with self.concurrency_manager.acquire_resource(
                self.resource_pool,
                {"operation": "tdd_validation", "tool": event_data.get("tool_name")},
                timeout=30
            ) as acquired:
                if not acquired:
                    logger.warning("Could not acquire validation resource - allowing operation")
                    return True, "⚠️ TDD validation skipped (resource limit)"
                    
                return self._validate_tdd_compliance(event_data)
        else:
            return self._validate_tdd_compliance(event_data)
            
    def _validate_tdd_compliance(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate TDD compliance using TDD-Guard via external_loader."""
        tdd_timeout = min(self.timeout, 60)  # Define timeout at method level
        
        try:
            # Check if TDD-Guard is available
            if not self.external_loader.is_tool_available("tdd_guard"):
                logger.debug("TDD-Guard not available - skipping validation")
                return True, "⚠️ TDD-Guard not available - skipping validation"
                
            # Prepare request for TDD-Guard
            request = self._prepare_tdd_request(event_data)
            
            # Get tool info and build command
            tool_info = self.external_loader.get_tool_info("tdd_guard")
            command = self._build_tdd_command(tool_info)
            
            # Call TDD-Guard CLI with proper timeout
            # Use a shorter timeout for TDD-Guard itself (it has its own Claude timeout)
            tdd_timeout = min(self.timeout, 60)  # Max 60 seconds for TDD-Guard
            
            result = subprocess.run(
                command,
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=tdd_timeout,
                env=self._get_environment()
            )
            
            if result.returncode != 0:
                logger.error(f"TDD-Guard error: {result.stderr}")
                return True, "⚠️ TDD validation error - allowing operation"
                
            # Parse TDD-Guard response
            return self._parse_tdd_response(result.stdout)
            
        except subprocess.TimeoutExpired:
            logger.warning(f"TDD-Guard validation timed out after {tdd_timeout}s")
            # For timeouts, we should be more conservative - block by default in strict mode
            if self.strict_mode:
                return False, "🛑 TDD validation timed out - blocking operation (strict mode). Try again in a moment."
            else:
                return True, "⚠️ TDD validation timed out - allowing operation"
        except Exception as e:
            logger.error(f"TDD validation error: {e}")
            return True, "⚠️ TDD validation failed - allowing operation"
            
    def _build_tdd_command(self, tool_info: Dict[str, Any]) -> list:
        """Build TDD-Guard command based on tool info."""
        tool_type = tool_info.get("type", "global_cli")
        
        if tool_type == "local_npm":
            # Use node to run the actual CLI script
            tool_path = tool_info.get("path")
            # Convert .bin/tdd-guard to actual JS file
            js_path = tool_path.parent.parent / "tdd-guard" / "dist" / "cli" / "tdd-guard.js"
            if js_path.exists():
                return ["node", str(js_path)]
            else:
                return [str(tool_path)]
        elif tool_type == "submodule_cli":
            # Use submodule path
            tool_path = tool_info.get("path")
            return ["node", str(tool_path)]
        elif tool_type == "global_cli":
            # Use global command
            return ["tdd-guard"]
        else:
            # Fallback to global
            return ["tdd-guard"]
            
    def _prepare_tdd_request(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request for TDD-Guard validation."""
        # Generate session_id if not provided
        import uuid
        session_id = event_data.get("session_id", str(uuid.uuid4()))
        
        # Generate transcript_path if not provided
        transcript_path = event_data.get("transcript_path", f"/tmp/claude_buddy_transcript_{session_id}.json")
        
        return {
            # Required fields for TDD-Guard
            "session_id": session_id,
            "transcript_path": transcript_path,
            "hook_event_name": event_data.get("event_type", "PreToolUse"),
            
            # Standard fields
            "event_type": event_data.get("event_type"),
            "tool_name": event_data.get("tool_name"),
            "tool_input": event_data.get("tool_input", {}),
            
            # Additional metadata
            "metadata": {
                "timestamp": event_data.get("metadata", {}).get("timestamp"),
                "strict_mode": self.strict_mode,
                "model": self.model,
                "test_runner": self.test_runner
            }
        }
        
    def _parse_tdd_response(self, response: str) -> Tuple[bool, str]:
        """Parse TDD-Guard response."""
        try:
            if not response.strip():
                return True, ""
                
            data = json.loads(response)
            
            # Check decision
            decision = data.get("decision", "approve")
            should_continue = decision == "approve"
            
            # Build message
            message_parts = []
            
            if not should_continue:
                stop_reason = data.get("stopReason", "TDD validation failed")
                message_parts.append(f"🛑 {stop_reason}")
                
            reason = data.get("reason", "")
            if reason:
                message_parts.append(reason)
                
            # Add validation details
            if "validationResults" in data:
                validation = data["validationResults"]
                if "tddPhase" in validation:
                    message_parts.append(f"🔄 TDD Phase: {validation['tddPhase']}")
                if "testCoverage" in validation:
                    message_parts.append(f"📊 Coverage: {validation['testCoverage']}%")
                    
            # Add suggestions if rejected
            if not should_continue and "suggestions" in data:
                message_parts.append("💡 Suggestions:")
                for suggestion in data["suggestions"][:3]:
                    message_parts.append(f"  • {suggestion}")
                    
            return should_continue, "\n".join(message_parts)
            
        except json.JSONDecodeError:
            logger.error(f"Invalid TDD-Guard response: {response}")
            return True, ""
        except Exception as e:
            logger.error(f"Error parsing TDD response: {e}")
            return True, ""
            
    def _get_environment(self) -> Dict[str, str]:
        """Get environment variables for TDD-Guard."""
        import os
        env = os.environ.copy()
        
        if self.strict_mode:
            env["TDD_GUARD_STRICT"] = "true"
        if self.model:
            env["TDD_GUARD_MODEL"] = self.model
        if self.test_runner:
            env["TDD_GUARD_TEST_RUNNER"] = self.test_runner
            
        # Set Claude CLI timeout to be slightly less than our timeout
        # This ensures TDD-Guard gets the timeout error, not us
        claude_timeout = max(30, min(self.timeout - 5, 55))
        env["CLAUDE_TIMEOUT"] = str(claude_timeout)
            
        return env
        
    def is_applicable(self, event_data: Dict[str, Any]) -> bool:
        """Check if this hook should process the event."""
        # Only process PreToolUse events
        if event_data.get("event_type") != "PreToolUse":
            return False
            
        # Only for code modification operations
        tool_name = event_data.get("tool_name", "")
        return tool_name in ["Write", "Edit", "MultiEdit", "TodoWrite"]
        
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema."""
        schema = super().get_config_schema()
        schema["properties"].update({
            "strict_mode": {
                "type": "boolean",
                "description": "Enforce strict TDD practices",
                "default": False
            },
            "model": {
                "type": "string",
                "description": "AI model for validation",
                "enum": ["claude", "anthropic-api"],
                "default": "claude"
            },
            "test_runner": {
                "type": "string",
                "description": "Test runner to use",
                "enum": ["pytest", "unittest", "vitest", "jest"],
                "default": "pytest"
            },
            "timeout": {
                "type": "integer",
                "description": "Validation timeout in seconds",
                "default": 30,
                "minimum": 5,
                "maximum": 120
            },
            "resource_pool": {
                "type": "string",
                "description": "Concurrency pool name",
                "default": "validation"
            }
        })
        return schema


# Factory function for registry
def create_hook(
    config: Dict[str, Any],
    concurrency_manager: Optional[ConcurrencyManager] = None,
) -> TDDGuardHook:
    """Create TDD-Guard hook instance."""
    return TDDGuardHook(config, concurrency_manager)