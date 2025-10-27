"""Database operations for project-specific task databases."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

from .utils import get_project_db_path


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
    db_path = get_project_db_path(workspace_path)

    # Create connection
    conn = sqlite3.connect(str(db_path))

    # Configure SQLite settings (CRITICAL for concurrent access)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")

    # Enable row factory for dict-like access
    conn.row_factory = sqlite3.Row

    # Initialize schema if needed
    init_schema(conn)

    return conn


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
    - created_at TIMESTAMP
    - updated_at TIMESTAMP
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
    # Create tasks table with all fields and constraints
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL CHECK(status IN ('todo', 'in_progress', 'blocked', 'done', 'cancelled')),
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
            parent_task_id INTEGER,
            depends_on TEXT,
            tags TEXT,
            blocker_reason TEXT,
            file_references TEXT,
            created_by TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            completed_at TIMESTAMP,
            deleted_at TIMESTAMP,
            FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
        )
    """)

    # Create indexes for performance
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_parent ON tasks(parent_task_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_deleted ON tasks(deleted_at)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tags ON tasks(tags)
    """)

    # Commit schema changes
    conn.commit()


@contextmanager
def connection_context(workspace_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.

    Automatically commits on success, rolls back on error, and closes connection.

    Args:
        workspace_path: Optional workspace path

    Yields:
        SQLite connection
    """
    conn = get_connection(workspace_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
