#!/usr/bin/env python3
"""Verification script to test database creation and configuration."""

import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from task_mcp import database, master


def verify_project_database() -> None:
    """Verify project database creation and schema."""
    print("Testing project database...")

    # Use temporary workspace for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "test-project")
        Path(workspace).mkdir()

        # Get connection
        conn = database.get_connection(workspace)

        # Verify WAL mode
        cursor = conn.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode == "wal", f"Expected WAL mode, got {journal_mode}"
        print("✓ WAL mode enabled")

        # Verify foreign keys
        cursor = conn.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        assert fk_enabled == 1, "Foreign keys not enabled"
        print("✓ Foreign keys enabled")

        # Verify tasks table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
        )
        assert cursor.fetchone() is not None, "Tasks table not created"
        print("✓ Tasks table created")

        # Verify indexes exist
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = {row[0] for row in cursor.fetchall()}
        expected_indexes = {"idx_status", "idx_parent", "idx_deleted", "idx_tags"}
        assert indexes == expected_indexes, f"Missing indexes: {expected_indexes - indexes}"
        print("✓ All indexes created")

        # Verify schema constraints
        cursor = conn.execute("PRAGMA table_info(tasks)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type

        required_columns = {
            "id", "title", "description", "status", "priority",
            "parent_task_id", "depends_on", "tags", "blocker_reason",
            "file_references", "created_by", "created_at", "updated_at",
            "completed_at", "deleted_at"
        }
        assert set(columns.keys()) == required_columns, "Missing columns"
        print("✓ All columns present")

        conn.close()
        print("✓ Project database verification passed!\n")


def verify_master_database() -> None:
    """Verify master database creation and schema."""
    print("Testing master database...")

    # Get connection
    conn = master.get_master_connection()

    # Verify WAL mode
    cursor = conn.execute("PRAGMA journal_mode")
    journal_mode = cursor.fetchone()[0]
    assert journal_mode == "wal", f"Expected WAL mode, got {journal_mode}"
    print("✓ WAL mode enabled")

    # Verify projects table exists
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
    )
    assert cursor.fetchone() is not None, "Projects table not created"
    print("✓ Projects table created")

    # Verify index exists
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_last_accessed'"
    )
    assert cursor.fetchone() is not None, "idx_last_accessed not created"
    print("✓ Index created")

    # Verify schema
    cursor = conn.execute("PRAGMA table_info(projects)")
    columns = {row[1] for row in cursor.fetchall()}

    expected_columns = {"id", "workspace_path", "friendly_name", "created_at", "last_accessed"}
    assert columns == expected_columns, "Missing columns"
    print("✓ All columns present")

    conn.close()
    print("✓ Master database verification passed!\n")


def verify_project_registration() -> None:
    """Verify project registration functionality."""
    print("Testing project registration...")

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "test-project")
        Path(workspace).mkdir()

        # Register project
        project_id = master.register_project(workspace)
        assert len(project_id) == 8, "Project ID should be 8 characters"
        print(f"✓ Project registered with ID: {project_id}")

        # Verify registration
        conn = master.get_master_connection()
        cursor = conn.execute("SELECT workspace_path FROM projects WHERE id = ?", (project_id,))
        result = cursor.fetchone()
        assert result is not None, "Project not found in database"
        # Workspace is resolved to absolute path, so compare resolved versions
        from task_mcp.utils import ensure_absolute_path
        assert result[0] == ensure_absolute_path(workspace), "Workspace path mismatch"
        print("✓ Project registration verified")

        conn.close()
        print("✓ Project registration verification passed!\n")


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Database Verification Script")
        print("=" * 60 + "\n")

        verify_project_database()
        verify_master_database()
        verify_project_registration()

        print("=" * 60)
        print("ALL VERIFICATIONS PASSED!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ VERIFICATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
