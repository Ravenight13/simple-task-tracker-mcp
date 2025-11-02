"""Tests for usage tracking functionality."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from task_mcp.master import (
    get_master_connection,
    get_project_id,
    init_master_schema,
    record_tool_usage,
    register_project,
)
from task_mcp.server import get_usage_stats


@pytest.fixture
def test_workspace_tracking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> str:
    """Create temporary workspace for tracking tests."""
    workspace = tmp_path / "test_tracking_workspace"
    workspace.mkdir()
    # Set HOME to temp directory to isolate master.db
    monkeypatch.setenv("HOME", str(tmp_path))
    return str(workspace)


class TestToolUsageSchema:
    """Test tool_usage table schema."""

    def test_tool_usage_table_created(
        self, test_workspace_tracking: str
    ) -> None:
        """Verify tool_usage table exists in master.db."""
        conn = get_master_connection()
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='tool_usage'
        """)
        assert cursor.fetchone() is not None

        # Check columns
        cursor.execute("PRAGMA table_info(tool_usage)")
        columns = {row[1] for row in cursor.fetchall()}
        assert columns == {
            "id",
            "tool_name",
            "workspace_id",
            "timestamp",
            "success",
        }

        conn.close()

    def test_tool_usage_indexes_created(
        self, test_workspace_tracking: str
    ) -> None:
        """Verify indexes on tool_usage table."""
        conn = get_master_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='tool_usage'
        """)
        indexes = {row[0] for row in cursor.fetchall()}

        assert "idx_tool_usage_timestamp" in indexes
        assert "idx_tool_usage_tool_name" in indexes
        assert "idx_tool_usage_workspace" in indexes

        conn.close()


class TestRecordToolUsage:
    """Test record_tool_usage function."""

    def test_record_successful_call(self, test_workspace_tracking: str) -> None:
        """Test recording a successful tool call."""
        # Register project first (required for foreign key constraint)
        workspace_id = register_project(test_workspace_tracking)

        record_tool_usage("test_tool", workspace_id, success=True)

        conn = get_master_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tool_name, workspace_id, success
            FROM tool_usage
            WHERE tool_name = 'test_tool' AND workspace_id = ?
        """, (workspace_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == "test_tool"
        assert row[1] == workspace_id
        assert row[2] == 1  # SQLite stores boolean as 1

        conn.close()

    def test_record_failed_call(self, test_workspace_tracking: str) -> None:
        """Test recording a failed tool call."""
        # Register project first (required for foreign key constraint)
        workspace_id = register_project(test_workspace_tracking)

        record_tool_usage("failing_tool", workspace_id, success=False)

        conn = get_master_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT success FROM tool_usage
            WHERE tool_name = 'failing_tool' AND workspace_id = ?
        """, (workspace_id,))
        row = cursor.fetchone()

        assert row[0] == 0  # SQLite stores False as 0

        conn.close()

    def test_record_multiple_calls(self, test_workspace_tracking: str) -> None:
        """Test recording multiple calls for same tool."""
        # Register project first (required for foreign key constraint)
        workspace_id = register_project(test_workspace_tracking)

        # Record multiple calls
        record_tool_usage("list_tasks", workspace_id, success=True)
        record_tool_usage("list_tasks", workspace_id, success=True)
        record_tool_usage("list_tasks", workspace_id, success=False)

        conn = get_master_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM tool_usage
            WHERE tool_name = 'list_tasks' AND workspace_id = ?
        """, (workspace_id,))
        count = cursor.fetchone()[0]

        assert count == 3

        conn.close()

    def test_timestamp_recorded(self, test_workspace_tracking: str) -> None:
        """Test that timestamp is automatically recorded."""
        # Register project first (required for foreign key constraint)
        workspace_id = register_project(test_workspace_tracking)

        record_tool_usage("timestamped_tool", workspace_id)

        conn = get_master_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp FROM tool_usage
            WHERE tool_name = 'timestamped_tool' AND workspace_id = ?
        """, (workspace_id,))
        row = cursor.fetchone()

        # Timestamp should be present and be a valid ISO 8601 datetime string
        assert row is not None
        assert row[0] is not None

        # Verify it's a valid ISO datetime format
        timestamp = datetime.fromisoformat(row[0])
        assert isinstance(timestamp, datetime)

        # Verify it's a recent timestamp (from today)
        today = datetime.now().date()
        assert timestamp.date() == today

        conn.close()


class TestGetUsageStats:
    """Test get_usage_stats MCP tool."""

    def test_get_stats_with_data(self, test_workspace_tracking: str) -> None:
        """Test getting usage stats with sample data."""
        # Register project first (required for foreign key constraint)
        workspace_id = register_project(test_workspace_tracking)

        # Record some usage
        record_tool_usage("list_tasks", workspace_id, success=True)
        record_tool_usage("list_tasks", workspace_id, success=True)
        record_tool_usage("create_task", workspace_id, success=True)
        record_tool_usage("get_task", workspace_id, success=False)

        # Extract underlying function from FastMCP wrapper
        stats = get_usage_stats.fn(
            workspace_path=test_workspace_tracking, days=30
        )

        assert stats["total_calls"] == 4
        assert stats["successful_calls"] == 3
        assert stats["success_rate"] == 75.0
        assert len(stats["tools"]) == 3

        # Check list_tasks is first (most calls)
        assert stats["tools"][0]["tool_name"] == "list_tasks"
        assert stats["tools"][0]["calls"] == 2
        assert stats["tools"][0]["successful"] == 2
        assert stats["tools"][0]["success_rate"] == 100.0

        # Check failed tool
        failed_tool = next(
            t for t in stats["tools"] if t["tool_name"] == "get_task"
        )
        assert failed_tool["calls"] == 1
        assert failed_tool["successful"] == 0
        assert failed_tool["success_rate"] == 0.0

    def test_get_stats_filter_by_tool(
        self, test_workspace_tracking: str
    ) -> None:
        """Test filtering stats by specific tool name."""
        # Register project first (required for foreign key constraint)
        workspace_id = register_project(test_workspace_tracking)

        record_tool_usage("list_tasks", workspace_id, success=True)
        record_tool_usage("create_task", workspace_id, success=True)

        stats = get_usage_stats.fn(
            workspace_path=test_workspace_tracking,
            days=30,
            tool_name="list_tasks",
        )

        assert stats["total_calls"] == 1
        assert len(stats["tools"]) == 1
        assert stats["tools"][0]["tool_name"] == "list_tasks"
        assert stats["filter"]["tool_name"] == "list_tasks"

    def test_get_stats_empty_workspace(
        self, test_workspace_tracking: str
    ) -> None:
        """Test getting stats for workspace with no usage."""
        # Register project first (creates empty workspace)
        register_project(test_workspace_tracking)

        stats = get_usage_stats.fn(
            workspace_path=test_workspace_tracking, days=30
        )

        assert stats["total_calls"] == 0
        # successful_calls is None when there are no calls (SQL SUM returns NULL)
        assert stats["successful_calls"] in (0, None)
        assert stats["success_rate"] == 0
        assert len(stats["tools"]) == 0
        assert len(stats["timeline"]) == 0

    def test_get_stats_date_range_filter(
        self, test_workspace_tracking: str
    ) -> None:
        """Test that date range filtering works correctly."""
        # Register project first (required for foreign key constraint)
        workspace_id = register_project(test_workspace_tracking)

        # Record usage
        record_tool_usage("list_tasks", workspace_id, success=True)

        # Query with 30 day range
        stats_30 = get_usage_stats.fn(
            workspace_path=test_workspace_tracking, days=30
        )
        assert stats_30["total_calls"] == 1
        assert stats_30["date_range"]["days"] == 30

        # Query with 7 day range
        stats_7 = get_usage_stats.fn(
            workspace_path=test_workspace_tracking, days=7
        )
        assert stats_7["total_calls"] == 1
        assert stats_7["date_range"]["days"] == 7

    def test_get_stats_timeline(self, test_workspace_tracking: str) -> None:
        """Test that timeline data is included."""
        # Register project first (required for foreign key constraint)
        workspace_id = register_project(test_workspace_tracking)

        # Record multiple calls
        record_tool_usage("list_tasks", workspace_id, success=True)
        record_tool_usage("create_task", workspace_id, success=True)

        stats = get_usage_stats.fn(
            workspace_path=test_workspace_tracking, days=30
        )

        assert len(stats["timeline"]) >= 1
        # Today should have 2 calls
        today = datetime.now().date().isoformat()
        today_stats = next(
            (t for t in stats["timeline"] if t["date"] == today), None
        )
        assert today_stats is not None
        assert today_stats["calls"] == 2

    def test_get_stats_multiple_workspaces(
        self, test_workspace_tracking: str, tmp_path: Path
    ) -> None:
        """Test that stats are isolated per workspace."""
        # Register first project
        workspace_id_1 = register_project(test_workspace_tracking)

        # Create second workspace
        workspace_2 = tmp_path / "test_tracking_workspace_2"
        workspace_2.mkdir()
        # Register second project
        workspace_id_2 = register_project(str(workspace_2))

        # Record usage in both workspaces
        record_tool_usage("list_tasks", workspace_id_1, success=True)
        record_tool_usage("list_tasks", workspace_id_1, success=True)
        record_tool_usage("create_task", workspace_id_2, success=True)

        # Stats for workspace 1
        stats_1 = get_usage_stats.fn(
            workspace_path=test_workspace_tracking, days=30
        )
        assert stats_1["total_calls"] == 2
        assert stats_1["filter"]["workspace_id"] == workspace_id_1

        # Stats for workspace 2
        stats_2 = get_usage_stats.fn(workspace_path=str(workspace_2), days=30)
        assert stats_2["total_calls"] == 1
        assert stats_2["filter"]["workspace_id"] == workspace_id_2

    def test_success_rate_calculation(
        self, test_workspace_tracking: str
    ) -> None:
        """Test success rate calculation accuracy."""
        # Register project first (required for foreign key constraint)
        workspace_id = register_project(test_workspace_tracking)

        # 3 success, 1 failure = 75% success rate
        record_tool_usage("test_tool", workspace_id, success=True)
        record_tool_usage("test_tool", workspace_id, success=True)
        record_tool_usage("test_tool", workspace_id, success=True)
        record_tool_usage("test_tool", workspace_id, success=False)

        stats = get_usage_stats.fn(
            workspace_path=test_workspace_tracking,
            days=30,
            tool_name="test_tool",
        )

        assert stats["total_calls"] == 4
        assert stats["successful_calls"] == 3
        assert stats["success_rate"] == 75.0


class TestUsageTrackingIntegration:
    """Test integration of usage tracking with MCP tools."""

    def test_tracking_doesnt_break_tools(
        self, test_workspace_tracking: str
    ) -> None:
        """Verify that tracking doesn't break tool functionality."""
        from task_mcp.server import create_task

        # Tools should work even if tracking fails
        # (In this case, project not registered yet, so tracking will silently fail)
        task = create_task.fn(
            title="Test Task",
            workspace_path=test_workspace_tracking,
        )

        # Tool should work regardless of tracking status
        assert task["title"] == "Test Task"
        assert task["status"] == "todo"

    def test_manual_tracking_integration(
        self, test_workspace_tracking: str
    ) -> None:
        """Verify manual tracking integration pattern."""
        # This tests the pattern that would be used by the decorator
        # Register project first
        workspace_id = register_project(test_workspace_tracking)

        # Simulate what the decorator does: record tool usage
        record_tool_usage("manual_tool", workspace_id, success=True)

        # Verify tracking recorded
        conn = get_master_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM tool_usage
            WHERE tool_name = 'manual_tool' AND workspace_id = ?
        """, (workspace_id,))
        count = cursor.fetchone()[0]

        assert count == 1

        conn.close()
