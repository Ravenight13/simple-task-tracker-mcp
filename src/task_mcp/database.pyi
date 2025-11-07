"""Type stubs for database operations module."""

import sqlite3
from contextlib import AbstractContextManager

def get_connection(workspace_path: str | None = None) -> sqlite3.Connection:
    """
    Get SQLite connection for project database.

    Configures:
    - WAL mode for concurrent reads
    - Foreign keys enforcement
    - Busy timeout (5 seconds)
    - Auto-creates database and schema if not exists

    Args:
        workspace_path: Optional workspace path (uses resolve_workspace)

    Returns:
        Configured SQLite connection
    """
    ...

def init_schema(conn: sqlite3.Connection) -> None:
    """
    Initialize tasks table with all fields and indexes.

    Schema:
    - id INTEGER PRIMARY KEY AUTOINCREMENT
    - title TEXT NOT NULL
    - description TEXT (max 10k chars via app validation)
    - status TEXT CHECK(status IN ('todo', 'in_progress', 'blocked', 'done', 'cancelled'))
    - priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high'))
    - parent_task_id INTEGER (FK to tasks.id)
    - depends_on TEXT (JSON array)
    - tags TEXT (space-separated)
    - blocker_reason TEXT
    - file_references TEXT (JSON array)
    - created_by TEXT
    - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    - updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    - completed_at TIMESTAMP
    - deleted_at TIMESTAMP

    Indexes:
    - idx_status ON tasks(status)
    - idx_parent ON tasks(parent_task_id)
    - idx_deleted ON tasks(deleted_at)
    - idx_tags ON tasks(tags)

    Args:
        conn: SQLite connection to initialize

    Raises:
        sqlite3.Error: If schema creation fails
    """
    ...

def connection_context(
    workspace_path: str | None = None,
) -> AbstractContextManager[sqlite3.Connection]:
    """
    Context manager for database connections.

    Automatically commits on success, rolls back on error, and closes connection.

    Args:
        workspace_path: Optional workspace path

    Returns:
        Context manager yielding SQLite connection
    """
    ...
