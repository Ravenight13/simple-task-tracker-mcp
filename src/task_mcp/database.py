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
    Initialize database schema with tasks, entities, and links tables.

    Tasks Table:
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

    Entities Table (v0.3.0):
    - id INTEGER PRIMARY KEY AUTOINCREMENT
    - entity_type TEXT NOT NULL CHECK(entity_type IN ('file', 'other'))
    - name TEXT NOT NULL
    - identifier TEXT (unique per type for active entities)
    - description TEXT
    - metadata TEXT (JSON)
    - tags TEXT (space-separated)
    - created_by TEXT
    - created_at TIMESTAMP NOT NULL
    - updated_at TIMESTAMP NOT NULL
    - deleted_at TIMESTAMP

    Task Entity Links Table (v0.3.0):
    - id INTEGER PRIMARY KEY AUTOINCREMENT
    - task_id INTEGER NOT NULL (FK to tasks.id)
    - entity_id INTEGER NOT NULL (FK to entities.id)
    - created_by TEXT
    - created_at TIMESTAMP NOT NULL
    - deleted_at TIMESTAMP
    - UNIQUE(task_id, entity_id)

    Indexes:
    Tasks:
    - idx_status ON tasks(status)
    - idx_parent ON tasks(parent_task_id)
    - idx_deleted ON tasks(deleted_at)
    - idx_tags ON tasks(tags)

    Entities:
    - idx_entity_unique UNIQUE ON entities(entity_type, identifier) WHERE deleted_at IS NULL
    - idx_entity_type ON entities(entity_type)
    - idx_entity_deleted ON entities(deleted_at)
    - idx_entity_tags ON entities(tags)

    Links:
    - idx_link_task ON task_entity_links(task_id)
    - idx_link_entity ON task_entity_links(entity_id)
    - idx_link_deleted ON task_entity_links(deleted_at)

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

    # ============================================================================
    # ENTITY SYSTEM TABLES (v0.3.0)
    # ============================================================================

    # Create entities table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL CHECK(entity_type IN ('file', 'other')),
            name TEXT NOT NULL,
            identifier TEXT,
            description TEXT,
            metadata TEXT,
            tags TEXT,
            created_by TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP
        )
    """)

    # Create partial UNIQUE index (CRITICAL for soft delete compatibility)
    # This enforces uniqueness ONLY for active (non-deleted) entities
    # Allows re-creating entities with same identifier after soft delete
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_entity_unique
        ON entities(entity_type, identifier)
        WHERE deleted_at IS NULL AND identifier IS NOT NULL
    """)

    # Create performance indexes for entities
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_deleted ON entities(deleted_at)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_tags ON entities(tags)
    """)

    # Create task-entity links junction table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_entity_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            entity_id INTEGER NOT NULL,
            created_by TEXT,
            created_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
            UNIQUE(task_id, entity_id)
        )
    """)

    # Create indexes for links (bidirectional queries)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_link_task ON task_entity_links(task_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_link_entity ON task_entity_links(entity_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_link_deleted ON task_entity_links(deleted_at)
    """)

    # Commit all schema changes
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
