"""
Integration tests for Entity System schema.

Validates:
- Entity tables creation
- Partial UNIQUE index behavior
- Soft delete + re-creation scenario
- CASCADE deletion behavior
- Zero breaking changes to tasks table
"""

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from task_mcp.database import get_connection, init_schema


class TestEntitySchemaMigration:
    """Test entity schema migration and structure."""

    def test_entities_table_created(self):
        """Verify entities table is created with correct schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)

            # Verify table exists
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='entities'
            """)
            assert cursor.fetchone() is not None

            # Verify columns
            cursor.execute("PRAGMA table_info(entities)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            expected_columns = {
                'id': 'INTEGER',
                'entity_type': 'TEXT',
                'name': 'TEXT',
                'identifier': 'TEXT',
                'description': 'TEXT',
                'metadata': 'TEXT',
                'tags': 'TEXT',
                'created_by': 'TEXT',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP',
                'deleted_at': 'TIMESTAMP'
            }

            assert columns == expected_columns
            conn.close()

    def test_task_entity_links_table_created(self):
        """Verify task_entity_links table is created with correct schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)

            # Verify table exists
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='task_entity_links'
            """)
            assert cursor.fetchone() is not None

            # Verify columns
            cursor.execute("PRAGMA table_info(task_entity_links)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            expected_columns = {
                'id': 'INTEGER',
                'task_id': 'INTEGER',
                'entity_id': 'INTEGER',
                'created_by': 'TEXT',
                'created_at': 'TIMESTAMP',
                'deleted_at': 'TIMESTAMP'
            }

            assert columns == expected_columns
            conn.close()

    def test_entity_indexes_created(self):
        """Verify all entity indexes are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)

            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='entities'
            """)
            indexes = {row[0] for row in cursor.fetchall()}

            expected_indexes = {
                'idx_entity_unique',
                'idx_entity_type',
                'idx_entity_deleted',
                'idx_entity_tags'
            }

            assert expected_indexes.issubset(indexes)
            conn.close()

    def test_link_indexes_created(self):
        """Verify all link indexes are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)

            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='task_entity_links'
            """)
            indexes = {row[0] for row in cursor.fetchall()}

            expected_indexes = {
                'idx_link_task',
                'idx_link_entity',
                'idx_link_deleted'
            }

            assert expected_indexes.issubset(indexes)
            conn.close()

    def test_entity_type_check_constraint(self):
        """Verify entity_type CHECK constraint enforces valid types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)

            # Valid entity types should work
            now = datetime.utcnow()
            conn.execute("""
                INSERT INTO entities (entity_type, name, created_at, updated_at)
                VALUES ('file', 'test.py', ?, ?)
            """, (now, now))

            conn.execute("""
                INSERT INTO entities (entity_type, name, created_at, updated_at)
                VALUES ('other', 'vendor', ?, ?)
            """, (now, now))

            # Invalid entity type should fail
            with pytest.raises(sqlite3.IntegrityError) as exc_info:
                conn.execute("""
                    INSERT INTO entities (entity_type, name, created_at, updated_at)
                    VALUES ('invalid', 'test', ?, ?)
                """, (now, now))

            assert "CHECK constraint failed" in str(exc_info.value)
            conn.close()


class TestPartialUniqueIndex:
    """Test partial UNIQUE index behavior for soft deletes."""

    def test_partial_unique_prevents_active_duplicates(self):
        """Partial UNIQUE index should prevent duplicate active entities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)
            now = datetime.utcnow()

            # Insert first entity
            conn.execute("""
                INSERT INTO entities (entity_type, identifier, name, created_at, updated_at)
                VALUES ('file', '/src/test.py', 'Test File', ?, ?)
            """, (now, now))

            # Try to insert duplicate (should fail)
            with pytest.raises(sqlite3.IntegrityError) as exc_info:
                conn.execute("""
                    INSERT INTO entities (entity_type, identifier, name, created_at, updated_at)
                    VALUES ('file', '/src/test.py', 'Duplicate', ?, ?)
                """, (now, now))

            assert "UNIQUE constraint failed" in str(exc_info.value)
            conn.close()

    def test_partial_unique_allows_null_identifiers(self):
        """Partial UNIQUE index should allow multiple NULL identifiers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)
            now = datetime.utcnow()

            # Insert multiple entities with NULL identifiers (should succeed)
            conn.execute("""
                INSERT INTO entities (entity_type, identifier, name, created_at, updated_at)
                VALUES ('other', NULL, 'Vendor 1', ?, ?)
            """, (now, now))

            conn.execute("""
                INSERT INTO entities (entity_type, identifier, name, created_at, updated_at)
                VALUES ('other', NULL, 'Vendor 2', ?, ?)
            """, (now, now))

            # Verify both were inserted
            cursor = conn.execute("""
                SELECT COUNT(*) FROM entities WHERE identifier IS NULL
            """)
            count = cursor.fetchone()[0]
            assert count == 2

            conn.close()

    def test_soft_delete_allows_recreation(self):
        """Soft deleting an entity should allow re-creating with same identifier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)
            now = datetime.utcnow()

            # Insert first entity
            cursor = conn.execute("""
                INSERT INTO entities (entity_type, identifier, name, created_at, updated_at)
                VALUES ('file', '/src/auth.py', 'Auth File v1', ?, ?)
            """, (now, now))
            entity1_id = cursor.lastrowid

            # Soft delete first entity
            conn.execute("""
                UPDATE entities SET deleted_at = ? WHERE id = ?
            """, (now, entity1_id))

            # Re-create entity with same identifier (should succeed)
            cursor = conn.execute("""
                INSERT INTO entities (entity_type, identifier, name, created_at, updated_at)
                VALUES ('file', '/src/auth.py', 'Auth File v2', ?, ?)
            """, (now, now))
            entity2_id = cursor.lastrowid

            # Verify both exist
            cursor = conn.execute("""
                SELECT id, name, deleted_at FROM entities
                WHERE identifier = '/src/auth.py'
                ORDER BY id
            """)
            results = cursor.fetchall()

            assert len(results) == 2
            assert results[0][0] == entity1_id
            assert results[0][1] == 'Auth File v1'
            assert results[0][2] is not None  # deleted_at set

            assert results[1][0] == entity2_id
            assert results[1][1] == 'Auth File v2'
            assert results[1][2] is None  # deleted_at not set

            conn.close()

    def test_different_entity_types_not_unique(self):
        """Different entity types can have same identifier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)
            now = datetime.utcnow()

            # Insert file entity with identifier 'test'
            conn.execute("""
                INSERT INTO entities (entity_type, identifier, name, created_at, updated_at)
                VALUES ('file', 'test', 'Test File', ?, ?)
            """, (now, now))

            # Insert other entity with same identifier (should succeed)
            conn.execute("""
                INSERT INTO entities (entity_type, identifier, name, created_at, updated_at)
                VALUES ('other', 'test', 'Test Vendor', ?, ?)
            """, (now, now))

            # Verify both exist
            cursor = conn.execute("""
                SELECT COUNT(*) FROM entities WHERE identifier = 'test'
            """)
            count = cursor.fetchone()[0]
            assert count == 2

            conn.close()


class TestCascadeDeletion:
    """Test CASCADE deletion behavior for foreign keys."""

    def test_task_deletion_cascades_to_links(self):
        """Deleting a task should CASCADE delete its entity links."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)
            now = datetime.utcnow()

            # Create task
            cursor = conn.execute("""
                INSERT INTO tasks (title, status, priority, created_at, updated_at)
                VALUES ('Test Task', 'todo', 'medium', ?, ?)
            """, (now, now))
            task_id = cursor.lastrowid

            # Create entity
            cursor = conn.execute("""
                INSERT INTO entities (entity_type, name, created_at, updated_at)
                VALUES ('file', 'test.py', ?, ?)
            """, (now, now))
            entity_id = cursor.lastrowid

            # Create link
            conn.execute("""
                INSERT INTO task_entity_links (task_id, entity_id, created_at)
                VALUES (?, ?, ?)
            """, (task_id, entity_id, now))

            # Verify link exists
            cursor = conn.execute("""
                SELECT COUNT(*) FROM task_entity_links
                WHERE task_id = ? AND entity_id = ?
            """, (task_id, entity_id))
            assert cursor.fetchone()[0] == 1

            # Delete task (hard delete for testing CASCADE)
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

            # Verify link was CASCADE deleted
            cursor = conn.execute("""
                SELECT COUNT(*) FROM task_entity_links
                WHERE task_id = ? AND entity_id = ?
            """, (task_id, entity_id))
            assert cursor.fetchone()[0] == 0

            conn.close()

    def test_entity_deletion_cascades_to_links(self):
        """Deleting an entity should CASCADE delete its task links."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)
            now = datetime.utcnow()

            # Create task
            cursor = conn.execute("""
                INSERT INTO tasks (title, status, priority, created_at, updated_at)
                VALUES ('Test Task', 'todo', 'medium', ?, ?)
            """, (now, now))
            task_id = cursor.lastrowid

            # Create entity
            cursor = conn.execute("""
                INSERT INTO entities (entity_type, name, created_at, updated_at)
                VALUES ('file', 'test.py', ?, ?)
            """, (now, now))
            entity_id = cursor.lastrowid

            # Create link
            conn.execute("""
                INSERT INTO task_entity_links (task_id, entity_id, created_at)
                VALUES (?, ?, ?)
            """, (task_id, entity_id, now))

            # Verify link exists
            cursor = conn.execute("""
                SELECT COUNT(*) FROM task_entity_links
                WHERE task_id = ? AND entity_id = ?
            """, (task_id, entity_id))
            assert cursor.fetchone()[0] == 1

            # Delete entity (hard delete for testing CASCADE)
            conn.execute("DELETE FROM entities WHERE id = ?", (entity_id,))

            # Verify link was CASCADE deleted
            cursor = conn.execute("""
                SELECT COUNT(*) FROM task_entity_links
                WHERE task_id = ? AND entity_id = ?
            """, (task_id, entity_id))
            assert cursor.fetchone()[0] == 0

            conn.close()


class TestTasksTableUnaffected:
    """Verify zero breaking changes to existing tasks table."""

    def test_tasks_table_unchanged(self):
        """Tasks table schema should be unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)

            # Verify tasks table structure
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(tasks)")
            columns = {row[1] for row in cursor.fetchall()}

            expected_columns = {
                'id', 'title', 'description', 'status', 'priority',
                'parent_task_id', 'depends_on', 'tags', 'blocker_reason',
                'file_references', 'created_by', 'created_at', 'updated_at',
                'completed_at', 'deleted_at'
            }

            assert columns == expected_columns
            conn.close()

    def test_task_operations_still_work(self):
        """Task CRUD operations should work exactly as before."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)
            now = datetime.utcnow()

            # Create task
            cursor = conn.execute("""
                INSERT INTO tasks (
                    title, description, status, priority,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('Test Task', 'Description', 'todo', 'high', now, now))
            task_id = cursor.lastrowid

            # Read task
            cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()
            assert task is not None
            assert task['title'] == 'Test Task'

            # Update task
            conn.execute("""
                UPDATE tasks SET status = 'done', completed_at = ?
                WHERE id = ?
            """, (now, task_id))

            # Verify update
            cursor = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
            assert cursor.fetchone()['status'] == 'done'

            # Soft delete task
            conn.execute("UPDATE tasks SET deleted_at = ? WHERE id = ?", (now, task_id))

            # Verify soft delete
            cursor = conn.execute("SELECT deleted_at FROM tasks WHERE id = ?", (task_id,))
            assert cursor.fetchone()['deleted_at'] is not None

            conn.close()

    def test_task_indexes_unchanged(self):
        """Task indexes should be unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = get_connection(tmpdir)

            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='tasks'
            """)
            indexes = {row[0] for row in cursor.fetchall()}

            expected_indexes = {
                'idx_status',
                'idx_parent',
                'idx_deleted',
                'idx_tags'
            }

            assert expected_indexes.issubset(indexes)
            conn.close()
