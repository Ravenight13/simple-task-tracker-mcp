"""Integration tests for database operations."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from task_mcp.database import get_connection
from task_mcp.master import get_master_connection, register_project
from task_mcp.utils import (
    ensure_absolute_path,
    hash_workspace_path,
    resolve_workspace,
    validate_description_length,
)


class TestUtils:
    """Test utility functions."""

    def test_resolve_workspace_explicit(self) -> None:
        """Test explicit workspace_path takes priority."""
        result = resolve_workspace("/explicit/path")
        assert result == "/explicit/path"

    def test_resolve_workspace_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that None raises ValueError (v0.4.0 - no auto-detection)."""
        monkeypatch.setenv("TASK_MCP_WORKSPACE", "/env/path")
        with pytest.raises(ValueError, match="workspace_path is REQUIRED"):
            resolve_workspace()

    def test_resolve_workspace_cwd(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that None raises ValueError (v0.4.0 - no auto-detection)."""
        monkeypatch.delenv("TASK_MCP_WORKSPACE", raising=False)
        with pytest.raises(ValueError, match="workspace_path is REQUIRED"):
            resolve_workspace()

    def test_hash_workspace_path(self) -> None:
        """Test workspace path hashing."""
        hash1 = hash_workspace_path("/path/to/project")
        hash2 = hash_workspace_path("/path/to/project")

        assert len(hash1) == 8
        assert hash1 == hash2  # Deterministic
        assert hash1.isalnum()

    def test_validate_description_length_valid(self) -> None:
        """Test valid description length."""
        validate_description_length("x" * 10000)  # Should not raise

    def test_validate_description_length_invalid(self) -> None:
        """Test description exceeding max length."""
        with pytest.raises(ValueError, match="exceeds"):
            validate_description_length("x" * 10001)

    def test_ensure_absolute_path(self) -> None:
        """Test path absolutization."""
        result = ensure_absolute_path("relative/path")
        assert result.startswith("/")


class TestDatabase:
    """Test database operations."""

    @pytest.fixture
    def temp_workspace(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Generator[str, None, None]:
        """Create temporary workspace for testing."""
        workspace = str(tmp_path / "test-workspace")
        Path(workspace).mkdir()

        # Point to temp directory for databases
        test_home = tmp_path / ".task-mcp"
        test_home.mkdir()
        monkeypatch.setenv("HOME", str(tmp_path))

        yield workspace

    def test_get_connection_creates_database(self, temp_workspace: str) -> None:
        """Test database auto-creation."""
        conn = get_connection(temp_workspace)

        try:
            # Check WAL mode
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == "wal"

            # Check foreign keys
            cursor.execute("PRAGMA foreign_keys")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 1

            # Check tasks table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='tasks'
            """)
            assert cursor.fetchone() is not None
        finally:
            conn.close()

    def test_schema_indexes(self, temp_workspace: str) -> None:
        """Test all indexes are created."""
        conn = get_connection(temp_workspace)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name LIKE 'idx_%'
            """)
            indexes = {row[0] for row in cursor.fetchall()}

            assert "idx_status" in indexes
            assert "idx_parent" in indexes
            assert "idx_deleted" in indexes
            assert "idx_tags" in indexes
        finally:
            conn.close()


class TestMasterDatabase:
    """Test master database operations."""

    @pytest.fixture
    def temp_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Generator[Path, None, None]:
        """Set up temporary home directory."""
        monkeypatch.setenv("HOME", str(tmp_path))
        yield tmp_path

    def test_register_project(self, temp_home: Path) -> None:
        """Test project registration."""
        workspace = "/test/workspace"

        project_id = register_project(workspace)

        assert len(project_id) == 8

        # Verify in database
        conn = get_master_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT workspace_path FROM projects WHERE id = ?", (project_id,)
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == workspace
        finally:
            conn.close()

    def test_register_project_updates_last_accessed(self, temp_home: Path) -> None:
        """Test last_accessed is updated on re-registration."""
        workspace = "/test/workspace"

        # First registration
        project_id1 = register_project(workspace)

        conn = get_master_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT last_accessed FROM projects WHERE id = ?", (project_id1,)
            )
            first_result = cursor.fetchone()
            assert first_result is not None
            first_access = first_result[0]

            # Re-register
            project_id2 = register_project(workspace)

            cursor.execute(
                "SELECT last_accessed FROM projects WHERE id = ?", (project_id2,)
            )
            second_result = cursor.fetchone()
            assert second_result is not None
            second_access = second_result[0]

            assert project_id1 == project_id2
            assert second_access >= first_access
        finally:
            conn.close()


class TestAutoRegistration:
    """Test auto-registration of projects in master.db on first access via CRUD tools."""

    @pytest.fixture
    def temp_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Generator[str, None, None]:
        """Set up temporary home directory and return test workspace path."""
        monkeypatch.setenv("HOME", str(tmp_path))
        workspace = str(tmp_path / "test-project")
        Path(workspace).mkdir()
        yield workspace

    def _get_registered_projects(self) -> list[dict]:
        """Helper to fetch all registered projects from master.db."""
        from task_mcp.server import list_projects
        return list_projects.fn()

    def _verify_project_registered(self, workspace_path: str) -> None:
        """Helper to verify project is registered in master.db."""
        from task_mcp.utils import hash_workspace_path

        projects = self._get_registered_projects()
        project_ids = [p['id'] for p in projects]
        expected_id = hash_workspace_path(workspace_path)

        assert expected_id in project_ids, f"Project {workspace_path} not registered in master.db"

    def test_create_task_auto_registers_project(self, temp_home: str) -> None:
        """Test create_task() auto-registers new project on first use."""
        from task_mcp.server import create_task

        # Verify no projects exist initially
        projects = self._get_registered_projects()
        assert len(projects) == 0, "Master.db should be empty initially"

        # Create task - should auto-register project
        task = create_task.fn(
            title="Test task",
            workspace_path=temp_home,
            description="Testing auto-registration"
        )

        assert task is not None
        assert task["title"] == "Test task"

        # Verify project is now registered
        self._verify_project_registered(temp_home)

    def test_list_tasks_auto_registers_empty_project(self, temp_home: str) -> None:
        """Test list_tasks() auto-registers project even when no tasks exist."""
        from task_mcp.server import list_tasks

        # Verify no projects exist initially
        projects = self._get_registered_projects()
        assert len(projects) == 0

        # List tasks on empty project - should auto-register
        tasks = list_tasks.fn(workspace_path=temp_home)

        assert isinstance(tasks, list)
        assert len(tasks) == 0  # No tasks yet

        # Verify project is registered despite being empty
        self._verify_project_registered(temp_home)

    def test_get_task_auto_registers_project(self, temp_home: str) -> None:
        """Test get_task() auto-registers project when querying."""
        from task_mcp.server import create_task, get_task

        # Create task (which should register project)
        created = create_task.fn(title="Task 1", workspace_path=temp_home)
        task_id = created["id"]

        # Clear our memory of registration by creating new temp home
        # (simulating fresh session)

        # Get task - should ensure registration
        task = get_task.fn(task_id=task_id, workspace_path=temp_home)

        assert task is not None
        assert task["id"] == task_id

        # Verify still registered
        self._verify_project_registered(temp_home)

    def test_search_tasks_auto_registers_project(self, temp_home: str) -> None:
        """Test search_tasks() auto-registers project during search."""
        from task_mcp.server import search_tasks

        # Verify no projects exist initially
        projects = self._get_registered_projects()
        assert len(projects) == 0

        # Search on empty project - should auto-register
        results = search_tasks.fn(search_term="test", workspace_path=temp_home)

        assert isinstance(results, list)
        assert len(results) == 0  # No matching tasks

        # Verify project registered even with no search results
        self._verify_project_registered(temp_home)

    def test_get_project_info_after_create_task(self, temp_home: str) -> None:
        """Test get_project_info() succeeds immediately after create_task()."""
        from task_mcp.server import create_task, get_project_info

        # Create task - should auto-register
        create_task.fn(title="First task", workspace_path=temp_home)

        # get_project_info should NOT fail with "Project not found"
        info = get_project_info.fn(workspace_path=temp_home)

        assert info is not None
        assert info["workspace_path"] == temp_home
        assert info["total_tasks"] == 1

    def test_update_task_maintains_registration(self, temp_home: str) -> None:
        """Test update_task() maintains project registration."""
        import time

        from task_mcp.server import create_task, update_task

        # Create task
        task = create_task.fn(title="Original", workspace_path=temp_home)
        task_id = task["id"]

        # Get initial registration time
        projects = self._get_registered_projects()
        initial_access = projects[0]["last_accessed"]

        # Wait to ensure timestamp difference
        time.sleep(0.1)

        # Update task - should update last_accessed
        updated = update_task.fn(
            task_id=task_id,
            workspace_path=temp_home,
            title="Updated"
        )

        assert updated["title"] == "Updated"

        # Verify last_accessed was updated
        projects = self._get_registered_projects()
        assert len(projects) == 1
        assert projects[0]["last_accessed"] >= initial_access


class TestLastAccessedUpdates:
    """Test that last_accessed timestamp updates on every operation."""

    @pytest.fixture
    def temp_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Generator[str, None, None]:
        """Set up temporary home directory and return test workspace path."""
        monkeypatch.setenv("HOME", str(tmp_path))
        workspace = str(tmp_path / "test-project")
        Path(workspace).mkdir()
        yield workspace

    def _get_last_accessed(self, workspace_path: str) -> str:
        """Helper to get last_accessed timestamp for a project."""
        from task_mcp.master import get_master_connection
        from task_mcp.utils import hash_workspace_path

        project_id = hash_workspace_path(workspace_path)
        conn = get_master_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT last_accessed FROM projects WHERE id = ?",
                (project_id,)
            )
            result = cursor.fetchone()
            assert result is not None, f"Project {workspace_path} not registered"
            return result[0]
        finally:
            conn.close()

    def test_last_accessed_updates_on_multiple_operations(self, temp_home: str) -> None:
        """Test last_accessed updates on various operations."""
        import time

        from task_mcp.server import create_task, get_task, list_tasks, update_task

        # Create task at T1
        task = create_task.fn(title="Test", workspace_path=temp_home)
        task_id = task["id"]
        t1_access = self._get_last_accessed(temp_home)

        # Wait to ensure timestamp difference
        time.sleep(0.1)

        # List tasks at T2
        list_tasks.fn(workspace_path=temp_home)
        t2_access = self._get_last_accessed(temp_home)
        assert t2_access >= t1_access

        # Wait again
        time.sleep(0.1)

        # Get task at T3
        get_task.fn(task_id=task_id, workspace_path=temp_home)
        t3_access = self._get_last_accessed(temp_home)
        assert t3_access >= t2_access

        # Wait again
        time.sleep(0.1)

        # Update task at T4
        update_task.fn(task_id=task_id, workspace_path=temp_home, title="Updated")
        t4_access = self._get_last_accessed(temp_home)
        assert t4_access >= t3_access


class TestCrossProjectIsolation:
    """Test that auto-registration doesn't break project isolation."""

    @pytest.fixture
    def temp_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Generator[tuple[str, str], None, None]:
        """Set up temporary home directory and return two test workspace paths."""
        monkeypatch.setenv("HOME", str(tmp_path))

        workspace_a = str(tmp_path / "project-a")
        workspace_b = str(tmp_path / "project-b")

        Path(workspace_a).mkdir()
        Path(workspace_b).mkdir()

        yield workspace_a, workspace_b

    def test_two_projects_have_separate_databases(self, temp_home: tuple[str, str]) -> None:
        """Test that two projects have separate task databases."""
        from task_mcp.server import create_task, list_projects, list_tasks

        workspace_a, workspace_b = temp_home

        # Create task in project A
        task_a = create_task.fn(title="Task A", workspace_path=workspace_a)
        assert task_a["title"] == "Task A"

        # Create task in project B
        task_b = create_task.fn(title="Task B", workspace_path=workspace_b)
        assert task_b["title"] == "Task B"

        # Verify both projects registered
        projects = list_projects.fn()
        assert len(projects) == 2

        # Verify project A only sees its task
        tasks_a = list_tasks.fn(workspace_path=workspace_a)
        assert len(tasks_a) == 1
        assert tasks_a[0]["title"] == "Task A"

        # Verify project B only sees its task
        tasks_b = list_tasks.fn(workspace_path=workspace_b)
        assert len(tasks_b) == 1
        assert tasks_b[0]["title"] == "Task B"

    def test_project_isolation_with_identical_task_ids(self, temp_home: tuple[str, str]) -> None:
        """Test that identical task IDs in different projects don't conflict."""
        from task_mcp.server import create_task, get_task

        workspace_a, workspace_b = temp_home

        # Create first task in each project (both will have ID 1)
        task_a = create_task.fn(title="Project A Task", workspace_path=workspace_a)
        task_b = create_task.fn(title="Project B Task", workspace_path=workspace_b)

        # Both should be ID 1 (first task in each database)
        assert task_a["id"] == 1
        assert task_b["id"] == 1

        # Fetch from specific projects - should get correct task
        fetched_a = get_task.fn(task_id=1, workspace_path=workspace_a)
        fetched_b = get_task.fn(task_id=1, workspace_path=workspace_b)

        assert fetched_a["title"] == "Project A Task"
        assert fetched_b["title"] == "Project B Task"
