#!/usr/bin/env python3
"""Post-Tool Linter Hook with Auto-Fix for Claude Code.

This hook automatically fixes linting and type issues in Python files
after they are modified by Claude Code tools.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

# Add src path for imports
src_path = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, src_path)

from hooks.base import BaseHook, ConcurrencyManager  # noqa: E402
from hooks.unified_logger import get_unified_logger, ComponentType, LogLevel  # noqa: E402
from process_timeouts import TIMEOUTS  # noqa: E402


class _FallbackManager:
    """Fallback concurrency manager that allows unlimited resources."""

    def can_acquire_resource(self: "_FallbackManager", pool_name: str) -> bool:
        """Check if resource can be acquired."""
        del pool_name  # Mark as intentionally unused
        return True

    def acquire_resource(
        self: "_FallbackManager",
        pool_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> "_AcquiredResource":
        """Acquire a resource for concurrency control."""
        del pool_name  # Mark as intentionally unused
        del metadata  # Mark as intentionally unused
        del timeout  # Mark as intentionally unused
        return _AcquiredResource()


class _AcquiredResource:
    """Context manager for acquired resources."""

    def __enter__(self: "_AcquiredResource") -> bool:
        """Enter context."""
        return True

    def __exit__(
        self: "_AcquiredResource",
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        """Exit context."""
        del exc_type, exc_val, exc_tb  # Mark as intentionally unused


# Import concurrency module with fallback
# Define a type variable that can be either implementation
ConcurrencyManagerImpl = Union[ConcurrencyManager, Any]

try:
    from tools.concurrency import get_concurrency_manager  # noqa: F401
except ImportError:
    # Create a wrapper that matches the expected signature
    def get_concurrency_manager(  # type: ignore[misc]
        config_path: Optional[str] = None,
    ) -> ConcurrencyManagerImpl:
        """Get concurrency manager with fallback."""
        del config_path  # Mark as intentionally unused
        return _FallbackManager()


# Try to find claude path
def _find_claude_path() -> str:
    """Find the Claude executable path."""
    claude_paths = [
        os.path.expanduser("~/.local/bin/claude"),
        "/usr/local/bin/claude",
        "claude",  # Try PATH
    ]

    for path in claude_paths:
        if os.path.exists(path) or os.system(f"which {path} > /dev/null 2>&1") == 0:
            return path

    return "claude"  # Default fallback


CLAUDE_PATH: str = _find_claude_path()

DEBUG_LOG = "/tmp/post_tool_linter_debug.log"


def _find_project_root(file_path: str) -> str:
    """Find the project root directory (containing .git or pyproject.toml)."""
    current = os.path.dirname(os.path.abspath(file_path))
    while current != os.path.dirname(current):  # Not at root
        if os.path.exists(os.path.join(current, ".git")):
            return current
        if os.path.exists(os.path.join(current, "pyproject.toml")):
            return current
        current = os.path.dirname(current)
    return os.path.dirname(os.path.abspath(file_path))


def _is_pyright_available() -> bool:
    """Check if pyright is available."""
    # Priority order (matching hook_wrapper.py):
    # 1. .claude/venv
    # 2. Hook's own .venv
    # 3. Project root .venv
    # 4. System pyright

    # Check for .claude/venv by walking up directory tree
    current = Path.cwd()
    while current != current.parent:
        claude_pyright = current / ".claude" / "venv" / "bin" / "pyright"
        if claude_pyright.exists():
            return True
        current = current.parent

    # Check hook's own .venv
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    hook_venv_pyright = os.path.join(hook_dir, ".venv", "bin", "pyright")
    if os.path.exists(hook_venv_pyright):
        return True

    # Check project root .venv
    root_venv_pyright = os.path.join(".venv", "bin", "pyright")
    if os.path.exists(root_venv_pyright):
        return True

    # Check system pyright
    try:
        subprocess.run(
            ["pyright", "--version"],
            capture_output=True,
            check=False,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _find_claude_venv(project_root: str) -> Optional[str]:
    """Find .claude/venv by walking up the directory tree."""
    current = Path(project_root)
    while current != current.parent:
        claude_venv = current / ".claude" / "venv"
        if claude_venv.exists() and (claude_venv / "bin" / "python").exists():
            return str(claude_venv)
        current = current.parent
    return None


def _find_hook_venv() -> Optional[str]:
    """Find hook's own .venv directory."""
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    hook_venv = os.path.join(hook_dir, ".venv")
    if os.path.exists(hook_venv) and os.path.isdir(hook_venv):
        return hook_venv
    return None


def _find_project_root_venv(project_root: str) -> Optional[str]:
    """Find virtual environment in project root directory."""
    venv_names = [".venv", "venv", "env"]
    for venv_name in venv_names:
        venv_path = os.path.join(project_root, venv_name)
        if os.path.exists(venv_path) and os.path.isdir(venv_path):
            return venv_path
    return None


def _find_venv_path(project_root: str) -> Optional[str]:
    """Find virtual environment path if it exists.

    Priority order:
    1. .claude/venv (as per hook_wrapper.py standard)
    2. Hook's own .venv
    3. Project root .venv, venv, or env
    """
    # Check for .claude/venv first
    claude_venv = _find_claude_venv(project_root)
    if claude_venv:
        return claude_venv

    # Check hook's own .venv
    hook_venv = _find_hook_venv()
    if hook_venv:
        return hook_venv

    # Check project root venvs
    return _find_project_root_venv(project_root)


def _load_hook_config() -> Dict[str, Any]:
    """Load hook configuration from config.json."""
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.json"
        )
        with open(config_path, "r", encoding="utf-8") as f:
            return cast(Dict[str, Any], json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default config if file not found or invalid
        return {"settings": {"enabled_linters": ["black", "flake8", "pyright"]}}


def _get_linter_config_paths(file_path: str) -> Tuple[str, str, str]:
    """Get configuration file paths for linters.

    Returns:
        Tuple of (pyproject_path, flake8_config, hook_dir)
    """
    project_root = _find_project_root(file_path)
    hook_dir = os.path.join(project_root, "src", "hooks", "post_tool_linter")
    pyproject_path = os.path.join(hook_dir, "pyproject.toml")
    flake8_config = os.path.join(hook_dir, ".flake8")
    return pyproject_path, flake8_config, hook_dir


def _run_black_linter(file_path: str, pyproject_path: str) -> Tuple[bool, str]:
    """Run black linter and return pass status and issues."""
    black_cmd = ["black", "--check", file_path]
    if os.path.exists(pyproject_path):
        black_cmd.extend(["--config", pyproject_path])

    result = subprocess.run(
        black_cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, f"Black (formatting): {result.stderr.strip()}"
    return True, ""


def _run_isort_linter(file_path: str, pyproject_path: str) -> Tuple[bool, str]:
    """Run isort linter and return pass status and issues."""
    isort_cmd = ["isort", "--check", file_path]
    if os.path.exists(pyproject_path):
        isort_cmd.extend(["--settings-path", pyproject_path])

    result = subprocess.run(
        isort_cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, f"isort (import order): {result.stderr.strip()}"
    return True, ""


def _run_flake8_linter(file_path: str, flake8_config: str) -> Tuple[bool, str]:
    """Run flake8 linter and return pass status and issues."""
    flake8_cmd = ["flake8", file_path]
    if os.path.exists(flake8_config):
        flake8_cmd.extend(["--config", flake8_config])

    result = subprocess.run(
        flake8_cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, f"Flake8 (style):\n{result.stdout.strip()}"
    return True, ""


def _run_mypy_linter(file_path: str, pyproject_path: str) -> Tuple[bool, str]:
    """Run mypy linter and return pass status and issues."""
    mypy_cmd = ["mypy", file_path]
    if os.path.exists(pyproject_path):
        mypy_cmd.extend(["--config-file", pyproject_path])
    else:
        mypy_cmd.append("--strict")

    result = subprocess.run(
        mypy_cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, f"MyPy (type checking):\n{result.stdout.strip()}"
    return True, ""


def _find_pyright_executable(project_root: str, hook_dir: str) -> List[str]:
    """Find pyright executable in priority order.

    Priority order:
    1. .claude/venv
    2. Hook's own .venv
    3. Project root .venv
    4. System pyright
    """
    # Check for .claude/venv by walking up
    current = Path(project_root)
    while current != current.parent:
        claude_pyright = current / ".claude" / "venv" / "bin" / "pyright"
        if claude_pyright.exists() and os.access(str(claude_pyright), os.X_OK):
            return [str(claude_pyright)]
        current = current.parent

    # Check hook's own .venv
    hook_venv_pyright = os.path.join(hook_dir, ".venv", "bin", "pyright")
    if os.path.exists(hook_venv_pyright) and os.access(hook_venv_pyright, os.X_OK):
        return [hook_venv_pyright]

    # Check project root .venv
    root_venv_pyright = os.path.join(project_root, ".venv", "bin", "pyright")
    if os.path.exists(root_venv_pyright) and os.access(root_venv_pyright, os.X_OK):
        return [root_venv_pyright]

    # Fall back to system pyright
    return ["pyright"]


def _build_pyright_command(
    file_path: str, project_root: str, hook_dir: str
) -> List[str]:
    """Build pyright command with all necessary options."""
    pyright_executable = _find_pyright_executable(project_root, hook_dir)
    pyright_cmd = pyright_executable + [file_path]

    # Add config file if it exists
    pyright_config = os.path.join(hook_dir, "pyrightconfig.json")
    if os.path.exists(pyright_config):
        pyright_cmd.extend(["--project", hook_dir])

    # Add venv path if in a virtual environment
    venv_path = _find_venv_path(project_root)
    if venv_path:
        pyright_cmd.extend(["--venv-path", project_root])

    # Add pythonpath for imports
    pyright_cmd.extend(["--pythonpath", project_root])

    return pyright_cmd


def _parse_pyright_errors(output: str) -> List[str]:
    """Parse pyright output and extract error messages."""
    error_lines: List[str] = []
    for line in output.split("\n"):
        # Pyright error format: file:line:col - error: message
        if " - error: " in line:
            error_lines.append(line.strip())
        # Also capture the summary line
        elif "error" in line and "warning" in line and "information" in line:
            error_lines.append(f"Summary: {line.strip()}")
    return error_lines


def _format_pyright_error_message(error_lines: List[str]) -> str:
    """Format pyright error lines into a readable message."""
    error_msg = "Pyright (VS Code):\n" + "\n".join(error_lines[:10])
    if len(error_lines) > 10:
        error_msg += f"\n... and {len(error_lines) - 10} more errors"
    return error_msg


def _run_pyright_linter(
    file_path: str, project_root: str, hook_dir: str
) -> Tuple[bool, str]:
    """Run pyright linter and return pass status and issues."""
    if not _is_pyright_available():
        return True, ""

    pyright_cmd = _build_pyright_command(file_path, project_root, hook_dir)

    try:
        result = subprocess.run(
            pyright_cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, PermissionError) as e:
        # Handle permission errors gracefully
        return True, ""  # Skip pyright if we can't run it

    if result.returncode != 0:
        output = result.stdout + result.stderr
        if "0 errors" not in output:
            error_lines = _parse_pyright_errors(output)
            if error_lines:
                return False, _format_pyright_error_message(error_lines)

    return True, ""


def run_linters(file_path: str) -> Tuple[bool, str]:
    """Run linters on file and return pass status and issues.

    Runs enabled linters based on configuration.
    Default: black, flake8, pyright
    Optional: mypy, isort (can be enabled in config.json)

    Uses configuration files if available:
    - hooks/post_tool_linter/pyproject.toml for black, isort, mypy
    - hooks/post_tool_linter/.flake8 for flake8
    - hooks/post_tool_linter/pyrightconfig.json for pyright
    """
    issues: List[str] = []
    all_pass = True

    # Load config to get enabled linters
    config = _load_hook_config()
    enabled_linters = config.get("settings", {}).get(
        "enabled_linters", ["black", "flake8", "pyright"]
    )

    # Get configuration file paths
    pyproject_path, flake8_config, hook_dir = _get_linter_config_paths(file_path)
    project_root = _find_project_root(file_path)

    # Run each enabled linter
    linter_runners: Dict[str, Callable[[], Tuple[bool, str]]] = {
        "black": lambda: _run_black_linter(file_path, pyproject_path),
        "isort": lambda: _run_isort_linter(file_path, pyproject_path),
        "flake8": lambda: _run_flake8_linter(file_path, flake8_config),
        "mypy": lambda: _run_mypy_linter(file_path, pyproject_path),
        "pyright": lambda: _run_pyright_linter(file_path, project_root, hook_dir),
    }

    for linter_name in enabled_linters:
        if linter_name in linter_runners:
            passed, issue = linter_runners[linter_name]()
            if not passed:
                all_pass = False
                issues.append(issue)

    return all_pass, "\n\n".join(issues)


def calculate_timeout(issues_text: str) -> int:
    """Calculate dynamic timeout based on number of linting issues.

    Args:
        issues_text: Combined text of all linting issues

    Returns:
        Timeout in seconds using centralized timeout system
    """
    # Count approximate number of issues for complexity scaling
    issue_lines = len(issues_text.split("\n"))
    estimated_issues = max(1, issue_lines // 3)
    
    # Use centralized timeout system with complexity factor
    complexity_factor = 1.0 + (estimated_issues * 0.2)  # Scale based on issues
    return TIMEOUTS.for_claude_call(complexity_factor, min_timeout=60, max_timeout=600)


def parse_stdin_data() -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Parse stdin data and extract file path.

    Returns:
        Tuple of (file_path, stdin_data) or (None, None) if no data
    """
    stdin_raw = sys.stdin.read()
    if not stdin_raw:
        return None, None

    try:
        stdin_data = cast(Dict[str, Any], json.loads(stdin_raw))
    except json.JSONDecodeError:
        return None, None

    # Get tool_input with explicit type
    tool_input = stdin_data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return None, None

    # Now tool_input is definitely a dict, cast it to avoid unknown tracking
    typed_tool_input = cast(Dict[str, Any], tool_input)

    # Get file_path with proper type handling
    file_path_raw = typed_tool_input.get("file_path")
    if file_path_raw is None:
        file_path = None
    else:
        file_path = str(file_path_raw)

    return file_path, stdin_data


def should_process_file(file_path: str) -> bool:
    """Check if file should be processed by linter.

    Args:
        file_path: Path to file

    Returns:
        True if file should be processed, False otherwise
    """
    # Check all exclusion criteria
    exclusion_checks = [
        is_claude_directory(file_path),
        not is_python_file(file_path),
        not is_claude_available(),
    ]

    return not any(exclusion_checks)


def is_claude_directory(file_path: str) -> bool:
    """Check if file is in .claude directory.

    Args:
        file_path: Path to file

    Returns:
        True if in .claude directory, False otherwise
    """
    return "/.claude/" in file_path


def is_python_file(file_path: str) -> bool:
    """Check if file is a Python file.

    Args:
        file_path: Path to file

    Returns:
        True if Python file, False otherwise
    """
    return file_path.endswith(".py")


def is_claude_available() -> bool:
    """Check if claude command is available.

    Returns:
        True if claude is available, False otherwise
    """
    return (
        os.path.exists(CLAUDE_PATH)
        or os.system(f"which {CLAUDE_PATH} > /dev/null 2>&1") == 0
    )


def setup_debug_logging() -> bool:
    """Check if debug logging is enabled."""
    # Check if debug is enabled in hook config
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            return config.get("settings", {}).get("debug", False)
        except Exception:
            pass
    return False

def print_response(reasoning: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Print formatted response.

    Args:
        reasoning: The reasoning message
        details: Optional additional details
    """
    response: Dict[str, Any] = {
        "continue": True,
        "reasoning": reasoning,
    }
    if details:
        response["details"] = details
    print(json.dumps(response))
    
    # Log to debug file if enabled
    debug_dir = setup_debug_logging()
    if debug_dir:
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "response": response
        }
        log_file = debug_dir / f"responses_{datetime.date.today().isoformat()}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json.

    Returns:
        Configuration dictionary
    """
    config_file = os.path.join(os.path.dirname(__file__), "config.json")
    config: Dict[str, Any] = {}
    if os.path.exists(config_file):
        with open(config_file, encoding="utf-8") as f:
            data: Any = json.load(f)
            if isinstance(data, dict):
                config = cast(Dict[str, Any], data)
    return config


def _log_autofix_iteration(
    file_path: str, issues: str, iteration: int, dynamic_timeout: int
) -> None:
    """Log autofix iteration details to debug file."""
    with open(DEBUG_LOG, "a", encoding="utf-8") as log:
        log.write(f"\n=== Iteration {iteration + 1} for {file_path} ===\n")
        log.write(f"Issues to fix:\n{issues}\n")
        log.write(f"Dynamic timeout: {dynamic_timeout}s\n")


def _create_autofix_prompt(file_path: str, issues: str) -> str:
    """Create prompt for autofix agent."""
    return f"""Fix ALL linting and type errors in {file_path}

Current issues that MUST be fixed:
{issues}

Instructions:
1. Use Edit or MultiEdit to fix ALL issues listed above
2. If needed to resolve type errors, you may modify other imported files
3. Ensure all linting passes: black, flake8, mypy, and pyright/VS Code
4. DO NOT just say the file looks good - actually fix every issue listed

Common issues to watch for:
- Unknown type propagation: Use explicit type annotations and cast() when needed
- Import order: All imports must be at the top of the file (E402)
- Type incompatibility: Ensure return types and assignments match exactly
- Protocol mismatches: Method signatures must match protocol definitions exactly
- Protected member access: Add public methods or use type: ignore sparingly
- Missing type annotations: Always annotate function parameters and return types
- Dict operations: dict.get() can propagate 'unknown' types - use cast() when needed
- Mypy import-not-found: Add '# type: ignore[import-not-found]' to imports that can't be resolved
- Missing module stubs: For pytest, tools.concurrency, etc. use type ignore comments

The goal is ZERO issues in VS Code/Pylance!"""


def _log_agent_result(result: CompletedProcess[str]) -> None:
    """Log agent execution result."""
    with open(DEBUG_LOG, "a", encoding="utf-8") as log:
        log.write(f"Agent return code: {result.returncode}\n")
        if result.stdout:
            log.write(f"Agent output: {result.stdout[:1000]}\n")
    
    # Also log to debug folder if enabled
    debug_dir = setup_debug_logging()
    if debug_dir:
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": "claude_agent_result",
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "stdout_length": len(result.stdout) if result.stdout else 0
        }
        log_file = debug_dir / f"claude_agents_{datetime.date.today().isoformat()}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


def _execute_autofix_agent(prompt: str, dynamic_timeout: int) -> Tuple[bool, str]:
    """Execute the autofix agent and handle errors."""
    try:
        cmd: List[str] = [
            CLAUDE_PATH,
            "--dangerously-skip-permissions",
            "--output-format", "stream-json",
            "--verbose",
            "-p",
            "-",
        ]

        result: CompletedProcess[str] = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=dynamic_timeout,
            check=False,
        )

        _log_agent_result(result)
        
        # Check if Claude actually succeeded
        if result.returncode != 0:
            error_msg = f"Claude CLI failed with return code {result.returncode}"
            if result.stderr:
                error_msg += f": {result.stderr.strip()}"
            return False, error_msg
            
        # Verify that Claude made actual changes to the file
        if not result.stdout or "no changes needed" in result.stdout.lower():
            return False, "Claude did not make any changes to the file"
            
        return True, f"Claude successfully processed file (output: {len(result.stdout)} chars)"

    except subprocess.TimeoutExpired:
        return False, "⏱️ Auto-fix timed out"

    except (OSError, ValueError) as e:
        with open(DEBUG_LOG, "a", encoding="utf-8") as log:
            log.write(f"Error running agent: {e}\n")
        return False, f"❌ Error during auto-fix: {str(e)}"


def run_autofix_iteration(
    file_path: str,
    issues: str,
    iteration: int,
    max_iterations: int,
    dynamic_timeout: int,
    operation_id: str = "unknown",
) -> Tuple[bool, str]:
    """Run a single autofix iteration.

    Args:
        file_path: Path to file to fix
        issues: Current linting issues
        iteration: Current iteration number
        max_iterations: Maximum number of iterations
        dynamic_timeout: Timeout in seconds

    Returns:
        Tuple of (success, error_message)
    """
    print_response(
        f"🔧 Auto-fixing linting issues in {os.path.basename(file_path)} "
        f"(attempt {iteration + 1}/{max_iterations}, "
        f"timeout: {dynamic_timeout}s, ID: {operation_id})...",
    )

    _log_autofix_iteration(file_path, issues, iteration, dynamic_timeout)
    prompt = _create_autofix_prompt(file_path, issues)
    return _execute_autofix_agent(prompt, dynamic_timeout)


def process_file_with_autofix(
    file_path: str,
    issues: str,
    concurrency_manager: ConcurrencyManagerImpl,
) -> int:
    """Process file with autofix using concurrency manager.

    Args:
        file_path: Path to file to fix
        issues: Current linting issues
        concurrency_manager: Concurrency manager instance

    Returns:
        Exit code (0 for success)
    """
    # Wait for resources to become available (blocking)
    print_response(f"⏳ {os.path.basename(file_path)} - Waiting for agent resource...")
    return _execute_autofix_with_resource(file_path, issues, concurrency_manager)


def _can_acquire_agent_resource(
    file_path: str,
    concurrency_manager: ConcurrencyManagerImpl,
) -> bool:
    """Check if we can acquire an agent resource.

    Args:
        file_path: Path to file being processed
        concurrency_manager: Concurrency manager instance

    Returns:
        True if resource can be acquired, False otherwise
    """
    if not concurrency_manager.can_acquire_resource("agents"):
        print_response(
            f"⏸️ {os.path.basename(file_path)} - "
            "Too many concurrent agents, skipping autofix",
        )
        return False
    return True


def _execute_autofix_with_resource(
    file_path: str,
    issues: str,
    concurrency_manager: ConcurrencyManagerImpl,
) -> int:
    """Execute autofix iterations with acquired resource.

    Args:
        file_path: Path to file to fix
        issues: Current linting issues
        concurrency_manager: Concurrency manager instance

    Returns:
        Exit code (0 for success)
    """
    import uuid
    operation_id = str(uuid.uuid4())[:8]  # Short ID for this operation
    metadata: Dict[str, Any] = {
        "file_path": file_path, 
        "hook": "post_tool_linter",
        "operation_id": operation_id
    }
    print_response(f"🔒 {os.path.basename(file_path)} - Acquiring agent resource (ID: {operation_id})")
    
    # Wait up to 10 minutes for a resource to become available
    with concurrency_manager.acquire_resource("agents", metadata, timeout=600) as acquired:
        if not acquired:
            print_response(
                f"⏸️ {os.path.basename(file_path)} - "
                "Timed out waiting for agent resource (10 min), skipping autofix",
            )
            return 0

        print_response(f"✅ {os.path.basename(file_path)} - Agent resource acquired (ID: {operation_id})")
        return _run_autofix_iterations(file_path, issues, operation_id)


def _run_autofix_iterations(file_path: str, issues: str, operation_id: str = "unknown") -> int:
    """Run autofix iterations until success or max attempts.

    Args:
        file_path: Path to file to fix
        issues: Current linting issues
        operation_id: Unique ID for this operation

    Returns:
        Exit code (0 for success)
    """
    max_iterations = _get_max_iterations_from_config()
    dynamic_timeout = calculate_timeout(issues)

    for iteration in range(max_iterations):
        success, error_msg = run_autofix_iteration(
            file_path,
            issues,
            iteration,
            max_iterations,
            dynamic_timeout,
            operation_id,
        )

        if not success:
            print_response(error_msg)
            break

        # Check if linting passes now
        all_pass, new_issues = run_linters(file_path)
        if all_pass:
            _print_success_message(file_path)
            return 0
        issues = new_issues

    # Failed after max iterations
    _print_failure_message(file_path, max_iterations, issues)
    return 0


def _get_max_iterations_from_config() -> int:
    """Get max iterations from config with fallback."""
    config = load_config()
    settings = config.get("settings", {})

    # Default value
    default_iterations = 3

    if not isinstance(settings, dict):
        return default_iterations

    # Cast settings to avoid unknown tracking
    typed_settings = cast(Dict[str, Any], settings)
    max_iterations_raw = typed_settings.get("max_iterations")

    # Handle different types explicitly
    if max_iterations_raw is None:
        return default_iterations
    elif isinstance(max_iterations_raw, int):
        return max_iterations_raw
    elif isinstance(max_iterations_raw, str):
        try:
            return int(max_iterations_raw)
        except ValueError:
            return default_iterations
    else:
        return default_iterations


def _print_success_message(file_path: str) -> None:
    """Print success message for fixed file."""
    print_response(
        f"✅ {os.path.basename(file_path)} - All linting issues fixed successfully!",
    )


def _print_failure_message(file_path: str, max_iterations: int, issues: str) -> None:
    """Print failure message when max iterations reached."""
    print_response(
        f"⚠️ {os.path.basename(file_path)} - "
        f"Some issues remain after {max_iterations} attempts",
        {
            "remaining_issues": issues.split("\n")[:10],
            "note": "Manual intervention may be required",
        },
    )


class PostToolLinterHook(BaseHook):
    """Post-Tool Linter Hook implementation."""

    def __init__(
        self,
        config: Dict[str, Any],
        concurrency_manager: Optional[ConcurrencyManager] = None,
    ) -> None:
        """Initialize hook with configuration and concurrency manager."""
        super().__init__(config, concurrency_manager)
        # If no concurrency manager provided, try to get the global one
        if self.concurrency_manager is None:
            try:
                self.concurrency_manager = get_concurrency_manager()
            except Exception:
                # Fall back to no concurrency control
                self.concurrency_manager = _FallbackManager()

    def process_event(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Process a Claude Code event."""
        # Only process PostToolUse events
        if event_data.get("event_type") != "PostToolUse":
            return True, ""

        # Only process file editing tools
        tool_name = event_data.get("tool_name", "")
        if tool_name not in ["Edit", "Write", "MultiEdit", "NotebookEdit"]:
            return True, ""

        # Get file path
        tool_input = event_data.get("tool_input", {})
        file_path = tool_input.get("file_path")
        if not file_path:
            return True, ""

        # Check if we should process this file
        if not should_process_file(file_path):
            return True, ""

        # Run linters
        all_pass, issues = run_linters(file_path)

        if all_pass:
            return True, f"✅ {os.path.basename(file_path)} - No linting issues found"

        # Only run autofix if enabled
        if self.config.get("settings", {}).get("auto_fix", True):
            # Use concurrency manager if available
            if isinstance(
                self.concurrency_manager, (ConcurrencyManager, _FallbackManager)
            ):
                exit_code = process_file_with_autofix(file_path, issues, self.concurrency_manager)
                
                # Check if autofix was successful
                if exit_code == 0:
                    # Verify linting actually passes now
                    all_pass_now, remaining_issues = run_linters(file_path)
                    if all_pass_now:
                        return (
                            True,
                            f"✅ {os.path.basename(file_path)} - All linting issues fixed successfully!",
                        )
                    else:
                        return (
                            True,
                            f"⚠️ {os.path.basename(file_path)} - Claude autofix completed but some issues remain:\n{remaining_issues}",
                        )
                else:
                    return (
                        True,
                        f"❌ {os.path.basename(file_path)} - Claude autofix failed, issues remain:\n{issues}",
                    )
            else:
                return (
                    True,
                    f"⚠️ {os.path.basename(file_path)} has linting issues but auto-fix disabled",
                )

        return (
            True,
            f"⚠️ {os.path.basename(file_path)} has linting issues:\n{issues[:500]}",
        )

    def is_applicable(self, event_data: Dict[str, Any]) -> bool:
        """Check if this hook should process the event."""
        if not super().is_applicable(event_data):
            return False

        # Check event type
        if event_data.get("event_type") != "PostToolUse":
            return False

        # Check tool name
        tool_name = event_data.get("tool_name", "")
        return tool_name in ["Edit", "Write", "MultiEdit", "NotebookEdit"]

    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema."""
        schema = super().get_config_schema()
        schema["properties"].update(
            {
                "settings": {
                    "type": "object",
                    "properties": {
                        "enabled_linters": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["black", "flake8", "mypy", "pyright", "isort"],
                            },
                            "default": ["black", "flake8", "pyright"],
                            "description": "Linters to run",
                        },
                        "auto_fix": {
                            "type": "boolean",
                            "default": True,
                            "description": "Automatically fix linting issues",
                        },
                        "max_iterations": {
                            "type": "integer",
                            "default": 3,
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Maximum autofix attempts",
                        },
                    },
                }
            }
        )
        return schema


# Factory function for hook loader
def create_hook(
    config: Dict[str, Any], concurrency_manager: Optional[ConcurrencyManager] = None
) -> PostToolLinterHook:
    """Create PostToolLinterHook instance."""
    return PostToolLinterHook(config, concurrency_manager)


def main() -> int:
    """Run the post-tool linter hook.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        return _process_hook_request()
    except (json.JSONDecodeError, OSError) as e:
        print_response(f"❌ Linting hook error: {str(e)}")
        return 0


def _process_hook_request() -> int:
    """Process the hook request and handle file linting.

    Returns:
        Exit code (0 for success)
    """
    # Parse stdin data
    file_path, stdin_data = parse_stdin_data()
    if not file_path or not stdin_data:
        return 0

    # Create hook instance
    config = load_config()
    hook = PostToolLinterHook(config)

    # Process event
    should_continue, message = hook.process_event(stdin_data)

    # Print response
    response = {
        "continue": should_continue,
        "reasoning": message if message else "Processed",
    }
    print(json.dumps(response))

    return 0


if __name__ == "__main__":
    sys.exit(main())
