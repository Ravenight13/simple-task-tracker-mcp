"""Master database operations for project registry."""

import sqlite3
from datetime import datetime

from .utils import ensure_absolute_path, get_master_db_path, hash_workspace_path


def get_master_connection() -> sqlite3.Connection:
    """
    Get connection to master.db with WAL mode.

    Configures:
    - WAL mode for concurrent reads
    - Foreign keys enforcement
    - Busy timeout (5 seconds)
    - Auto-creates database and schema if not exists

    Returns:
        Configured SQLite connection to master database
    """
    db_path = get_master_db_path()

    # Create connection
    conn = sqlite3.connect(str(db_path))

    # Configure SQLite settings (CRITICAL for concurrent access)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")

    # Enable row factory for dict-like access
    conn.row_factory = sqlite3.Row

    # Initialize schema if needed
    init_master_schema(conn)

    return conn


def init_master_schema(conn: sqlite3.Connection) -> None:
    """
    Initialize master database schema.

    Projects table schema:
    - id TEXT PRIMARY KEY (8-char hash)
    - workspace_path TEXT UNIQUE NOT NULL
    - friendly_name TEXT
    - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    - last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    Tool usage table schema:
    - id INTEGER PRIMARY KEY AUTOINCREMENT
    - tool_name TEXT NOT NULL
    - workspace_id TEXT NOT NULL (FK to projects.id)
    - timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    - success BOOLEAN NOT NULL DEFAULT 1

    Indexes:
    - idx_last_accessed ON projects(last_accessed)
    - idx_tool_usage_timestamp ON tool_usage(timestamp)
    - idx_tool_usage_tool_name ON tool_usage(tool_name)
    - idx_tool_usage_workspace ON tool_usage(workspace_id)

    Args:
        conn: SQLite connection to initialize

    Raises:
        sqlite3.Error: If schema creation fails
    """
    # Create projects table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            workspace_path TEXT UNIQUE NOT NULL,
            friendly_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create index for sorting by last access
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_last_accessed ON projects(last_accessed)
    """)

    # Create tool_usage table for tracking MCP tool calls
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tool_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN NOT NULL DEFAULT 1,
            FOREIGN KEY (workspace_id) REFERENCES projects(id)
        )
    """)

    # Create indexes for efficient querying on tool_usage
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tool_usage_timestamp ON tool_usage(timestamp)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tool_usage_tool_name ON tool_usage(tool_name)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tool_usage_workspace ON tool_usage(workspace_id)
    """)

    # Commit schema changes
    conn.commit()


def register_project(workspace_path: str) -> str:
    """
    Register project in master.db (or update last_accessed).

    If project already exists, updates last_accessed timestamp.
    If project is new, creates entry with generated hash ID.

    Args:
        workspace_path: Absolute path to project workspace

    Returns:
        Project hash ID (8 characters)

    Raises:
        ValueError: If workspace_path is invalid
        sqlite3.Error: If database operation fails
    """
    # Validate and normalize workspace path
    workspace_path = ensure_absolute_path(workspace_path)

    # Generate project hash ID
    project_id = hash_workspace_path(workspace_path)

    # Get master database connection
    conn = get_master_connection()

    try:
        # Check if project exists
        cursor = conn.execute(
            "SELECT id FROM projects WHERE id = ?",
            (project_id,)
        )
        existing = cursor.fetchone()

        if existing:
            # Update last_accessed timestamp
            conn.execute(
                "UPDATE projects SET last_accessed = ? WHERE id = ?",
                (datetime.now().isoformat(), project_id)
            )
        else:
            # Insert new project record
            conn.execute(
                """
                INSERT INTO projects (id, workspace_path, created_at, last_accessed)
                VALUES (?, ?, ?, ?)
                """,
                (
                    project_id,
                    workspace_path,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                )
            )

        conn.commit()
        return project_id

    finally:
        conn.close()
