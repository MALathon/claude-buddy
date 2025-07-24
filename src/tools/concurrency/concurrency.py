#!/usr/bin/env python3
"""Global Concurrency Manager for Claude Code Hooks.

This module provides centralized resource management for all hooks,
preventing resource exhaustion and coordinating concurrent operations.

This version uses individual lock files per resource acquisition for
better reliability and race condition prevention.
"""
import fcntl
import json
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional, cast


class GlobalConcurrencyManager:
    """Manages concurrency across all Claude Code hooks."""

    def __init__(
        self: "GlobalConcurrencyManager", config_path: Optional[str] = None
    ) -> None:
        """Initialize the concurrency manager.

        Args:
            config_path: Path to configuration file
        """
        self._config_path = config_path
        # Initialize attributes with defaults
        self._resource_pools: Dict[str, Any] = {}
        self._settings: Dict[str, Any] = {}
        self.lock_dir: Path = Path("/tmp/claude_concurrency")
        self._stale_timeout: int = 300
        self._debug: bool = False

        self._load_config()

        # Ensure lock directory exists
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self: "GlobalConcurrencyManager") -> None:
        """Load configuration from file or use defaults."""
        config_file = self._get_config_file_path()
        config = self._read_config_file(config_file)
        if config is None:
            config = self._get_default_config()
        self._apply_config(config)

    def _get_config_file_path(self: "GlobalConcurrencyManager") -> Path:
        """Get the path to the configuration file."""
        if self._config_path and Path(self._config_path).exists():
            return Path(self._config_path)
        return Path(__file__).parent / "config.json"

    def _read_config_file(
        self: "GlobalConcurrencyManager", config_file: Path
    ) -> Optional[Dict[str, Any]]:
        """Read configuration from file."""
        if not config_file.exists():
            return None

        result: Optional[Dict[str, Any]] = None
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data: Any = json.load(f)
                if isinstance(data, dict):
                    result = cast(Dict[str, Any], data)
        except (json.JSONDecodeError, OSError):
            pass

        return result

    def _get_default_config(self: "GlobalConcurrencyManager") -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "resource_pools": {
                "agents": {
                    "max": 3,
                    "timeout": 300,
                    "description": "Headless Claude agents",
                },
                "linting": {
                    "max": 2,
                    "timeout": 120,
                    "description": "Linting operations",
                },
                "testing": {
                    "max": 1,
                    "timeout": 600,
                    "description": "Test execution",
                },
            },
            "settings": {
                "lock_dir": "/tmp/claude_hooks",
                "stale_lock_timeout": 300,
                "debug": False,
            },
        }

    def _apply_config(self: "GlobalConcurrencyManager", config: Dict[str, Any]) -> None:
        """Apply configuration to instance attributes."""
        self._resource_pools = config.get("resource_pools", {})
        self._settings = config.get("settings", {})
        lock_dir = self._settings.get("lock_dir", "/tmp/claude_hooks")
        
        # If lock_dir is relative, make it relative to the concurrency module directory
        if not os.path.isabs(lock_dir):
            self.lock_dir = Path(__file__).parent / lock_dir
        else:
            self.lock_dir = Path(lock_dir)
        self._stale_timeout = self._settings.get("stale_lock_timeout", 300)
        self._debug = self._settings.get("debug", False)

    def _debug_log(self: "GlobalConcurrencyManager", message: str) -> None:
        """Log debug messages if debug is enabled."""
        if self._debug:
            try:
                # Ensure lock directory exists
                self.lock_dir.mkdir(parents=True, exist_ok=True)
                debug_file = self.lock_dir / "debug.log"
                with open(debug_file, "a", encoding="utf-8") as f:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {message}\n")
            except OSError:
                # Silently ignore debug logging errors
                pass

    def _is_lock_stale(self: "GlobalConcurrencyManager", lock_file: Path) -> bool:
        """Check if a lock file is stale based on timestamp and PID."""
        lock_data = self._read_lock_data(lock_file)
        if lock_data is None:
            return True

        return self._check_lock_staleness(lock_data)

    def _read_lock_data(
        self: "GlobalConcurrencyManager", lock_file: Path
    ) -> Optional[Dict[str, Any]]:
        """Read lock data from file.

        Args:
            lock_file: Path to lock file

        Returns:
            Lock data dictionary or None if unreadable
        """
        result: Optional[Dict[str, Any]] = None
        if lock_file.exists():
            try:
                with open(lock_file, "r", encoding="utf-8") as f:
                    data: Any = json.load(f)
                    if isinstance(data, dict):
                        result = cast(Dict[str, Any], data)
            except (OSError, json.JSONDecodeError):
                # If we can't read the lock file, consider it stale
                pass
        return result

    def _check_lock_staleness(
        self: "GlobalConcurrencyManager", lock_data: Dict[str, Any]
    ) -> bool:
        """Check if lock data indicates a stale lock.

        Args:
            lock_data: Lock data dictionary

        Returns:
            True if lock is stale, False otherwise
        """
        # Check timestamp
        timestamp = lock_data.get("timestamp", 0)
        if time.time() - timestamp > self._stale_timeout:
            return True

        # Check if process is still alive
        if pid := lock_data.get("pid"):
            return self._is_process_dead(pid)

        return False

    def _is_process_dead(self: "GlobalConcurrencyManager", pid: int) -> bool:
        """Check if a process is dead.

        Args:
            pid: Process ID to check

        Returns:
            True if process is dead, False if alive
        """
        try:
            # Send signal 0 to check if process exists
            os.kill(pid, 0)
            return False
        except ProcessLookupError:
            # Process doesn't exist
            return True

    def _cleanup_stale_locks(self: "GlobalConcurrencyManager", pool_name: str) -> None:
        """Remove stale lock files for a resource pool."""
        # Ensure pool subdirectory exists
        pool_dir = self.lock_dir / pool_name
        pool_dir.mkdir(parents=True, exist_ok=True)
        
        pattern = "*.json"
        for lock_file in pool_dir.glob(pattern):
            if self._is_lock_stale(lock_file):
                self._remove_stale_lock(lock_file)

    def _remove_stale_lock(self: "GlobalConcurrencyManager", lock_file: Path) -> None:
        """Remove a single stale lock file."""
        try:
            lock_file.unlink()
            self._debug_log(f"Removed stale lock: {lock_file}")
        except OSError as e:
            msg = f"Failed to remove stale lock {lock_file}: {e}"
            self._debug_log(msg)

    def _count_active_locks(self: "GlobalConcurrencyManager", pool_name: str) -> int:
        """Count non-stale locks for a resource pool."""
        self._cleanup_stale_locks(pool_name)
        pool_dir = self.lock_dir / pool_name
        if not pool_dir.exists():
            return 0
        return len(list(pool_dir.glob("*.json")))

    def _try_acquire_lock_atomically(
        self: "GlobalConcurrencyManager",
        pool_name: str,
        max_resources: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        """Atomically check resource limit and create lock file if under limit.

        Returns:
            Path to lock file if successful, None otherwise
        """
        if not self._ensure_lock_directory():
            return None

        global_lock_file = self.lock_dir / f".{pool_name}_global.lock"
        return self._acquire_with_global_lock(
            pool_name,
            max_resources,
            metadata,
            global_lock_file,
        )

    def _ensure_lock_directory(self: "GlobalConcurrencyManager") -> bool:
        """Ensure lock directory exists.

        Returns:
            True if directory exists or was created, False on error
        """
        try:
            self.lock_dir.mkdir(parents=True, exist_ok=True)
            return True
        except OSError:
            self._debug_log(f"Failed to create lock directory: {self.lock_dir}")
            return False

    def _acquire_with_global_lock(
        self: "GlobalConcurrencyManager",
        pool_name: str,
        max_resources: int,
        metadata: Optional[Dict[str, Any]],
        global_lock_file: Path,
    ) -> Optional[Path]:
        """Acquire lock using global lock file for coordination.

        Args:
            pool_name: Name of resource pool
            max_resources: Maximum number of resources
            metadata: Optional metadata for lock
            global_lock_file: Path to global lock file

        Returns:
            Path to created lock file or None
        """
        try:
            # Use a persistent lock file with flock for coordination
            with open(global_lock_file, "w", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                # Critical section: check count and create lock atomically
                lock_file = self._create_resource_lock_atomic(
                    pool_name,
                    max_resources,
                    metadata,
                )
                return lock_file

        except OSError as e:
            self._handle_global_lock_error(e, pool_name, global_lock_file)
            return None

    def _create_resource_lock_atomic(
        self: "GlobalConcurrencyManager",
        pool_name: str,
        max_resources: int,
        metadata: Optional[Dict[str, Any]],
    ) -> Optional[Path]:
        """Create resource lock if under limit (atomic operation under global lock).

        Args:
            pool_name: Name of resource pool
            max_resources: Maximum number of resources
            metadata: Optional metadata for lock

        Returns:
            Path to created lock file or None if at capacity
        """
        # Clean up stale locks and check count
        self._cleanup_stale_locks(pool_name)
        pool_dir = self.lock_dir / pool_name
        pool_dir.mkdir(parents=True, exist_ok=True)
        
        current_count = len(list(pool_dir.glob("*.json")))
        if current_count >= max_resources:
            self._debug_log(
                f"Pool {pool_name} at capacity " f"({current_count}/{max_resources})",
            )
            return None

        # Generate unique lock filename and create it
        lock_id = uuid.uuid4().hex[:8]
        lock_file = pool_dir / f"{lock_id}.json"

        # Prepare lock data
        lock_data = {
            "pool": pool_name,
            "timestamp": time.time(),
            "pid": os.getpid(),
            "id": lock_id,
            "metadata": metadata or {},
        }

        # Create the actual resource lock
        with open(lock_file, "w", encoding="utf-8") as lock_f:
            json.dump(lock_data, lock_f)

        self._debug_log(
            f"Created lock: {lock_file} " f"({current_count + 1}/{max_resources})",
        )
        return lock_file

    def _handle_global_lock_error(
        self: "GlobalConcurrencyManager",
        error: OSError,
        pool_name: str,
        global_lock_file: Path,
    ) -> None:
        """Handle errors when creating global lock.

        Args:
            error: The OSError that occurred
            pool_name: Name of resource pool
            global_lock_file: Path to global lock file

        Returns:
            None
        """
        if error.errno == 17:  # File exists - another thread has the global lock
            self._debug_log(f"Global lock exists for {pool_name}, waiting")
        else:
            self._debug_log(f"Failed to create global lock {global_lock_file}: {error}")
        # Always return None as this is error handling

    def can_acquire_resource(self: "GlobalConcurrencyManager", pool_name: str) -> bool:
        """Check if a resource can be acquired without actually acquiring it.

        Args:
            pool_name: Name of the resource pool

        Returns:
            True if resource can be acquired, False otherwise
        """
        # Check if pool exists
        if pool_name not in self._resource_pools:
            return False

        pool_config = self._resource_pools[pool_name]
        max_resources = pool_config.get("max", 1)

        # Count current active locks
        active_count = self._count_active_locks(pool_name)

        return bool(active_count < max_resources)  # noqa: SIM901

    @contextmanager
    def acquire_resource(
        self: "GlobalConcurrencyManager",
        pool_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Generator[bool, None, None]:
        """Context manager for acquiring and releasing resources.

        Args:
            pool_name: Name of the resource pool
            metadata: Optional metadata about the operation
            timeout: Optional timeout in seconds (overrides pool default)

        Yields:
            True if resource was acquired, False otherwise
        """
        # Check if pool exists
        if pool_name not in self._resource_pools:
            self._debug_log(f"Unknown pool: {pool_name}")
            yield False
            return

        pool_config = self._resource_pools[pool_name]
        max_resources = pool_config.get("max", 1)
        actual_timeout = (
            timeout if timeout is not None else pool_config.get("timeout", 180)
        )

        lock_file = self._attempt_resource_acquisition(
            pool_name,
            max_resources,
            metadata,
            actual_timeout,
        )

        try:
            yield lock_file is not None
        finally:
            self._release_lock_file(lock_file)

    def _attempt_resource_acquisition(
        self: "GlobalConcurrencyManager",
        pool_name: str,
        max_resources: int,
        metadata: Optional[Dict[str, Any]],
        timeout: int,
    ) -> Optional[Path]:
        """Attempt to acquire a resource with timeout handling.

        Args:
            pool_name: Name of resource pool
            max_resources: Maximum number of resources
            metadata: Optional metadata for lock
            timeout: Timeout in seconds

        Returns:
            Path to lock file if successful, None otherwise
        """
        if timeout == 0:
            return self._try_acquire_lock_atomically(
                pool_name,
                max_resources,
                metadata,
            )

        return self._acquire_with_retry(pool_name, max_resources, metadata, timeout)

    def _acquire_with_retry(
        self: "GlobalConcurrencyManager",
        pool_name: str,
        max_resources: int,
        metadata: Optional[Dict[str, Any]],
        timeout: int,
    ) -> Optional[Path]:
        """Acquire resource with retry logic.

        Args:
            pool_name: Name of resource pool
            max_resources: Maximum number of resources
            metadata: Optional metadata for lock
            timeout: Timeout in seconds

        Returns:
            Path to lock file if successful, None otherwise
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            lock_file = self._try_acquire_lock_atomically(
                pool_name,
                max_resources,
                metadata,
            )
            if lock_file:
                return lock_file

            # Brief wait before retry
            time.sleep(0.5)

        # Timeout reached
        self._debug_log(f"Timeout acquiring resource from {pool_name}")
        return None

    def _release_lock_file(
        self: "GlobalConcurrencyManager", lock_file: Optional[Path]
    ) -> None:
        """Release a lock file if it exists.

        Args:
            lock_file: Path to lock file to release
        """
        if lock_file and lock_file.exists():
            try:
                lock_file.unlink()
                self._debug_log(f"Released lock: {lock_file}")
            except OSError as e:
                self._debug_log(f"Failed to release lock {lock_file}: {e}")

    def get_status(self: "GlobalConcurrencyManager") -> Dict[str, Any]:
        """Get current status of all resource pools.

        Returns:
            Dictionary with current counts and limits for all pools
        """
        status: Dict[str, Dict[str, Any]] = {
            "pools": {},
            "total": {"current": 0, "max": 0},
        }

        total_current = 0
        total_max = 0

        for pool_name, pool_config in self._resource_pools.items():
            current = self._count_active_locks(pool_name)
            max_count = pool_config.get("max", 1)

            total_current += current
            total_max += max_count

            status["pools"][pool_name] = {
                "current": current,
                "max": max_count,
                "available": max_count - current,
                "timeout": pool_config.get("timeout", 180),
                "description": pool_config.get("description", ""),
            }

        status["total"]["current"] = total_current
        status["total"]["max"] = total_max

        return status

    # Test helper methods - only for testing purposes
    def get_resource_pools_for_testing(self) -> Dict[str, Any]:
        """Get resource pools configuration (for testing only)."""
        return self._resource_pools

    def get_debug_for_testing(self) -> bool:
        """Get debug setting (for testing only)."""
        return self._debug

    def get_stale_timeout_for_testing(self) -> int:
        """Get stale timeout setting (for testing only)."""
        return self._stale_timeout


# Convenience function for easy import
def get_concurrency_manager(
    config_path: Optional[str] = None,
) -> "GlobalConcurrencyManager":
    """Get a global concurrency manager instance.

    Args:
        config_path: Optional path to configuration file

    Returns:
        GlobalConcurrencyManager instance
    """
    return GlobalConcurrencyManager(config_path)
