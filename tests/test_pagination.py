"""Comprehensive pagination tests for Task MCP listing and search tools."""

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
create_entity = server.create_entity.fn
list_entities = server.list_entities.fn
search_entities = server.search_entities.fn
get_task_entities = server.get_task_entities.fn
get_entity_tasks = server.get_entity_tasks.fn
link_entity_to_task = server.link_entity_to_task.fn


@pytest.fixture
def test_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[str, None, None]:
    """Create isolated test workspace."""
    workspace = str(tmp_path / "test-project")
    Path(workspace).mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    yield workspace


class TestListTasksPagination:
    """Test pagination in list_tasks tool."""

    def test_list_tasks_pagination_default(self, test_workspace: str) -> None:
        """Test default pagination with limit=100, offset=0."""
        # Create 5 test tasks
        for i in range(5):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
                description=f"Description for task {i + 1}",
            )

        # List with default pagination (should work without explicit params)
        response = list_tasks(workspace_path=test_workspace)

        assert isinstance(response, dict)
        assert len(response["items"]) == 5
        assert response["items"][0]["title"] == "Task 5"  # Most recent first (DESC)

    def test_list_tasks_pagination_custom_limit(self, test_workspace: str) -> None:
        """Test custom limit parameter."""
        # Create 10 test tasks
        for i in range(10):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # List with custom limit of 5
        response = list_tasks(
            workspace_path=test_workspace,
            limit=5,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 5
        # Should get most recent 5 tasks (tasks 10, 9, 8, 7, 6)
        assert response["items"][0]["title"] == "Task 10"
        assert response["items"][4]["title"] == "Task 6"

    def test_list_tasks_pagination_custom_offset(self, test_workspace: str) -> None:
        """Test custom offset parameter."""
        # Create 10 test tasks
        for i in range(10):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # List with offset of 5 (skip first 5, get next 5)
        response = list_tasks(
            workspace_path=test_workspace,
            limit=10,
            offset=5,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 5
        # Should get tasks 5, 4, 3, 2, 1
        assert response["items"][0]["title"] == "Task 5"
        assert response["items"][4]["title"] == "Task 1"

    def test_list_tasks_pagination_limit_and_offset(self, test_workspace: str) -> None:
        """Test combined limit and offset."""
        # Create 15 test tasks
        for i in range(15):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # Get tasks 6-10 (offset=5, limit=5)
        response = list_tasks(
            workspace_path=test_workspace,
            limit=5,
            offset=5,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 5
        assert response["items"][0]["title"] == "Task 10"
        assert response["items"][4]["title"] == "Task 6"

    def test_list_tasks_pagination_boundary_offset_exceeds_total(
        self, test_workspace: str
    ) -> None:
        """Test offset greater than total count."""
        # Create 5 test tasks
        for i in range(5):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # Request with offset >= total_count
        response = list_tasks(
            workspace_path=test_workspace,
            limit=10,
            offset=10,  # Greater than total (5)
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 0

    def test_list_tasks_pagination_boundary_limit_exceeds_remaining(
        self, test_workspace: str
    ) -> None:
        """Test limit greater than remaining items."""
        # Create 7 test tasks
        for i in range(7):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # Request offset=5, limit=10 (only 2 items remain)
        response = list_tasks(
            workspace_path=test_workspace,
            limit=10,
            offset=5,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 2
        assert response["items"][0]["title"] == "Task 2"
        assert response["items"][1]["title"] == "Task 1"

    def test_list_tasks_pagination_with_filters(self, test_workspace: str) -> None:
        """Test pagination with status filter."""
        # Create tasks with different statuses
        for i in range(10):
            status = "done" if i < 5 else "todo"
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
                status=status,
            )

        # Get first 3 'todo' tasks
        response = list_tasks(
            workspace_path=test_workspace,
            status="todo",
            limit=3,
            offset=0,
        )

        # Should only get 'todo' tasks
        assert isinstance(response, dict)
        assert all(t["status"] == "todo" for t in response["items"])
        assert len(response["items"]) == 3

    def test_list_tasks_pagination_with_priority_filter(self, test_workspace: str) -> None:
        """Test pagination with priority filter."""
        # Create tasks with different priorities
        priorities = ["low", "medium", "high"]
        for i in range(9):
            priority = priorities[i % 3]
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
                priority=priority,
            )

        # Get 'high' priority tasks with pagination
        response = list_tasks(
            workspace_path=test_workspace,
            priority="high",
            limit=10,
        )

        # Should only get high priority tasks (3 total)
        assert isinstance(response, dict)
        assert len(response["items"]) == 3
        assert all(t["priority"] == "high" for t in response["items"])

    def test_list_tasks_pagination_metadata_structure(self, test_workspace: str) -> None:
        """Test pagination response includes metadata."""
        # Create 10 test tasks
        for i in range(10):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # Test that list_tasks returns dict with pagination metadata
        response = list_tasks(
            workspace_path=test_workspace,
            limit=5,
            offset=0,
        )

        assert isinstance(response, dict)
        assert "total_count" in response
        assert "returned_count" in response
        assert "limit" in response
        assert "offset" in response
        assert "items" in response
        assert len(response["items"]) == 5

    def test_list_tasks_pagination_zero_limit_error(self, test_workspace: str) -> None:
        """Test that limit <= 0 returns error response."""
        response = list_tasks(
            workspace_path=test_workspace,
            limit=0,  # Invalid
        )

        # Should return error response
        assert isinstance(response, dict)
        assert "error" in response
        assert response["error"]["code"] == "PAGINATION_INVALID"

    def test_list_tasks_pagination_negative_offset_error(self, test_workspace: str) -> None:
        """Test that negative offset returns error response."""
        response = list_tasks(
            workspace_path=test_workspace,
            offset=-1,  # Invalid
        )

        # Should return error response
        assert isinstance(response, dict)
        assert "error" in response
        assert response["error"]["code"] == "PAGINATION_INVALID"


class TestSearchTasksPagination:
    """Test pagination in search_tasks tool."""

    def test_search_tasks_pagination_basic(self, test_workspace: str) -> None:
        """Test search with pagination."""
        # Create 10 tasks with searchable title
        for i in range(10):
            create_task(
                title=f"Authentication task {i + 1}",
                workspace_path=test_workspace,
                description=f"Implement auth feature {i + 1}",
            )

        # Search with pagination
        response = search_tasks(
            search_term="Authentication",
            workspace_path=test_workspace,
            limit=5,
            offset=0,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 5
        assert all("Authentication" in t["title"] for t in response["items"])

    def test_search_tasks_pagination_offset(self, test_workspace: str) -> None:
        """Test search with offset."""
        # Create 10 tasks
        for i in range(10):
            create_task(
                title=f"Feature {i + 1}",
                workspace_path=test_workspace,
                description=f"Implement feature {i + 1}",
            )

        # Get second page (offset=5, limit=5)
        response = search_tasks(
            search_term="Feature",
            workspace_path=test_workspace,
            limit=5,
            offset=5,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 5


class TestListEntitiesPagination:
    """Test pagination in list_entities tool."""

    def test_list_entities_pagination_basic(self, test_workspace: str) -> None:
        """Test basic entity listing with pagination."""
        # Create 8 file entities
        for i in range(8):
            create_entity(
                entity_type="file",
                name=f"file_{i + 1}.py",
                workspace_path=test_workspace,
                identifier=f"/src/module_{i + 1}.py",
            )

        # List with pagination
        response = list_entities(
            workspace_path=test_workspace,
            limit=4,
            offset=0,
        )

        assert isinstance(response, dict)
        assert "items" in response
        assert response["total_count"] == 8
        assert response["returned_count"] == 4
        assert response["limit"] == 4
        assert response["offset"] == 0
        assert len(response["items"]) == 4

    def test_list_entities_pagination_with_type_filter(self, test_workspace: str) -> None:
        """Test entity pagination with type filter."""
        # Create 5 file entities and 5 'other' entities
        for i in range(5):
            create_entity(
                entity_type="file",
                name=f"file_{i + 1}.py",
                workspace_path=test_workspace,
            )
            create_entity(
                entity_type="other",
                name=f"vendor_{i + 1}",
                workspace_path=test_workspace,
            )

        # Get 'file' entities with pagination
        response = list_entities(
            workspace_path=test_workspace,
            entity_type="file",
            limit=3,
            offset=0,
        )

        assert isinstance(response, dict)
        assert response["total_count"] == 5
        assert response["returned_count"] == 3
        assert response["limit"] == 3
        assert len(response["items"]) == 3
        assert all(e["entity_type"] == "file" for e in response["items"])

    def test_list_entities_pagination_offset(self, test_workspace: str) -> None:
        """Test entity pagination with offset."""
        # Create 10 entities
        for i in range(10):
            create_entity(
                entity_type="file",
                name=f"file_{i + 1}.py",
                workspace_path=test_workspace,
            )

        # Get items 5-7
        response = list_entities(
            workspace_path=test_workspace,
            limit=3,
            offset=5,
        )

        assert isinstance(response, dict)
        assert response["total_count"] == 10
        assert response["returned_count"] == 3
        assert response["limit"] == 3
        assert response["offset"] == 5
        assert len(response["items"]) == 3


class TestGetEntityTasksPagination:
    """Test pagination in get_entity_tasks tool."""

    def test_get_entity_tasks_pagination_basic(self, test_workspace: str) -> None:
        """Test getting entity tasks with pagination."""
        # Create a vendor entity
        vendor = create_entity(
            entity_type="other",
            name="Vendor ABC",
            workspace_path=test_workspace,
            identifier="ABC-INS",
        )

        # Create 10 tasks and link them to vendor
        for i in range(10):
            task = create_task(
                title=f"Vendor task {i + 1}",
                workspace_path=test_workspace,
            )
            link_entity_to_task(
                task_id=task["id"],
                entity_id=vendor["id"],
                workspace_path=test_workspace,
            )

        # Get tasks for entity with pagination
        response = get_entity_tasks(
            entity_id=vendor["id"],
            workspace_path=test_workspace,
            limit=5,
            offset=0,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 5

    def test_get_entity_tasks_pagination_with_filter(self, test_workspace: str) -> None:
        """Test get_entity_tasks pagination with status filter."""
        # Create entity
        vendor = create_entity(
            entity_type="other",
            name="Vendor ABC",
            workspace_path=test_workspace,
        )

        # Create tasks with mixed statuses
        for i in range(10):
            status = "done" if i < 5 else "in_progress"
            task = create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
                status=status,
            )
            link_entity_to_task(
                task_id=task["id"],
                entity_id=vendor["id"],
                workspace_path=test_workspace,
            )

        # Get in_progress tasks with pagination
        response = get_entity_tasks(
            entity_id=vendor["id"],
            workspace_path=test_workspace,
            status="in_progress",
            limit=10,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 5
        assert all(t["status"] == "in_progress" for t in response["items"])

    def test_get_entity_tasks_pagination_offset(self, test_workspace: str) -> None:
        """Test get_entity_tasks pagination with offset."""
        # Create entity and tasks
        vendor = create_entity(
            entity_type="other",
            name="Vendor",
            workspace_path=test_workspace,
        )

        for i in range(8):
            task = create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )
            link_entity_to_task(
                task_id=task["id"],
                entity_id=vendor["id"],
                workspace_path=test_workspace,
            )

        # Get second page
        response = get_entity_tasks(
            entity_id=vendor["id"],
            workspace_path=test_workspace,
            limit=3,
            offset=3,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 3


class TestPaginationModeInteraction:
    """Test pagination interaction with summary/details modes."""

    def test_list_tasks_pagination_with_summary_mode(self, test_workspace: str) -> None:
        """Test pagination works with summary mode."""
        # Create tasks
        for i in range(10):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
                description="Large description " * 100,  # Make it large
            )

        # Get with pagination and summary mode
        response = list_tasks(
            workspace_path=test_workspace,
            limit=5,
            offset=0,
            mode="summary",
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 5
        # Summary mode should exclude description
        assert "description" not in response["items"][0]

    def test_list_tasks_pagination_with_details_mode(self, test_workspace: str) -> None:
        """Test pagination works with details mode."""
        # Create tasks
        for i in range(10):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
                description=f"Description {i}",
            )

        # Get with pagination and details mode
        response = list_tasks(
            workspace_path=test_workspace,
            limit=5,
            offset=0,
            mode="details",
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 5
        # Details mode should include description
        assert "description" in response["items"][0]
        assert response["items"][0]["description"] == "Description 9"

    def test_list_entities_pagination_with_summary_mode(self, test_workspace: str) -> None:
        """Test entity pagination works with summary mode."""
        # Create entities
        for i in range(10):
            create_entity(
                entity_type="file",
                name=f"file_{i}.py",
                workspace_path=test_workspace,
                description="Large description " * 50,
            )

        # Get with pagination and summary mode
        response = list_entities(
            workspace_path=test_workspace,
            limit=5,
            mode="summary",
        )

        assert isinstance(response, dict)
        assert response["total_count"] == 10
        assert response["returned_count"] == 5
        assert len(response["items"]) == 5
        # Summary mode should exclude description
        assert "description" not in response["items"][0]


class TestPaginationEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_pagination_empty_results(self, test_workspace: str) -> None:
        """Test pagination when no results match."""
        # Create a task with 'done' status
        create_task(
            title="Task 1",
            workspace_path=test_workspace,
            status="done",
        )

        # Search for 'todo' status (should be empty)
        response = list_tasks(
            workspace_path=test_workspace,
            status="todo",
            limit=10,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 0

    def test_pagination_single_item(self, test_workspace: str) -> None:
        """Test pagination with single item."""
        create_task(
            title="Task 1",
            workspace_path=test_workspace,
        )

        response = list_tasks(
            workspace_path=test_workspace,
            limit=10,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 1

    def test_pagination_exact_limit(self, test_workspace: str) -> None:
        """Test when result count equals limit."""
        # Create exactly 5 tasks
        for i in range(5):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # Request with exact limit
        response = list_tasks(
            workspace_path=test_workspace,
            limit=5,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 5

    def test_search_pagination_no_matches(self, test_workspace: str) -> None:
        """Test search pagination with no matches."""
        create_task(
            title="Authentication task",
            workspace_path=test_workspace,
        )

        # Search for non-existent term
        response = search_tasks(
            search_term="NonExistent",
            workspace_path=test_workspace,
            limit=10,
        )

        assert isinstance(response, dict)
        assert len(response["items"]) == 0

    def test_pagination_max_limit(self, test_workspace: str) -> None:
        """Test pagination with limit exceeding max (1000)."""
        # Create 50 tasks
        for i in range(50):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # Request with limit exceeding max (1000)
        response = list_tasks(
            workspace_path=test_workspace,
            limit=10000,  # Exceeds max limit of 1000
        )

        # Should return error response
        assert isinstance(response, dict)
        assert "error" in response
        assert response["error"]["code"] == "PAGINATION_INVALID"
