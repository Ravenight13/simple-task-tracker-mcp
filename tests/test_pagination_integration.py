"""Integration tests for pagination with real-world scenarios."""

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
get_entity_tasks = server.get_entity_tasks.fn
link_entity_to_task = server.link_entity_to_task.fn


@pytest.fixture
def test_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[str, None, None]:
    """Create isolated test workspace."""
    workspace = str(tmp_path / "test-project")
    Path(workspace).mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    yield workspace


class TestPaginationWithFilters:
    """Test pagination works correctly with various filters."""

    def test_pagination_with_status_filter(self, test_workspace: str) -> None:
        """Test pagination respects status filter."""
        # Create 15 tasks: 5 todo, 5 in_progress, 5 done
        for i in range(5):
            create_task(
                title=f"Todo task {i + 1}",
                workspace_path=test_workspace,
                status="todo",
            )
            create_task(
                title=f"In progress task {i + 1}",
                workspace_path=test_workspace,
                status="in_progress",
            )
            create_task(
                title=f"Done task {i + 1}",
                workspace_path=test_workspace,
                status="done",
            )

        # Get first page of 'in_progress' tasks
        page1: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            status="in_progress",
            limit=3,
            offset=0,
        )

        # All results should be in_progress
        assert all(t["status"] == "in_progress" for t in page1)
        assert len(page1) == 3

        # Get second page
        page2: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            status="in_progress",
            limit=3,
            offset=3,
        )

        assert all(t["status"] == "in_progress" for t in page2)
        assert len(page2) == 2  # Only 2 remaining

    def test_pagination_with_priority_filter(self, test_workspace: str) -> None:
        """Test pagination respects priority filter."""
        # Create 12 tasks: 4 of each priority
        for i in range(4):
            create_task(
                title=f"Low priority {i + 1}",
                workspace_path=test_workspace,
                priority="low",
            )
            create_task(
                title=f"Medium priority {i + 1}",
                workspace_path=test_workspace,
                priority="medium",
            )
            create_task(
                title=f"High priority {i + 1}",
                workspace_path=test_workspace,
                priority="high",
            )

        # Get 'high' priority tasks with pagination
        high_tasks: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            priority="high",
            limit=2,
            offset=0,
        )

        assert len(high_tasks) == 2
        assert all(t["priority"] == "high" for t in high_tasks)

    def test_pagination_with_multiple_filters(self, test_workspace: str) -> None:
        """Test pagination with both status and priority filters."""
        # Create tasks with combinations of status and priority
        for priority in ["low", "medium", "high"]:
            for i in range(3):
                create_task(
                    title=f"Task {priority} {i}",
                    workspace_path=test_workspace,
                    status="in_progress",
                    priority=priority,
                )

        # Get high priority in_progress tasks
        tasks: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            status="in_progress",
            priority="high",
            limit=2,
        )

        assert len(tasks) == 2
        assert all(t["status"] == "in_progress" for t in tasks)
        assert all(t["priority"] == "high" for t in tasks)

    def test_pagination_with_tag_filter(self, test_workspace: str) -> None:
        """Test pagination works with tag filter."""
        # Create tasks with different tags
        for i in range(8):
            tags = "backend api" if i % 2 == 0 else "frontend ui"
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
                tags=tags,
            )

        # Get 'backend' tasks with pagination
        backend_tasks: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            tags="backend",
            limit=2,
            offset=0,
        )

        assert len(backend_tasks) == 2
        assert all("backend" in t["tags"] for t in backend_tasks)


class TestSearchPaginationWithMode:
    """Test search with pagination and summary/details modes."""

    def test_search_pagination_with_summary_mode(self, test_workspace: str) -> None:
        """Test search pagination works with summary mode."""
        # Create 12 searchable tasks
        for i in range(12):
            create_task(
                title=f"Feature {i + 1}: Enhanced user experience",
                workspace_path=test_workspace,
                description="Large description " * 100,
            )

        # Search with pagination and summary mode
        page1: list[dict[str, Any]] = search_tasks(
            search_term="Feature",
            workspace_path=test_workspace,
            limit=5,
            offset=0,
            mode="summary",
        )

        assert len(page1) == 5
        # Summary should exclude description
        assert "description" not in page1[0]

        # Get second page
        page2: list[dict[str, Any]] = search_tasks(
            search_term="Feature",
            workspace_path=test_workspace,
            limit=5,
            offset=5,
            mode="summary",
        )

        assert len(page2) == 5
        assert page1[0]["id"] != page2[0]["id"]  # Different pages

    def test_search_pagination_with_details_mode(self, test_workspace: str) -> None:
        """Test search pagination works with details mode."""
        # Create searchable tasks
        for i in range(8):
            create_task(
                title=f"Auth task {i + 1}",
                workspace_path=test_workspace,
                description=f"Details about authentication task {i}",
            )

        # Search with details mode
        tasks: list[dict[str, Any]] = search_tasks(
            search_term="Auth",
            workspace_path=test_workspace,
            limit=4,
            mode="details",
        )

        assert len(tasks) == 4
        # Details should include description
        assert "description" in tasks[0]
        assert tasks[0]["description"]


class TestEntityPaginationWithMode:
    """Test entity pagination with summary/details modes."""

    def test_entity_pagination_list_summary_mode(self, test_workspace: str) -> None:
        """Test entity listing pagination with summary mode."""
        # Create 10 entities
        for i in range(10):
            create_entity(
                entity_type="file",
                name=f"module_{i + 1}.py",
                workspace_path=test_workspace,
                identifier=f"/src/module_{i + 1}.py",
                description=f"Large description content " * 50,
                metadata={"version": "1.0", "status": "active"},
            )

        # Get first page in summary mode
        page1: list[dict[str, Any]] = list_entities(
            workspace_path=test_workspace,
            limit=4,
            offset=0,
            mode="summary",
        )

        assert len(page1) == 4
        # Summary should exclude description
        assert "description" not in page1[0]
        # Summary should exclude metadata
        assert "metadata" not in page1[0]

        # Get second page
        page2: list[dict[str, Any]] = list_entities(
            workspace_path=test_workspace,
            limit=4,
            offset=4,
            mode="summary",
        )

        assert len(page2) == 4
        # Pages should be different
        assert page1[0]["id"] != page2[0]["id"]

    def test_entity_pagination_list_details_mode(self, test_workspace: str) -> None:
        """Test entity listing pagination with details mode."""
        # Create 6 entities
        for i in range(6):
            create_entity(
                entity_type="other",
                name=f"vendor_{i + 1}",
                workspace_path=test_workspace,
                description=f"Vendor details {i}",
                metadata={"code": f"VENDOR-{i}"},
            )

        # Get all in details mode
        entities: list[dict[str, Any]] = list_entities(
            workspace_path=test_workspace,
            limit=3,
            mode="details",
        )

        assert len(entities) == 3
        # Details should include description and metadata
        assert "description" in entities[0]
        assert "metadata" in entities[0]


class TestPaginationCursorWalk:
    """Test walking through all results using pagination cursor pattern."""

    def test_cursor_walk_through_all_tasks(self, test_workspace: str) -> None:
        """Test walking through all tasks using limit/offset."""
        # Create 27 tasks
        for i in range(27):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # Walk through with cursor (limit=10)
        all_tasks: list[dict[str, Any]] = []
        offset = 0
        limit = 10

        while True:
            page: list[dict[str, Any]] = list_tasks(
                workspace_path=test_workspace,
                limit=limit,
                offset=offset,
            )

            if not page:
                break

            all_tasks.extend(page)
            offset += len(page)

            # Safety check (shouldn't infinite loop)
            if len(all_tasks) > 100:
                break

        assert len(all_tasks) == 27

    def test_cursor_walk_with_filter(self, test_workspace: str) -> None:
        """Test cursor walking with status filter."""
        # Create 18 tasks: 9 todo, 9 done
        for i in range(9):
            create_task(
                title=f"Todo {i + 1}",
                workspace_path=test_workspace,
                status="todo",
            )
            create_task(
                title=f"Done {i + 1}",
                workspace_path=test_workspace,
                status="done",
            )

        # Walk through all 'todo' tasks
        todo_tasks: list[dict[str, Any]] = []
        offset = 0
        limit = 3

        while True:
            page: list[dict[str, Any]] = list_tasks(
                workspace_path=test_workspace,
                status="todo",
                limit=limit,
                offset=offset,
            )

            if not page:
                break

            todo_tasks.extend(page)
            offset += len(page)

            if len(todo_tasks) > 100:
                break

        assert len(todo_tasks) == 9
        assert all(t["status"] == "todo" for t in todo_tasks)

    def test_cursor_walk_search_results(self, test_workspace: str) -> None:
        """Test cursor walking through search results."""
        # Create 20 searchable tasks
        for i in range(20):
            create_task(
                title=f"Migration task {i + 1}",
                workspace_path=test_workspace,
            )

        # Walk through search results
        results: list[dict[str, Any]] = []
        offset = 0
        limit = 4

        while True:
            page: list[dict[str, Any]] = search_tasks(
                search_term="Migration",
                workspace_path=test_workspace,
                limit=limit,
                offset=offset,
            )

            if not page:
                break

            results.extend(page)
            offset += len(page)

        assert len(results) == 20


class TestLargeDatasetPagination:
    """Test pagination performance and correctness with large datasets."""

    def test_large_dataset_pagination(self, test_workspace: str) -> None:
        """Test pagination with 100+ items."""
        # Create 150 tasks
        for i in range(150):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # Get all tasks in chunks
        all_tasks: list[dict[str, Any]] = []
        offset = 0

        while True:
            page: list[dict[str, Any]] = list_tasks(
                workspace_path=test_workspace,
                limit=50,
                offset=offset,
            )

            if not page:
                break

            all_tasks.extend(page)
            offset += 50

        assert len(all_tasks) == 150

    def test_large_dataset_with_filter(self, test_workspace: str) -> None:
        """Test pagination with large dataset and filter."""
        # Create 200 tasks: 100 high, 100 medium priority
        for i in range(100):
            create_task(
                title=f"High task {i + 1}",
                workspace_path=test_workspace,
                priority="high",
            )
            create_task(
                title=f"Medium task {i + 1}",
                workspace_path=test_workspace,
                priority="medium",
            )

        # Get all high priority tasks
        high_tasks: list[dict[str, Any]] = []
        offset = 0

        while True:
            page: list[dict[str, Any]] = list_tasks(
                workspace_path=test_workspace,
                priority="high",
                limit=25,
                offset=offset,
            )

            if not page:
                break

            high_tasks.extend(page)
            offset += 25

        assert len(high_tasks) == 100
        assert all(t["priority"] == "high" for t in high_tasks)

    def test_large_entity_dataset_pagination(self, test_workspace: str) -> None:
        """Test entity pagination with large dataset."""
        # Create 120 entities
        for i in range(120):
            create_entity(
                entity_type="file" if i % 2 == 0 else "other",
                name=f"entity_{i + 1}",
                workspace_path=test_workspace,
            )

        # Paginate through all entities
        all_entities: list[dict[str, Any]] = []
        offset = 0

        while True:
            page: list[dict[str, Any]] = list_entities(
                workspace_path=test_workspace,
                limit=30,
                offset=offset,
            )

            if not page:
                break

            all_entities.extend(page)
            offset += 30

        assert len(all_entities) == 120


class TestGetEntityTasksPaginationIntegration:
    """Test get_entity_tasks pagination in real-world scenarios."""

    def test_vendor_task_pagination(self, test_workspace: str) -> None:
        """Test pagination of tasks linked to a vendor entity."""
        # Create a vendor entity
        vendor = create_entity(
            entity_type="other",
            name="Vendor ABC",
            workspace_path=test_workspace,
            identifier="ABC-VENDOR",
        )

        # Create 25 tasks linked to vendor
        for i in range(25):
            task = create_task(
                title=f"Vendor ABC task {i + 1}",
                workspace_path=test_workspace,
                priority="high" if i < 10 else "medium",
            )
            link_entity_to_task(
                task_id=task["id"],
                entity_id=vendor["id"],
                workspace_path=test_workspace,
            )

        # Get high priority tasks for vendor
        high_priority: list[dict[str, Any]] = []
        offset = 0

        while True:
            page: list[dict[str, Any]] = get_entity_tasks(
                entity_id=vendor["id"],
                workspace_path=test_workspace,
                priority="high",
                limit=5,
                offset=offset,
            )

            if not page:
                break

            high_priority.extend(page)
            offset += 5

        assert len(high_priority) == 10
        assert all(t["priority"] == "high" for t in high_priority)

    def test_file_entity_task_pagination(self, test_workspace: str) -> None:
        """Test pagination of tasks linked to a file entity."""
        # Create a file entity
        file_entity = create_entity(
            entity_type="file",
            name="auth.py",
            workspace_path=test_workspace,
            identifier="/src/auth.py",
        )

        # Create 15 tasks linked to file
        for i in range(15):
            task = create_task(
                title=f"Auth file task {i + 1}",
                workspace_path=test_workspace,
            )
            link_entity_to_task(
                task_id=task["id"],
                entity_id=file_entity["id"],
                workspace_path=test_workspace,
            )

        # Get tasks in pages
        all_tasks: list[dict[str, Any]] = []
        offset = 0

        while True:
            page: list[dict[str, Any]] = get_entity_tasks(
                entity_id=file_entity["id"],
                workspace_path=test_workspace,
                limit=4,
                offset=offset,
            )

            if not page:
                break

            all_tasks.extend(page)
            offset += 4

        assert len(all_tasks) == 15


class TestPaginationDataConsistency:
    """Test that pagination returns consistent data across requests."""

    def test_same_page_returns_same_data(self, test_workspace: str) -> None:
        """Test that requesting same page twice returns same data."""
        # Create 10 tasks
        for i in range(10):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # Get first page twice
        page1_first: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            limit=5,
            offset=0,
        )

        page1_second: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            limit=5,
            offset=0,
        )

        # Should have same IDs
        assert [t["id"] for t in page1_first] == [t["id"] for t in page1_second]

    def test_non_overlapping_pages(self, test_workspace: str) -> None:
        """Test that pages don't overlap."""
        # Create 20 tasks
        for i in range(20):
            create_task(
                title=f"Task {i + 1}",
                workspace_path=test_workspace,
            )

        # Get pages
        page1: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            limit=5,
            offset=0,
        )

        page2: list[dict[str, Any]] = list_tasks(
            workspace_path=test_workspace,
            limit=5,
            offset=5,
        )

        # Pages should not overlap
        page1_ids = {t["id"] for t in page1}
        page2_ids = {t["id"] for t in page2}

        assert not page1_ids.intersection(page2_ids)
