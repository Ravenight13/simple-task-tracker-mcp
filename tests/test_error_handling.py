"""Comprehensive error handling tests for Task MCP tools."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from task_mcp import server

# Extract underlying functions from FastMCP FunctionTool wrappers
create_task = server.create_task.fn
list_tasks = server.list_tasks.fn
search_tasks = server.search_tasks.fn
get_task = server.get_task.fn
update_task = server.update_task.fn
create_entity = server.create_entity.fn
list_entities = server.list_entities.fn
search_entities = server.search_entities.fn
get_entity = server.get_entity.fn
get_task_entities = server.get_task_entities.fn
get_entity_tasks = server.get_entity_tasks.fn


@pytest.fixture
def test_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[str, None, None]:
    """Create isolated test workspace."""
    workspace = str(tmp_path / "test-project")
    Path(workspace).mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    yield workspace


class TestInvalidModeErrors:
    """Test error handling for invalid mode parameter."""

    def test_list_tasks_invalid_mode_raises_error(self, test_workspace: str) -> None:
        """Test that invalid mode value raises ValueError."""
        create_task(
            title="Test Task",
            workspace_path=test_workspace,
        )

        with pytest.raises(ValueError) as exc_info:
            list_tasks(
                workspace_path=test_workspace,
                mode="invalid_mode",  # Invalid
            )

        error_msg = str(exc_info.value)
        assert "Invalid mode" in error_msg or "must be" in error_msg.lower()

    def test_list_tasks_mode_case_sensitive(self, test_workspace: str) -> None:
        """Test that mode is case-sensitive."""
        create_task(
            title="Test Task",
            workspace_path=test_workspace,
        )

        # "Summary" should fail (must be lowercase "summary")
        with pytest.raises(ValueError):
            list_tasks(
                workspace_path=test_workspace,
                mode="Summary",  # Wrong case
            )

    def test_search_tasks_invalid_mode(self, test_workspace: str) -> None:
        """Test invalid mode in search_tasks."""
        create_task(
            title="Search me",
            workspace_path=test_workspace,
        )

        with pytest.raises(ValueError):
            search_tasks(
                search_term="Search",
                workspace_path=test_workspace,
                mode="bad_mode",
            )

    def test_list_entities_invalid_mode(self, test_workspace: str) -> None:
        """Test invalid mode in list_entities."""
        create_entity(
            entity_type="file",
            name="test.py",
            workspace_path=test_workspace,
        )

        with pytest.raises(ValueError):
            list_entities(
                workspace_path=test_workspace,
                mode="invalid",
            )

    def test_search_entities_invalid_mode(self, test_workspace: str) -> None:
        """Test invalid mode in search_entities."""
        create_entity(
            entity_type="file",
            name="test.py",
            workspace_path=test_workspace,
        )

        with pytest.raises(ValueError):
            search_entities(
                search_term="test",
                workspace_path=test_workspace,
                mode="wrong_mode",
            )

    def test_get_task_entities_invalid_mode(self, test_workspace: str) -> None:
        """Test invalid mode in get_task_entities."""
        task = create_task(
            title="Test",
            workspace_path=test_workspace,
        )

        with pytest.raises(ValueError):
            get_task_entities(
                task_id=task["id"],
                workspace_path=test_workspace,
                mode="invalid_mode",
            )

    def test_get_entity_tasks_invalid_mode(self, test_workspace: str) -> None:
        """Test invalid mode in get_entity_tasks."""
        entity = create_entity(
            entity_type="file",
            name="test.py",
            workspace_path=test_workspace,
        )

        with pytest.raises(ValueError):
            get_entity_tasks(
                entity_id=entity["id"],
                workspace_path=test_workspace,
                mode="invalid",
            )


class TestInvalidFilterErrors:
    """Test error handling for invalid filter values."""

    def test_list_tasks_invalid_status(self, test_workspace: str) -> None:
        """Test that invalid status filter works (no validation currently)."""
        create_task(
            title="Task",
            workspace_path=test_workspace,
        )

        # Invalid status should return empty results (not error)
        tasks: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            status="invalid_status",
        )

        assert len(tasks) == 0

    def test_list_tasks_invalid_priority(self, test_workspace: str) -> None:
        """Test that invalid priority filter works (no validation currently)."""
        create_task(
            title="Task",
            workspace_path=test_workspace,
        )

        # Invalid priority should return empty results
        tasks: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            priority="super_high",  # Invalid
        )

        assert len(tasks) == 0

    def test_get_entity_tasks_invalid_status_filter(self, test_workspace: str) -> None:
        """Test invalid status filter in get_entity_tasks."""
        entity = create_entity(
            entity_type="file",
            name="test.py",
            workspace_path=test_workspace,
        )

        task = create_task(
            title="Task",
            workspace_path=test_workspace,
        )

        from task_mcp.server import link_entity_to_task
        link_entity_to_task.fn(
            task_id=task["id"],
            entity_id=entity["id"],
            workspace_path=test_workspace,
        )

        # Invalid status should return empty results
        tasks: list[dict[str, Any]] = get_entity_tasks(
            entity_id=entity["id"],
            workspace_path=test_workspace,
            status="invalid_status",
        )

        assert len(tasks) == 0

    def test_get_entity_tasks_invalid_priority_filter(self, test_workspace: str) -> None:
        """Test invalid priority filter in get_entity_tasks."""
        entity = create_entity(
            entity_type="file",
            name="test.py",
            workspace_path=test_workspace,
        )

        # Invalid priority should return empty results
        tasks: list[dict[str, Any]] = get_entity_tasks(
            entity_id=entity["id"],
            workspace_path=test_workspace,
            priority="ultra_high",  # Invalid
        )

        assert len(tasks) == 0


class TestNotFoundErrors:
    """Test error handling for not found resources."""

    def test_get_task_not_found(self, test_workspace: str) -> None:
        """Test get_task with non-existent task ID."""
        with pytest.raises(ValueError) as exc_info:
            get_task(
                task_id=99999,  # Non-existent
                workspace_path=test_workspace,
            )

        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower() or "deleted" in error_msg.lower()

    def test_get_entity_not_found(self, test_workspace: str) -> None:
        """Test get_entity with non-existent entity ID."""
        with pytest.raises(ValueError) as exc_info:
            get_entity(
                entity_id=99999,  # Non-existent
                workspace_path=test_workspace,
            )

        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower() or "deleted" in error_msg.lower()

    def test_get_task_entities_task_not_found(self, test_workspace: str) -> None:
        """Test get_task_entities with non-existent task."""
        with pytest.raises(ValueError) as exc_info:
            get_task_entities(
                task_id=99999,  # Non-existent
                workspace_path=test_workspace,
            )

        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower() or "deleted" in error_msg.lower()

    def test_get_entity_tasks_entity_not_found(self, test_workspace: str) -> None:
        """Test get_entity_tasks with non-existent entity."""
        with pytest.raises(ValueError) as exc_info:
            get_entity_tasks(
                entity_id=99999,  # Non-existent
                workspace_path=test_workspace,
            )

        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower() or "deleted" in error_msg.lower()

    def test_update_task_not_found(self, test_workspace: str) -> None:
        """Test update_task with non-existent task."""
        with pytest.raises(ValueError) as exc_info:
            update_task(
                task_id=99999,
                workspace_path=test_workspace,
                title="Updated Title",
            )

        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower() or "deleted" in error_msg.lower()


class TestMissingRequiredParameters:
    """Test error handling for missing required parameters."""

    def test_list_tasks_missing_workspace_path(self) -> None:
        """Test that workspace_path is required."""
        with pytest.raises((TypeError, ValueError)):
            list_tasks(  # type: ignore[call-arg]
                # Missing workspace_path
            )

    def test_create_task_missing_workspace_path(self) -> None:
        """Test that workspace_path is required for create_task."""
        with pytest.raises((TypeError, ValueError)):
            create_task(  # type: ignore[call-arg]
                title="Test Task",
                # Missing workspace_path
            )

    def test_get_task_missing_workspace_path(self) -> None:
        """Test that workspace_path is required for get_task."""
        with pytest.raises((TypeError, ValueError)):
            get_task(  # type: ignore[call-arg]
                task_id=1,
                # Missing workspace_path
            )

    def test_create_entity_missing_workspace_path(self) -> None:
        """Test that workspace_path is required for create_entity."""
        with pytest.raises((TypeError, ValueError)):
            create_entity(  # type: ignore[call-arg]
                entity_type="file",
                name="test.py",
                # Missing workspace_path
            )


class TestValidModeValues:
    """Test that valid mode values work correctly."""

    def test_list_tasks_summary_mode_valid(self, test_workspace: str) -> None:
        """Test that 'summary' mode is valid."""
        create_task(
            title="Task",
            workspace_path=test_workspace,
            description="Large description",
        )

        # Should not raise error
        tasks: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            mode="summary",
        )

        assert len(tasks) == 1

    def test_list_tasks_details_mode_valid(self, test_workspace: str) -> None:
        """Test that 'details' mode is valid."""
        create_task(
            title="Task",
            workspace_path=test_workspace,
            description="Large description",
        )

        # Should not raise error
        tasks: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            mode="details",
        )

        assert len(tasks) == 1
        assert "description" in tasks[0]

    def test_search_tasks_valid_modes(self, test_workspace: str) -> None:
        """Test valid modes for search_tasks."""
        create_task(
            title="Searchable task",
            workspace_path=test_workspace,
        )

        # Summary mode should work
        tasks_summary: list[dict[str, Any]] = search_tasks(
            search_term="Searchable",
            workspace_path=test_workspace,
            mode="summary",
        )
        assert len(tasks_summary) == 1

        # Details mode should work
        tasks_details: list[dict[str, Any]] = search_tasks(
            search_term="Searchable",
            workspace_path=test_workspace,
            mode="details",
        )
        assert len(tasks_details) == 1

    def test_list_entities_valid_modes(self, test_workspace: str) -> None:
        """Test valid modes for list_entities."""
        create_entity(
            entity_type="file",
            name="test.py",
            workspace_path=test_workspace,
        )

        # Summary mode
        entities_summary: list[dict[str, Any]] = list_entities(
            workspace_path=test_workspace,
            mode="summary",
        )
        assert len(entities_summary) == 1

        # Details mode
        entities_details: list[dict[str, Any]] = list_entities(
            workspace_path=test_workspace,
            mode="details",
        )
        assert len(entities_details) == 1


class TestErrorResponseFormats:
    """Test that errors return proper format."""

    def test_invalid_mode_error_is_value_error(self, test_workspace: str) -> None:
        """Test that invalid mode raises ValueError."""
        create_task(
            title="Task",
            workspace_path=test_workspace,
        )

        # Should raise ValueError (standard Python error)
        with pytest.raises(ValueError):
            list_tasks(
                workspace_path=test_workspace,
                mode="invalid",
            )

    def test_not_found_error_is_value_error(self, test_workspace: str) -> None:
        """Test that not found errors raise ValueError."""
        with pytest.raises(ValueError):
            get_task(
                task_id=99999,
                workspace_path=test_workspace,
            )

    def test_error_message_clarity(self, test_workspace: str) -> None:
        """Test that error messages are clear and helpful."""
        with pytest.raises(ValueError) as exc_info:
            list_tasks(
                workspace_path=test_workspace,
                mode="bad_mode",
            )

        # Error message should mention valid options
        error_msg = str(exc_info.value).lower()
        assert "mode" in error_msg
        assert ("summary" in error_msg or "details" in error_msg or "must be" in error_msg)

    def test_not_found_error_mentions_id(self, test_workspace: str) -> None:
        """Test that not found error mentions the ID."""
        with pytest.raises(ValueError) as exc_info:
            get_task(
                task_id=12345,
                workspace_path=test_workspace,
            )

        error_msg = str(exc_info.value)
        assert "12345" in error_msg or "not found" in error_msg.lower()


class TestPaginationErrors:
    """Test error handling for pagination parameters."""

    def test_pagination_zero_limit_error(self, test_workspace: str) -> None:
        """Test that limit=0 raises error."""
        create_task(
            title="Task",
            workspace_path=test_workspace,
        )

        with pytest.raises((ValueError, AssertionError)):
            list_tasks(
                workspace_path=test_workspace,
                limit=0,
            )

    def test_pagination_negative_limit_error(self, test_workspace: str) -> None:
        """Test that negative limit raises error."""
        create_task(
            title="Task",
            workspace_path=test_workspace,
        )

        with pytest.raises((ValueError, AssertionError)):
            list_tasks(
                workspace_path=test_workspace,
                limit=-5,
            )

    def test_pagination_negative_offset_error(self, test_workspace: str) -> None:
        """Test that negative offset raises error."""
        create_task(
            title="Task",
            workspace_path=test_workspace,
        )

        with pytest.raises((ValueError, AssertionError)):
            list_tasks(
                workspace_path=test_workspace,
                offset=-1,
            )

    def test_pagination_max_limit_validation(self, test_workspace: str) -> None:
        """Test that excessively large limit may be validated."""
        # Create some tasks
        for i in range(5):
            create_task(
                title=f"Task {i}",
                workspace_path=test_workspace,
            )

        # Very large limit should still work (returns actual count)
        tasks: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            limit=1000000,
        )

        assert len(tasks) == 5


class TestCreateTaskValidation:
    """Test validation in create_task."""

    def test_create_task_description_too_long(self, test_workspace: str) -> None:
        """Test that description exceeding 10k chars is rejected."""
        long_description = "a" * 10001  # Exceeds limit

        with pytest.raises(ValueError) as exc_info:
            create_task(
                title="Task",
                workspace_path=test_workspace,
                description=long_description,
            )

        error_msg = str(exc_info.value)
        assert "10" in error_msg or "character" in error_msg.lower()

    def test_create_task_max_description_allowed(self, test_workspace: str) -> None:
        """Test that description at 10k char limit is accepted."""
        max_description = "a" * 10000  # At limit

        task: dict[str, Any] = create_task(
            title="Task",
            workspace_path=test_workspace,
            description=max_description,
        )

        assert task["description"] == max_description

    def test_create_entity_description_too_long(self, test_workspace: str) -> None:
        """Test that entity description exceeding 10k chars is rejected."""
        long_description = "x" * 10001

        with pytest.raises(ValueError):
            create_entity(
                entity_type="file",
                name="test.py",
                workspace_path=test_workspace,
                description=long_description,
            )

    def test_create_entity_max_description_allowed(self, test_workspace: str) -> None:
        """Test that entity description at 10k limit is accepted."""
        max_description = "x" * 10000

        entity: dict[str, Any] = create_entity(
            entity_type="file",
            name="test.py",
            workspace_path=test_workspace,
            description=max_description,
        )

        assert entity["description"] == max_description


class TestUpdateTaskValidation:
    """Test validation in update_task."""

    def test_update_task_description_too_long(self, test_workspace: str) -> None:
        """Test that updating with long description is rejected."""
        task = create_task(
            title="Task",
            workspace_path=test_workspace,
        )

        long_description = "b" * 10001

        with pytest.raises(ValueError):
            update_task(
                task_id=task["id"],
                workspace_path=test_workspace,
                description=long_description,
            )

    def test_update_task_description_max_allowed(self, test_workspace: str) -> None:
        """Test that updating with max description is allowed."""
        task = create_task(
            title="Task",
            workspace_path=test_workspace,
        )

        max_description = "b" * 10000

        updated: dict[str, Any] = update_task(
            task_id=task["id"],
            workspace_path=test_workspace,
            description=max_description,
        )

        assert updated["description"] == max_description
