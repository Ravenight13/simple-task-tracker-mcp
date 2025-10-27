"""Integration tests for database operations."""

from __future__ import annotations

import os
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
        """Test environment variable fallback."""
        monkeypatch.setenv("TASK_MCP_WORKSPACE", "/env/path")
        result = resolve_workspace()
        assert result == "/env/path"

    def test_resolve_workspace_cwd(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test current directory fallback."""
        monkeypatch.delenv("TASK_MCP_WORKSPACE", raising=False)
        result = resolve_workspace()
        assert result == os.getcwd()

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
