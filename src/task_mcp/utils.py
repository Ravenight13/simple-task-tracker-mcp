"""Utility functions for workspace detection, path hashing, and validation."""

import hashlib
import os
from pathlib import Path


def resolve_workspace(workspace_path: str | None = None) -> str:
    """
    Resolve workspace path using priority order.

    Priority:
    1. Explicit workspace_path parameter
    2. TASK_MCP_WORKSPACE environment variable
    3. Current working directory (fallback)

    Args:
        workspace_path: Optional explicit workspace path

    Returns:
        Absolute path to workspace directory
    """
    if workspace_path:
        return ensure_absolute_path(workspace_path)

    env_workspace = os.environ.get("TASK_MCP_WORKSPACE")
    if env_workspace:
        return ensure_absolute_path(env_workspace)

    return str(Path.cwd().resolve())


def hash_workspace_path(workspace_path: str) -> str:
    """
    Hash workspace path to create safe database filename.

    Uses SHA256 hash, truncated to 8 characters for brevity
    while maintaining sufficient uniqueness for typical usage.

    Args:
        workspace_path: Path to workspace directory

    Returns:
        8-character lowercase hexadecimal hash string (e.g., "a1b2c3d4")
    """
    return hashlib.sha256(workspace_path.encode()).hexdigest()[:8]


def get_project_db_path(workspace_path: str | None = None) -> Path:
    """
    Generate project-specific database path.

    Creates database path in format: ~/.task-mcp/databases/project_{hash}.db
    where {hash} is derived from the workspace path.

    Creates ~/.task-mcp/databases/ directory if it doesn't exist.

    Args:
        workspace_path: Optional workspace path (passed to resolve_workspace)

    Returns:
        Path to project-specific database file
    """
    resolved_workspace = resolve_workspace(workspace_path)
    project_hash = hash_workspace_path(resolved_workspace)

    # Ensure databases directory exists
    databases_dir = Path.home() / ".task-mcp" / "databases"
    databases_dir.mkdir(parents=True, exist_ok=True)

    return databases_dir / f"project_{project_hash}.db"


def get_master_db_path() -> Path:
    """
    Get master database path.

    Returns path to master database at ~/.task-mcp/master.db
    Creates ~/.task-mcp/ directory if it doesn't exist.

    Returns:
        Path to master database file
    """
    task_mcp_dir = Path.home() / ".task-mcp"
    task_mcp_dir.mkdir(parents=True, exist_ok=True)
    return task_mcp_dir / "master.db"


def validate_description_length(description: str | None) -> None:
    """
    Validate description length constraint.

    Args:
        description: Optional description text to validate

    Raises:
        ValueError: If description exceeds 10,000 characters
    """
    if description and len(description) > 10000:
        raise ValueError(
            f"Description exceeds 10,000 character limit (got {len(description)} chars)"
        )


def ensure_absolute_path(path: str) -> str:
    """
    Convert path to absolute path and validate.

    Args:
        path: Path string to convert

    Returns:
        Absolute path string

    Raises:
        ValueError: If path is invalid or empty
    """
    if not path or not path.strip():
        raise ValueError("Path cannot be empty")

    return str(Path(path).resolve())
