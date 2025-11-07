"""Tests for summary/details mode feature in listing tools."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

# Import MCP tool wrappers and extract underlying functions
from task_mcp import server

# Extract underlying functions from FastMCP FunctionTool wrappers
create_task = server.create_task.fn
list_tasks = server.list_tasks.fn
search_tasks = server.search_tasks.fn
get_task_tree = server.get_task_tree.fn
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


class TestListTasksSummaryMode:
    """Test list_tasks with summary/details modes."""

    def test_list_tasks_summary_mode_default(self, test_workspace: str) -> None:
        """Test that summary mode is the default."""
        # Create task with description
        task = create_task(
            title="Test Task",
            description="This is a detailed description that should be excluded in summary mode",
            workspace_path=test_workspace,
            tags="test important",
            priority="high",
        )

        # List tasks (default should be summary mode)
        tasks = list_tasks(workspace_path=test_workspace)

        assert len(tasks) == 1
        summary_task = tasks[0]

        # Verify summary fields are present
        assert "id" in summary_task
        assert "title" in summary_task
        assert "status" in summary_task
        assert "priority" in summary_task
        assert "tags" in summary_task
        assert "created_at" in summary_task
        assert "updated_at" in summary_task
        assert "parent_task_id" in summary_task

        # Verify large fields are excluded
        assert "description" not in summary_task
        assert "workspace_metadata" not in summary_task
        assert "depends_on" not in summary_task
        assert "file_references" not in summary_task
        assert "blocker_reason" not in summary_task

    def test_list_tasks_summary_mode_explicit(self, test_workspace: str) -> None:
        """Test explicit summary mode parameter."""
        create_task(
            title="Test Task",
            description="This is a detailed description",
            workspace_path=test_workspace,
        )

        # List with explicit mode="summary"
        tasks = list_tasks(workspace_path=test_workspace, mode="summary")

        assert len(tasks) == 1
        assert "description" not in tasks[0]

    def test_list_tasks_details_mode(self, test_workspace: str) -> None:
        """Test details mode returns all fields."""
        create_task(
            title="Test Task",
            description="This is a detailed description",
            workspace_path=test_workspace,
            tags="test",
        )

        # List with mode="details"
        tasks = list_tasks(workspace_path=test_workspace, mode="details")

        assert len(tasks) == 1
        detail_task = tasks[0]

        # Verify all fields are present in details mode
        assert "id" in detail_task
        assert "title" in detail_task
        assert "description" in detail_task
        assert detail_task["description"] == "This is a detailed description"
        assert "workspace_metadata" in detail_task
        assert "tags" in detail_task

    def test_list_tasks_invalid_mode(self, test_workspace: str) -> None:
        """Test that invalid mode raises ValueError."""
        create_task(title="Test Task", workspace_path=test_workspace)

        with pytest.raises(ValueError, match="Invalid mode"):
            list_tasks(workspace_path=test_workspace, mode="invalid_mode")

    def test_list_tasks_summary_with_filters(self, test_workspace: str) -> None:
        """Test summary mode works with filters."""
        create_task(title="Task 1", status="todo", workspace_path=test_workspace)
        create_task(title="Task 2", status="in_progress", workspace_path=test_workspace)
        create_task(title="Task 3", status="done", workspace_path=test_workspace)

        # List with filter in summary mode
        in_progress = list_tasks(
            workspace_path=test_workspace,
            status="in_progress",
            mode="summary",
        )

        assert len(in_progress) == 1
        assert in_progress[0]["title"] == "Task 2"
        assert in_progress[0]["status"] == "in_progress"
        assert "description" not in in_progress[0]


class TestSearchTasksSummaryMode:
    """Test search_tasks with summary/details modes."""

    def test_search_tasks_summary_mode_default(self, test_workspace: str) -> None:
        """Test that search_tasks defaults to summary mode."""
        create_task(
            title="Important Feature",
            description="Long description about feature",
            workspace_path=test_workspace,
        )

        # Search (default should be summary mode)
        results = search_tasks(search_term="Important", workspace_path=test_workspace)

        assert len(results) == 1
        assert "description" not in results[0]
        assert "title" in results[0]

    def test_search_tasks_details_mode(self, test_workspace: str) -> None:
        """Test search_tasks with details mode."""
        create_task(
            title="Important Feature",
            description="Long description about feature",
            workspace_path=test_workspace,
        )

        # Search with details mode
        results = search_tasks(
            search_term="Important",
            workspace_path=test_workspace,
            mode="details",
        )

        assert len(results) == 1
        assert "description" in results[0]
        assert results[0]["description"] == "Long description about feature"


class TestGetTaskTreeSummaryMode:
    """Test get_task_tree with summary/details modes."""

    def test_get_task_tree_summary_mode_recursive(self, test_workspace: str) -> None:
        """Test that get_task_tree summary mode applies recursively to subtasks."""
        # Create parent task
        parent = create_task(
            title="Parent Task",
            description="Parent description",
            workspace_path=test_workspace,
        )

        # Create subtask
        child = create_task(
            title="Child Task",
            description="Child description",
            parent_task_id=parent["id"],
            workspace_path=test_workspace,
        )

        # Get tree in summary mode
        tree = get_task_tree(task_id=parent["id"], workspace_path=test_workspace, mode="summary")

        # Verify parent is summarized
        assert "description" not in tree
        assert "title" in tree

        # Verify subtasks are also summarized
        assert "subtasks" in tree
        assert len(tree["subtasks"]) == 1
        assert "description" not in tree["subtasks"][0]
        assert "title" in tree["subtasks"][0]

    def test_get_task_tree_details_mode(self, test_workspace: str) -> None:
        """Test get_task_tree with details mode."""
        parent = create_task(
            title="Parent Task",
            description="Parent description",
            workspace_path=test_workspace,
        )

        create_task(
            title="Child Task",
            description="Child description",
            parent_task_id=parent["id"],
            workspace_path=test_workspace,
        )

        # Get tree in details mode
        tree = get_task_tree(task_id=parent["id"], workspace_path=test_workspace, mode="details")

        # Verify all fields present
        assert "description" in tree
        assert tree["description"] == "Parent description"
        assert tree["subtasks"][0]["description"] == "Child description"


class TestListEntitiesSummaryMode:
    """Test list_entities with summary/details modes."""

    def test_list_entities_summary_mode_default(self, test_workspace: str) -> None:
        """Test that list_entities defaults to summary mode."""
        create_entity(
            entity_type="file",
            name="AuthController",
            identifier="/src/auth.py",
            description="Handles user authentication",
            workspace_path=test_workspace,
        )

        # List entities (default summary mode)
        entities = list_entities(workspace_path=test_workspace)

        assert len(entities) == 1
        entity = entities[0]

        # Verify summary fields
        assert "id" in entity
        assert "entity_type" in entity
        assert "name" in entity
        assert "identifier" in entity
        assert "tags" in entity
        assert "created_at" in entity

        # Verify excluded fields
        assert "description" not in entity
        assert "metadata" not in entity

    def test_list_entities_details_mode(self, test_workspace: str) -> None:
        """Test list_entities with details mode."""
        create_entity(
            entity_type="file",
            name="AuthController",
            identifier="/src/auth.py",
            description="Handles user authentication",
            workspace_path=test_workspace,
        )

        # List entities with details mode
        entities = list_entities(workspace_path=test_workspace, mode="details")

        assert len(entities) == 1
        entity = entities[0]

        # Verify all fields present
        assert "description" in entity
        assert entity["description"] == "Handles user authentication"


class TestSearchEntitiesSummaryMode:
    """Test search_entities with summary/details modes."""

    def test_search_entities_summary_mode_default(self, test_workspace: str) -> None:
        """Test that search_entities defaults to summary mode."""
        create_entity(
            entity_type="file",
            name="AuthController",
            identifier="/src/auth.py",
            description="Handles user authentication",
            workspace_path=test_workspace,
        )

        # Search entities (default summary mode)
        results = search_entities(search_term="Auth", workspace_path=test_workspace)

        assert len(results) == 1
        assert "description" not in results[0]

    def test_search_entities_details_mode(self, test_workspace: str) -> None:
        """Test search_entities with details mode."""
        create_entity(
            entity_type="file",
            name="AuthController",
            identifier="/src/auth.py",
            description="Handles user authentication",
            workspace_path=test_workspace,
        )

        # Search with details mode
        results = search_entities(
            search_term="Auth",
            workspace_path=test_workspace,
            mode="details",
        )

        assert len(results) == 1
        assert "description" in results[0]


class TestTaskEntitiesRelationshipMode:
    """Test get_task_entities and get_entity_tasks with summary/details modes."""

    def test_get_task_entities_summary_mode_preserves_link_metadata(
        self, test_workspace: str
    ) -> None:
        """Test that summary mode preserves link metadata."""
        task = create_task(title="Task", workspace_path=test_workspace)
        entity = create_entity(
            entity_type="file",
            name="File",
            identifier="/src/file.py",
            description="Long description of file",
            workspace_path=test_workspace,
        )

        link_entity_to_task(task_id=task["id"], entity_id=entity["id"], workspace_path=test_workspace)

        # Get entities in summary mode
        entities = get_task_entities(task_id=task["id"], workspace_path=test_workspace, mode="summary")

        assert len(entities) == 1
        entity_result = entities[0]

        # Verify summary fields present
        assert "id" in entity_result
        assert "name" in entity_result
        assert "identifier" in entity_result

        # Verify link metadata is preserved
        assert "link_created_at" in entity_result
        assert "link_created_by" in entity_result

        # Verify description excluded
        assert "description" not in entity_result

    def test_get_task_entities_details_mode(self, test_workspace: str) -> None:
        """Test get_task_entities with details mode."""
        task = create_task(title="Task", workspace_path=test_workspace)
        entity = create_entity(
            entity_type="file",
            name="File",
            identifier="/src/file.py",
            description="Long description of file",
            workspace_path=test_workspace,
        )

        link_entity_to_task(task_id=task["id"], entity_id=entity["id"], workspace_path=test_workspace)

        # Get entities in details mode
        entities = get_task_entities(
            task_id=task["id"],
            workspace_path=test_workspace,
            mode="details",
        )

        assert len(entities) == 1
        assert "description" in entities[0]

    def test_get_entity_tasks_summary_mode_preserves_link_metadata(
        self, test_workspace: str
    ) -> None:
        """Test that get_entity_tasks summary mode preserves link metadata."""
        task = create_task(
            title="Task",
            description="Long task description",
            workspace_path=test_workspace,
        )
        entity = create_entity(
            entity_type="file",
            name="File",
            identifier="/src/file.py",
            workspace_path=test_workspace,
        )

        link_entity_to_task(task_id=task["id"], entity_id=entity["id"], workspace_path=test_workspace)

        # Get tasks in summary mode
        tasks = get_entity_tasks(entity_id=entity["id"], workspace_path=test_workspace, mode="summary")

        assert len(tasks) == 1
        task_result = tasks[0]

        # Verify summary fields
        assert "id" in task_result
        assert "title" in task_result

        # Verify link metadata preserved
        assert "link_created_at" in task_result
        assert "link_created_by" in task_result

        # Verify description excluded
        assert "description" not in task_result

    def test_get_entity_tasks_details_mode(self, test_workspace: str) -> None:
        """Test get_entity_tasks with details mode."""
        task = create_task(
            title="Task",
            description="Long task description",
            workspace_path=test_workspace,
        )
        entity = create_entity(
            entity_type="file",
            name="File",
            identifier="/src/file.py",
            workspace_path=test_workspace,
        )

        link_entity_to_task(task_id=task["id"], entity_id=entity["id"], workspace_path=test_workspace)

        # Get tasks in details mode
        tasks = get_entity_tasks(entity_id=entity["id"], workspace_path=test_workspace, mode="details")

        assert len(tasks) == 1
        assert "description" in tasks[0]


class TestSummaryModeFieldValues:
    """Test that summary mode correctly preserves field values."""

    def test_summary_task_fields_accurate(self, test_workspace: str) -> None:
        """Test that summary mode returns accurate field values."""
        task = create_task(
            title="Test Task",
            status="in_progress",
            priority="high",
            tags="urgent backend",
            workspace_path=test_workspace,
        )

        tasks = list_tasks(workspace_path=test_workspace, mode="summary")
        summary_task = tasks[0]

        assert summary_task["id"] == task["id"]
        assert summary_task["title"] == "Test Task"
        assert summary_task["status"] == "in_progress"
        assert summary_task["priority"] == "high"
        assert summary_task["tags"] == "urgent backend"

    def test_summary_entity_fields_accurate(self, test_workspace: str) -> None:
        """Test that summary mode returns accurate entity field values."""
        entity = create_entity(
            entity_type="file",
            name="AuthModule",
            identifier="/src/auth.py",
            tags="backend api",
            workspace_path=test_workspace,
        )

        entities = list_entities(workspace_path=test_workspace, mode="summary")
        summary_entity = entities[0]

        assert summary_entity["id"] == entity["id"]
        assert summary_entity["entity_type"] == "file"
        assert summary_entity["name"] == "AuthModule"
        assert summary_entity["identifier"] == "/src/auth.py"
        assert summary_entity["tags"] == "backend api"
