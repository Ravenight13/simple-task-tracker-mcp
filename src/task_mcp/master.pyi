"""Type stubs for master database operations module."""

import sqlite3

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
    ...

def init_master_schema(conn: sqlite3.Connection) -> None:
    """
    Initialize projects table.

    Schema:
    - id TEXT PRIMARY KEY (8-char hash)
    - workspace_path TEXT UNIQUE NOT NULL
    - friendly_name TEXT
    - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    - last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    Index:
    - idx_last_accessed ON projects(last_accessed)

    Args:
        conn: SQLite connection to initialize

    Raises:
        sqlite3.Error: If schema creation fails
    """
    ...

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
    ...
