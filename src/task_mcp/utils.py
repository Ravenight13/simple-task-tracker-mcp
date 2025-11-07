"""Utility functions for workspace detection, path hashing, and validation."""

import hashlib
import subprocess
from pathlib import Path


def resolve_workspace(workspace_path: str | None = None) -> str:
    """
    Resolve workspace path with REQUIRED explicit parameter.

    IMPORTANT: As of v0.4.0, workspace_path is REQUIRED to prevent
    cross-workspace contamination. All MCP tool calls must explicitly
    provide the workspace_path parameter.

    Args:
        workspace_path: REQUIRED explicit workspace path

    Returns:
        Absolute path to workspace directory

    Raises:
        ValueError: If workspace_path is None or empty
    """
    if not workspace_path:
        raise ValueError(
            "workspace_path is REQUIRED. "
            "Please provide an explicit workspace_path parameter "
            "to prevent cross-workspace contamination. "
            "Example: create_task(title='Fix bug', workspace_path='/path/to/project')"
        )

    return ensure_absolute_path(workspace_path)


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


def get_workspace_metadata(workspace_path: str | None = None) -> dict[str, str | None]:
    """
    Capture workspace metadata for task audit trail.

    Collects workspace context including resolved path, git repository root,
    current working directory, and project friendly name. This metadata
    enables cross-workspace validation and task contamination prevention.

    Args:
        workspace_path: Optional workspace path (resolved internally)

    Returns:
        Dictionary with workspace context:
        - workspace_path: Resolved absolute workspace path
        - git_root: Absolute path to git root (None if not a git repo)
        - cwd_at_creation: Absolute current working directory
        - project_name: Friendly name from master.db or workspace basename

    Examples:
        >>> get_workspace_metadata()
        {
            "workspace_path": "/Users/user/projects/task-mcp",
            "git_root": "/Users/user/projects/task-mcp",
            "cwd_at_creation": "/Users/user/projects/task-mcp/src",
            "project_name": "task-mcp"
        }

        >>> get_workspace_metadata("/path/to/non-git-project")
        {
            "workspace_path": "/path/to/non-git-project",
            "git_root": None,
            "cwd_at_creation": "/Users/user/projects/task-mcp",
            "project_name": "non-git-project"
        }
    """
    # Resolve workspace using existing logic
    resolved_workspace = resolve_workspace(workspace_path)

    # Get current working directory
    cwd = str(Path.cwd().resolve())

    # Detect git root (if any)
    git_root = _get_git_root(resolved_workspace)

    # Get project name from master.db or workspace basename
    project_name = _get_project_name(resolved_workspace)

    return {
        "workspace_path": resolved_workspace,
        "git_root": git_root,
        "cwd_at_creation": cwd,
        "project_name": project_name
    }


def _get_git_root(workspace_path: str) -> str | None:
    """
    Get git repository root for workspace.

    Uses `git rev-parse --show-toplevel` to detect git repository root.
    Handles non-git directories gracefully by returning None.

    Args:
        workspace_path: Absolute path to workspace

    Returns:
        Absolute path to git root, or None if not a git repo

    Examples:
        >>> _get_git_root("/Users/user/projects/task-mcp")
        "/Users/user/projects/task-mcp"

        >>> _get_git_root("/Users/user/non-git-directory")
        None

    Notes:
        - Uses 2-second timeout for subprocess operations
        - Handles FileNotFoundError if git is not installed
        - Returns None on any error (non-git directory, timeout, etc.)
    """
    try:
        result = subprocess.run(
            ["git", "-C", workspace_path, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _get_project_name(workspace_path: str) -> str:
    """
    Get project friendly name from master.db or workspace basename.

    Attempts to retrieve friendly_name from master.db projects table.
    Falls back to workspace directory name if:
    - friendly_name is not set in master.db
    - master.db is not accessible
    - Project not yet registered

    Args:
        workspace_path: Absolute path to workspace

    Returns:
        Project friendly name or workspace directory name

    Examples:
        >>> _get_project_name("/Users/user/projects/task-mcp")
        "task-mcp"  # from master.db friendly_name or basename

        >>> _get_project_name("/Users/user/new-project")
        "new-project"  # fallback to basename if not in master.db

    Notes:
        - Does NOT register project in master.db (read-only operation)
        - Handles database connection errors gracefully
        - Handles missing friendly_name gracefully (returns basename)
    """
    from .master import get_master_connection

    # Try to get friendly_name from master.db
    try:
        project_hash = hash_workspace_path(workspace_path)
        conn = get_master_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT friendly_name FROM projects WHERE id = ?",
            (project_hash,)
        )
        row = cursor.fetchone()
        conn.close()

        if row and row["friendly_name"]:
            return str(row["friendly_name"])
    except Exception:
        pass  # Fallback to basename

    # Fallback: use workspace directory name
    return Path(workspace_path).name
