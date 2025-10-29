"""Integration tests for entity MCP tools."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

# Import MCP tool wrappers and extract underlying functions
from task_mcp import server

# Extract entity tool functions from FastMCP FunctionTool wrappers
create_entity = server.create_entity.fn
update_entity = server.update_entity.fn
get_entity = server.get_entity.fn
list_entities = server.list_entities.fn
delete_entity = server.delete_entity.fn
link_entity_to_task = server.link_entity_to_task.fn
get_task_entities = server.get_task_entities.fn

# Also need create_task for testing task-entity links
create_task = server.create_task.fn


@pytest.fixture
def test_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[str, None, None]:
    """Create isolated test workspace."""
    workspace = str(tmp_path / "test-project")
    Path(workspace).mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    yield workspace


class TestCreateEntity:
    """Test create_entity tool."""

    def test_create_file_entity(self, test_workspace: str) -> None:
        """Test creating a file entity with full details."""
        entity = create_entity(
            entity_type="file",
            name="Login Controller",
            identifier="/src/auth/login.py",
            description="User authentication controller",
            metadata={"language": "python", "line_count": 250},
            tags="auth backend",
            workspace_path=test_workspace,
        )

        assert entity["id"] is not None
        assert entity["entity_type"] == "file"
        assert entity["name"] == "Login Controller"
        assert entity["identifier"] == "/src/auth/login.py"
        assert entity["description"] == "User authentication controller"
        assert entity["metadata"] == '{"language": "python", "line_count": 250}'
        assert entity["tags"] == "auth backend"
        assert entity["created_at"] is not None
        assert entity["updated_at"] is not None
        assert entity["deleted_at"] is None

    def test_create_other_entity(self, test_workspace: str) -> None:
        """Test creating an 'other' type entity."""
        entity = create_entity(
            entity_type="other",
            name="ABC Insurance Vendor",
            identifier="ABC-INS",
            description="Commission processing vendor",
            metadata={"vendor_code": "ABC", "format": "xlsx"},
            tags="vendor insurance",
            workspace_path=test_workspace,
        )

        assert entity["entity_type"] == "other"
        assert entity["name"] == "ABC Insurance Vendor"
        assert entity["identifier"] == "ABC-INS"
        assert entity["metadata"] == '{"vendor_code": "ABC", "format": "xlsx"}'

    def test_create_entity_with_metadata_dict(self, test_workspace: str) -> None:
        """Test creating entity with metadata as dict."""
        entity = create_entity(
            entity_type="file",
            name="Config File",
            metadata={"env": "production", "version": 2},
            workspace_path=test_workspace,
        )

        assert entity["metadata"] == '{"env": "production", "version": 2}'

    def test_create_entity_with_metadata_list(self, test_workspace: str) -> None:
        """Test creating entity with metadata as list."""
        entity = create_entity(
            entity_type="file",
            name="Dependencies",
            metadata=["python-3.11", "pytest", "fastapi"],
            workspace_path=test_workspace,
        )

        assert entity["metadata"] == '["python-3.11", "pytest", "fastapi"]'

    def test_create_entity_with_metadata_string(self, test_workspace: str) -> None:
        """Test creating entity with metadata as JSON string."""
        entity = create_entity(
            entity_type="file",
            name="Package",
            metadata='{"name": "mypackage", "version": "1.0.0"}',
            workspace_path=test_workspace,
        )

        assert entity["metadata"] == '{"name": "mypackage", "version": "1.0.0"}'

    def test_create_entity_minimal(self, test_workspace: str) -> None:
        """Test creating entity with only required fields."""
        entity = create_entity(
            entity_type="file",
            name="Minimal Entity",
            workspace_path=test_workspace,
        )

        assert entity["entity_type"] == "file"
        assert entity["name"] == "Minimal Entity"
        assert entity["identifier"] is None
        assert entity["description"] is None
        assert entity["metadata"] is None
        assert entity["tags"] is None

    def test_create_entity_duplicate_identifier_error(self, test_workspace: str) -> None:
        """Test creating entity with duplicate identifier raises error."""
        # Create first entity
        create_entity(
            entity_type="file",
            name="First File",
            identifier="/src/duplicate.py",
            workspace_path=test_workspace,
        )

        # Attempt to create duplicate
        with pytest.raises(ValueError, match="Entity already exists"):
            create_entity(
                entity_type="file",
                name="Second File",
                identifier="/src/duplicate.py",
                workspace_path=test_workspace,
            )

    def test_create_entity_invalid_type_error(self, test_workspace: str) -> None:
        """Test creating entity with invalid type raises error."""
        with pytest.raises(ValueError, match="entity_type must be one of"):
            create_entity(
                entity_type="invalid_type",
                name="Bad Entity",
                workspace_path=test_workspace,
            )

    def test_create_entity_description_length_validation(self, test_workspace: str) -> None:
        """Test description length is validated (max 10k chars)."""
        # 10k chars is fine
        long_desc = "x" * 10_000
        entity = create_entity(
            entity_type="file",
            name="Long Description",
            description=long_desc,
            workspace_path=test_workspace,
        )
        assert len(entity["description"]) == 10_000

        # Over 10k chars should fail
        too_long_desc = "x" * 10_001
        with pytest.raises(ValueError, match="Description exceeds 10,000 character limit"):
            create_entity(
                entity_type="file",
                name="Too Long",
                description=too_long_desc,
                workspace_path=test_workspace,
            )

    def test_create_entity_auto_captures_conversation_id(self, test_workspace: str) -> None:
        """Test that created_by field is auto-captured from context."""
        # When called directly (no context), created_by should be None
        entity = create_entity(
            entity_type="file",
            name="Test Entity",
            workspace_path=test_workspace,
        )
        # In direct calls without context, created_by is None
        assert entity["created_by"] is None

    def test_create_entity_tags_normalized(self, test_workspace: str) -> None:
        """Test that tags are normalized to lowercase with single spaces."""
        entity = create_entity(
            entity_type="file",
            name="Tagged Entity",
            tags="  Python   Django  REST  ",
            workspace_path=test_workspace,
        )

        assert entity["tags"] == "python django rest"

    def test_create_entity_duplicate_allowed_different_type(self, test_workspace: str) -> None:
        """Test same identifier allowed for different entity types."""
        # Create file entity
        create_entity(
            entity_type="file",
            name="File Entity",
            identifier="shared-id",
            workspace_path=test_workspace,
        )

        # Create other entity with same identifier - should succeed
        entity2 = create_entity(
            entity_type="other",
            name="Other Entity",
            identifier="shared-id",
            workspace_path=test_workspace,
        )

        assert entity2["identifier"] == "shared-id"
        assert entity2["entity_type"] == "other"


class TestUpdateEntity:
    """Test update_entity tool."""

    def test_update_entity_partial(self, test_workspace: str) -> None:
        """Test updating entity with partial fields."""
        # Create entity
        entity = create_entity(
            entity_type="file",
            name="Original Name",
            description="Original description",
            workspace_path=test_workspace,
        )

        # Update only name
        updated = update_entity(
            entity["id"],
            name="Updated Name",
            workspace_path=test_workspace,
        )

        assert updated["name"] == "Updated Name"
        assert updated["description"] == "Original description"
        assert updated["updated_at"] != entity["updated_at"]

    def test_update_entity_full(self, test_workspace: str) -> None:
        """Test updating all entity fields."""
        # Create minimal entity
        entity = create_entity(
            entity_type="file",
            name="Original",
            workspace_path=test_workspace,
        )

        # Update all fields
        updated = update_entity(
            entity["id"],
            name="New Name",
            identifier="/new/path.py",
            description="New description",
            metadata={"key": "value"},
            tags="new tags",
            workspace_path=test_workspace,
        )

        assert updated["name"] == "New Name"
        assert updated["identifier"] == "/new/path.py"
        assert updated["description"] == "New description"
        assert updated["metadata"] == '{"key": "value"}'
        assert updated["tags"] == "new tags"

    def test_update_entity_metadata_dict(self, test_workspace: str) -> None:
        """Test updating entity metadata with dict."""
        entity = create_entity(
            entity_type="file",
            name="Test",
            workspace_path=test_workspace,
        )

        updated = update_entity(
            entity["id"],
            metadata={"version": 2, "status": "active"},
            workspace_path=test_workspace,
        )

        assert updated["metadata"] == '{"version": 2, "status": "active"}'

    def test_update_entity_metadata_list(self, test_workspace: str) -> None:
        """Test updating entity metadata with list."""
        entity = create_entity(
            entity_type="file",
            name="Test",
            workspace_path=test_workspace,
        )

        updated = update_entity(
            entity["id"],
            metadata=["item1", "item2", "item3"],
            workspace_path=test_workspace,
        )

        assert updated["metadata"] == '["item1", "item2", "item3"]'

    def test_update_entity_not_found_error(self, test_workspace: str) -> None:
        """Test updating non-existent entity raises error."""
        with pytest.raises(ValueError, match="Entity 999 not found or has been deleted"):
            update_entity(
                999,
                name="New Name",
                workspace_path=test_workspace,
            )

    def test_update_entity_duplicate_identifier_error(self, test_workspace: str) -> None:
        """Test updating to duplicate identifier raises error."""
        # Create two entities
        entity1 = create_entity(
            entity_type="file",
            name="Entity 1",
            identifier="/path1.py",
            workspace_path=test_workspace,
        )
        create_entity(
            entity_type="file",
            name="Entity 2",
            identifier="/path2.py",
            workspace_path=test_workspace,
        )

        # Try to update entity1 to use entity2's identifier
        with pytest.raises(ValueError, match="already exists with identifier"):
            update_entity(
                entity1["id"],
                identifier="/path2.py",
                workspace_path=test_workspace,
            )

    def test_update_entity_updates_timestamp(self, test_workspace: str) -> None:
        """Test that updated_at timestamp is automatically updated."""
        entity = create_entity(
            entity_type="file",
            name="Test",
            workspace_path=test_workspace,
        )

        original_updated_at = entity["updated_at"]

        # Update entity
        updated = update_entity(
            entity["id"],
            name="Updated",
            workspace_path=test_workspace,
        )

        assert updated["updated_at"] != original_updated_at

    def test_update_entity_identifier_same_value_allowed(self, test_workspace: str) -> None:
        """Test updating entity with same identifier is allowed."""
        entity = create_entity(
            entity_type="file",
            name="Test",
            identifier="/same.py",
            workspace_path=test_workspace,
        )

        # Update with same identifier should succeed
        updated = update_entity(
            entity["id"],
            identifier="/same.py",
            name="New Name",
            workspace_path=test_workspace,
        )

        assert updated["identifier"] == "/same.py"
        assert updated["name"] == "New Name"


class TestGetEntity:
    """Test get_entity tool."""

    def test_get_entity_by_id(self, test_workspace: str) -> None:
        """Test retrieving entity by ID."""
        created = create_entity(
            entity_type="file",
            name="Test Entity",
            identifier="/test.py",
            workspace_path=test_workspace,
        )

        retrieved = get_entity(created["id"], test_workspace)

        assert retrieved["id"] == created["id"]
        assert retrieved["name"] == "Test Entity"
        assert retrieved["identifier"] == "/test.py"

    def test_get_entity_not_found_error(self, test_workspace: str) -> None:
        """Test getting non-existent entity raises error."""
        with pytest.raises(ValueError, match="Entity 999 not found or has been deleted"):
            get_entity(999, test_workspace)

    def test_get_entity_soft_deleted_error(self, test_workspace: str) -> None:
        """Test getting soft-deleted entity raises error."""
        # Create and delete entity
        entity = create_entity(
            entity_type="file",
            name="To Delete",
            workspace_path=test_workspace,
        )
        delete_entity(entity["id"], test_workspace)

        # Try to get deleted entity
        with pytest.raises(ValueError, match="not found or has been deleted"):
            get_entity(entity["id"], test_workspace)


class TestListEntities:
    """Test list_entities tool."""

    def test_list_all_entities(self, test_workspace: str) -> None:
        """Test listing all entities without filters."""
        # Create multiple entities
        create_entity(
            entity_type="file",
            name="File 1",
            workspace_path=test_workspace,
        )
        create_entity(
            entity_type="other",
            name="Vendor 1",
            workspace_path=test_workspace,
        )
        create_entity(
            entity_type="file",
            name="File 2",
            workspace_path=test_workspace,
        )

        entities = list_entities(workspace_path=test_workspace)

        assert len(entities) == 3
        names = {e["name"] for e in entities}
        assert names == {"File 1", "Vendor 1", "File 2"}

    def test_list_entities_filter_by_type(self, test_workspace: str) -> None:
        """Test listing entities filtered by type."""
        # Create mixed entities
        create_entity(
            entity_type="file",
            name="File 1",
            workspace_path=test_workspace,
        )
        create_entity(
            entity_type="other",
            name="Vendor 1",
            workspace_path=test_workspace,
        )
        create_entity(
            entity_type="file",
            name="File 2",
            workspace_path=test_workspace,
        )

        # Filter by file type
        file_entities = list_entities(entity_type="file", workspace_path=test_workspace)
        assert len(file_entities) == 2
        assert all(e["entity_type"] == "file" for e in file_entities)

        # Filter by other type
        other_entities = list_entities(entity_type="other", workspace_path=test_workspace)
        assert len(other_entities) == 1
        assert other_entities[0]["name"] == "Vendor 1"

    def test_list_entities_filter_by_tags(self, test_workspace: str) -> None:
        """Test listing entities filtered by tags."""
        # Create entities with different tags
        create_entity(
            entity_type="file",
            name="Auth File",
            tags="auth backend",
            workspace_path=test_workspace,
        )
        create_entity(
            entity_type="file",
            name="Frontend File",
            tags="frontend ui",
            workspace_path=test_workspace,
        )
        create_entity(
            entity_type="file",
            name="API File",
            tags="backend api auth",
            workspace_path=test_workspace,
        )

        # Filter by single tag
        auth_entities = list_entities(tags="auth", workspace_path=test_workspace)
        assert len(auth_entities) == 2
        names = {e["name"] for e in auth_entities}
        assert names == {"Auth File", "API File"}

        # Filter by multiple tags (OR logic)
        backend_entities = list_entities(tags="backend frontend", workspace_path=test_workspace)
        assert len(backend_entities) == 3  # All match either backend or frontend

    def test_list_entities_filter_by_tags_partial_match(self, test_workspace: str) -> None:
        """Test tag filtering uses partial match."""
        create_entity(
            entity_type="file",
            name="Test File",
            tags="authentication authorization",
            workspace_path=test_workspace,
        )

        # Partial match should work
        entities = list_entities(tags="auth", workspace_path=test_workspace)
        assert len(entities) == 1
        assert entities[0]["name"] == "Test File"

    def test_list_entities_excludes_deleted(self, test_workspace: str) -> None:
        """Test that soft-deleted entities are excluded from list."""
        # Create entities
        entity1 = create_entity(
            entity_type="file",
            name="Active",
            workspace_path=test_workspace,
        )
        entity2 = create_entity(
            entity_type="file",
            name="To Delete",
            workspace_path=test_workspace,
        )

        # Delete one entity
        delete_entity(entity2["id"], test_workspace)

        # List should only show active entity
        entities = list_entities(workspace_path=test_workspace)
        assert len(entities) == 1
        assert entities[0]["id"] == entity1["id"]

    def test_list_entities_empty_result(self, test_workspace: str) -> None:
        """Test listing entities returns empty list when no matches."""
        entities = list_entities(workspace_path=test_workspace)
        assert entities == []

        # Create entity but filter to non-matching type
        create_entity(
            entity_type="file",
            name="File",
            workspace_path=test_workspace,
        )

        other_entities = list_entities(entity_type="other", workspace_path=test_workspace)
        assert other_entities == []

    def test_list_entities_ordered_by_created_at_desc(self, test_workspace: str) -> None:
        """Test entities are returned in reverse chronological order."""
        e1 = create_entity(entity_type="file", name="First", workspace_path=test_workspace)
        e2 = create_entity(entity_type="file", name="Second", workspace_path=test_workspace)
        e3 = create_entity(entity_type="file", name="Third", workspace_path=test_workspace)

        entities = list_entities(workspace_path=test_workspace)

        # Should be in reverse order (newest first)
        assert entities[0]["id"] == e3["id"]
        assert entities[1]["id"] == e2["id"]
        assert entities[2]["id"] == e1["id"]


class TestDeleteEntity:
    """Test delete_entity tool."""

    def test_delete_entity(self, test_workspace: str) -> None:
        """Test soft-deleting an entity."""
        entity = create_entity(
            entity_type="file",
            name="To Delete",
            workspace_path=test_workspace,
        )

        result = delete_entity(entity["id"], test_workspace)

        assert result["success"] is True
        assert result["entity_id"] == entity["id"]
        assert result["deleted_links"] == 0

        # Entity should not appear in list
        entities = list_entities(workspace_path=test_workspace)
        assert len(entities) == 0

    def test_delete_entity_cascades_links(self, test_workspace: str) -> None:
        """Test deleting entity cascades to soft-delete associated links."""
        # Create task and entity
        task = create_task(title="Test Task", workspace_path=test_workspace)
        entity = create_entity(
            entity_type="file",
            name="Linked Entity",
            workspace_path=test_workspace,
        )

        # Create links
        link_entity_to_task(task["id"], entity["id"], test_workspace)

        # Delete entity
        result = delete_entity(entity["id"], test_workspace)

        assert result["success"] is True
        assert result["deleted_links"] == 1

        # Links should not appear in get_task_entities
        task_entities = get_task_entities(task["id"], test_workspace)
        assert len(task_entities) == 0

    def test_delete_entity_cascades_multiple_links(self, test_workspace: str) -> None:
        """Test deleting entity cascades to multiple task links."""
        # Create multiple tasks
        task1 = create_task(title="Task 1", workspace_path=test_workspace)
        task2 = create_task(title="Task 2", workspace_path=test_workspace)
        task3 = create_task(title="Task 3", workspace_path=test_workspace)

        # Create entity and link to all tasks
        entity = create_entity(
            entity_type="file",
            name="Shared Entity",
            workspace_path=test_workspace,
        )
        link_entity_to_task(task1["id"], entity["id"], test_workspace)
        link_entity_to_task(task2["id"], entity["id"], test_workspace)
        link_entity_to_task(task3["id"], entity["id"], test_workspace)

        # Delete entity
        result = delete_entity(entity["id"], test_workspace)

        assert result["deleted_links"] == 3

    def test_delete_entity_not_found_error(self, test_workspace: str) -> None:
        """Test deleting non-existent entity raises error."""
        with pytest.raises(ValueError, match="Entity 999 not found or already deleted"):
            delete_entity(999, test_workspace)

    def test_delete_entity_already_deleted_error(self, test_workspace: str) -> None:
        """Test deleting already-deleted entity raises error."""
        entity = create_entity(
            entity_type="file",
            name="Test",
            workspace_path=test_workspace,
        )

        # Delete once
        delete_entity(entity["id"], test_workspace)

        # Try to delete again
        with pytest.raises(ValueError, match="not found or already deleted"):
            delete_entity(entity["id"], test_workspace)

    def test_delete_entity_allows_recreation(self, test_workspace: str) -> None:
        """Test that entity can be recreated after soft delete."""
        # Create and delete entity
        entity = create_entity(
            entity_type="file",
            name="Original",
            identifier="/unique.py",
            workspace_path=test_workspace,
        )
        delete_entity(entity["id"], test_workspace)

        # Recreate with same identifier should succeed
        new_entity = create_entity(
            entity_type="file",
            name="Recreated",
            identifier="/unique.py",
            workspace_path=test_workspace,
        )

        assert new_entity["identifier"] == "/unique.py"
        assert new_entity["name"] == "Recreated"
        assert new_entity["id"] != entity["id"]


class TestLinkEntityToTask:
    """Test link_entity_to_task tool."""

    def test_link_entity_to_task(self, test_workspace: str) -> None:
        """Test creating a link between task and entity."""
        task = create_task(title="Test Task", workspace_path=test_workspace)
        entity = create_entity(
            entity_type="file",
            name="Test Entity",
            workspace_path=test_workspace,
        )

        link = link_entity_to_task(task["id"], entity["id"], test_workspace)

        assert link["link_id"] is not None
        assert link["task_id"] == task["id"]
        assert link["entity_id"] == entity["id"]
        assert link["created_at"] is not None

    def test_link_entity_to_task_duplicate_error(self, test_workspace: str) -> None:
        """Test creating duplicate link raises error."""
        task = create_task(title="Test Task", workspace_path=test_workspace)
        entity = create_entity(
            entity_type="file",
            name="Test Entity",
            workspace_path=test_workspace,
        )

        # Create first link
        link_entity_to_task(task["id"], entity["id"], test_workspace)

        # Try to create duplicate link
        with pytest.raises(ValueError, match="Link already exists"):
            link_entity_to_task(task["id"], entity["id"], test_workspace)

    def test_link_entity_to_task_invalid_task_error(self, test_workspace: str) -> None:
        """Test linking to non-existent task raises error."""
        entity = create_entity(
            entity_type="file",
            name="Test Entity",
            workspace_path=test_workspace,
        )

        with pytest.raises(ValueError, match="Task 999 not found or has been deleted"):
            link_entity_to_task(999, entity["id"], test_workspace)

    def test_link_entity_to_task_invalid_entity_error(self, test_workspace: str) -> None:
        """Test linking to non-existent entity raises error."""
        task = create_task(title="Test Task", workspace_path=test_workspace)

        with pytest.raises(ValueError, match="Entity 999 not found or has been deleted"):
            link_entity_to_task(task["id"], 999, test_workspace)

    def test_link_entity_to_task_deleted_task_error(self, test_workspace: str) -> None:
        """Test linking to soft-deleted task raises error."""
        from task_mcp.server import delete_task

        task = create_task(title="Test Task", workspace_path=test_workspace)
        entity = create_entity(
            entity_type="file",
            name="Test Entity",
            workspace_path=test_workspace,
        )

        # Delete task
        delete_task.fn(task["id"], test_workspace)

        # Try to link to deleted task
        with pytest.raises(ValueError, match="Task .* not found or has been deleted"):
            link_entity_to_task(task["id"], entity["id"], test_workspace)

    def test_link_entity_to_task_deleted_entity_error(self, test_workspace: str) -> None:
        """Test linking to soft-deleted entity raises error."""
        task = create_task(title="Test Task", workspace_path=test_workspace)
        entity = create_entity(
            entity_type="file",
            name="Test Entity",
            workspace_path=test_workspace,
        )

        # Delete entity
        delete_entity(entity["id"], test_workspace)

        # Try to link to deleted entity
        with pytest.raises(ValueError, match="Entity .* not found or has been deleted"):
            link_entity_to_task(task["id"], entity["id"], test_workspace)

    def test_link_entity_to_task_multiple_entities(self, test_workspace: str) -> None:
        """Test linking multiple entities to one task."""
        task = create_task(title="Test Task", workspace_path=test_workspace)
        entity1 = create_entity(entity_type="file", name="Entity 1", workspace_path=test_workspace)
        entity2 = create_entity(entity_type="file", name="Entity 2", workspace_path=test_workspace)
        entity3 = create_entity(entity_type="file", name="Entity 3", workspace_path=test_workspace)

        # Link all entities to task
        link_entity_to_task(task["id"], entity1["id"], test_workspace)
        link_entity_to_task(task["id"], entity2["id"], test_workspace)
        link_entity_to_task(task["id"], entity3["id"], test_workspace)

        # Verify all links
        task_entities = get_task_entities(task["id"], test_workspace)
        assert len(task_entities) == 3

    def test_link_entity_to_task_multiple_tasks(self, test_workspace: str) -> None:
        """Test linking one entity to multiple tasks."""
        task1 = create_task(title="Task 1", workspace_path=test_workspace)
        task2 = create_task(title="Task 2", workspace_path=test_workspace)
        task3 = create_task(title="Task 3", workspace_path=test_workspace)
        entity = create_entity(entity_type="file", name="Shared Entity", workspace_path=test_workspace)

        # Link entity to all tasks
        link_entity_to_task(task1["id"], entity["id"], test_workspace)
        link_entity_to_task(task2["id"], entity["id"], test_workspace)
        link_entity_to_task(task3["id"], entity["id"], test_workspace)

        # Verify each task has the entity
        for task in [task1, task2, task3]:
            entities = get_task_entities(task["id"], test_workspace)
            assert len(entities) == 1
            assert entities[0]["id"] == entity["id"]


class TestGetTaskEntities:
    """Test get_task_entities tool."""

    def test_get_task_entities(self, test_workspace: str) -> None:
        """Test getting all entities linked to a task."""
        task = create_task(title="Test Task", workspace_path=test_workspace)
        entity1 = create_entity(
            entity_type="file",
            name="Entity 1",
            identifier="/file1.py",
            workspace_path=test_workspace,
        )
        entity2 = create_entity(
            entity_type="other",
            name="Entity 2",
            identifier="vendor-abc",
            workspace_path=test_workspace,
        )

        # Link entities to task
        link_entity_to_task(task["id"], entity1["id"], test_workspace)
        link_entity_to_task(task["id"], entity2["id"], test_workspace)

        # Get task entities
        entities = get_task_entities(task["id"], test_workspace)

        assert len(entities) == 2
        entity_names = {e["name"] for e in entities}
        assert entity_names == {"Entity 1", "Entity 2"}

        # Verify link metadata is included
        for entity in entities:
            assert "link_created_at" in entity
            assert "link_created_by" in entity
            assert entity["link_created_at"] is not None

    def test_get_task_entities_includes_all_entity_fields(self, test_workspace: str) -> None:
        """Test that all entity fields are included in response."""
        task = create_task(title="Test Task", workspace_path=test_workspace)
        entity = create_entity(
            entity_type="file",
            name="Full Entity",
            identifier="/path/file.py",
            description="Entity description",
            metadata={"key": "value"},
            tags="tag1 tag2",
            workspace_path=test_workspace,
        )
        link_entity_to_task(task["id"], entity["id"], test_workspace)

        entities = get_task_entities(task["id"], test_workspace)

        assert len(entities) == 1
        e = entities[0]
        assert e["id"] == entity["id"]
        assert e["entity_type"] == "file"
        assert e["name"] == "Full Entity"
        assert e["identifier"] == "/path/file.py"
        assert e["description"] == "Entity description"
        assert e["metadata"] == '{"key": "value"}'
        assert e["tags"] == "tag1 tag2"
        assert e["created_at"] is not None
        assert e["updated_at"] is not None
        assert e["deleted_at"] is None
        assert "link_created_at" in e
        assert "link_created_by" in e

    def test_get_task_entities_empty_result(self, test_workspace: str) -> None:
        """Test getting entities for task with no links."""
        task = create_task(title="Test Task", workspace_path=test_workspace)

        entities = get_task_entities(task["id"], test_workspace)

        assert entities == []

    def test_get_task_entities_excludes_deleted(self, test_workspace: str) -> None:
        """Test that deleted entities are excluded from results."""
        task = create_task(title="Test Task", workspace_path=test_workspace)
        entity1 = create_entity(entity_type="file", name="Active", workspace_path=test_workspace)
        entity2 = create_entity(entity_type="file", name="To Delete", workspace_path=test_workspace)

        # Link both entities
        link_entity_to_task(task["id"], entity1["id"], test_workspace)
        link_entity_to_task(task["id"], entity2["id"], test_workspace)

        # Delete one entity
        delete_entity(entity2["id"], test_workspace)

        # Should only return active entity
        entities = get_task_entities(task["id"], test_workspace)
        assert len(entities) == 1
        assert entities[0]["name"] == "Active"

    def test_get_task_entities_invalid_task_error(self, test_workspace: str) -> None:
        """Test getting entities for non-existent task raises error."""
        with pytest.raises(ValueError, match="Task 999 not found or has been deleted"):
            get_task_entities(999, test_workspace)

    def test_get_task_entities_deleted_task_error(self, test_workspace: str) -> None:
        """Test getting entities for soft-deleted task raises error."""
        from task_mcp.server import delete_task

        task = create_task(title="Test Task", workspace_path=test_workspace)
        delete_task.fn(task["id"], test_workspace)

        with pytest.raises(ValueError, match="Task .* not found or has been deleted"):
            get_task_entities(task["id"], test_workspace)

    def test_get_task_entities_ordered_by_link_created_at_desc(self, test_workspace: str) -> None:
        """Test entities are returned in reverse chronological order of linking."""
        task = create_task(title="Test Task", workspace_path=test_workspace)
        e1 = create_entity(entity_type="file", name="First", workspace_path=test_workspace)
        e2 = create_entity(entity_type="file", name="Second", workspace_path=test_workspace)
        e3 = create_entity(entity_type="file", name="Third", workspace_path=test_workspace)

        # Link in order
        link_entity_to_task(task["id"], e1["id"], test_workspace)
        link_entity_to_task(task["id"], e2["id"], test_workspace)
        link_entity_to_task(task["id"], e3["id"], test_workspace)

        entities = get_task_entities(task["id"], test_workspace)

        # Should be in reverse order (most recent link first)
        assert entities[0]["id"] == e3["id"]
        assert entities[1]["id"] == e2["id"]
        assert entities[2]["id"] == e1["id"]


class TestVendorWorkflow:
    """End-to-end test of vendor use case."""

    def test_vendor_complete_lifecycle(self, test_workspace: str) -> None:
        """
        Test complete vendor workflow:
        1. Create vendor entity (other type)
        2. Create task for vendor integration
        3. Link vendor to task
        4. List all vendors
        5. Get vendors for task
        6. Update vendor metadata (phase change)
        7. Delete vendor (cascade to links)
        8. Verify vendor cannot be retrieved
        """
        # Step 1: Create vendor entity (other type)
        vendor = create_entity(
            entity_type="other",
            name="ABC Insurance Vendor",
            identifier="ABC-INS",
            description="Commission processing vendor for ABC Insurance",
            metadata={"vendor_code": "ABC", "phase": "testing", "formats": ["xlsx", "pdf"]},
            tags="vendor insurance",
            workspace_path=test_workspace,
        )

        assert vendor["id"] is not None
        assert vendor["entity_type"] == "other"
        assert vendor["name"] == "ABC Insurance Vendor"
        assert vendor["identifier"] == "ABC-INS"
        assert vendor["metadata"] == '{"vendor_code": "ABC", "phase": "testing", "formats": ["xlsx", "pdf"]}'
        assert vendor["tags"] == "vendor insurance"

        # Step 2: Create task for vendor integration
        task = create_task(
            title="Integrate ABC Insurance vendor data pipeline",
            description="Implement ETL pipeline for ABC Insurance commission files",
            status="todo",
            priority="high",
            tags="vendor integration",
            workspace_path=test_workspace,
        )

        assert task["id"] is not None
        assert task["title"] == "Integrate ABC Insurance vendor data pipeline"

        # Step 3: Link vendor to task
        link = link_entity_to_task(task["id"], vendor["id"], test_workspace)

        assert link["link_id"] is not None
        assert link["task_id"] == task["id"]
        assert link["entity_id"] == vendor["id"]

        # Step 4: List all vendors (filter by type and tags)
        vendors = list_entities(entity_type="other", tags="vendor", workspace_path=test_workspace)

        assert len(vendors) == 1
        assert vendors[0]["id"] == vendor["id"]
        assert vendors[0]["name"] == "ABC Insurance Vendor"

        # Step 5: Get vendors for task
        task_entities = get_task_entities(task["id"], test_workspace)

        assert len(task_entities) == 1
        assert task_entities[0]["id"] == vendor["id"]
        assert task_entities[0]["entity_type"] == "other"
        assert task_entities[0]["name"] == "ABC Insurance Vendor"
        assert task_entities[0]["link_created_at"] is not None

        # Step 6: Update vendor metadata (phase change: testing → active)
        updated_vendor = update_entity(
            vendor["id"],
            metadata={"vendor_code": "ABC", "phase": "active", "formats": ["xlsx", "pdf"]},
            workspace_path=test_workspace,
        )

        assert updated_vendor["metadata"] == '{"vendor_code": "ABC", "phase": "active", "formats": ["xlsx", "pdf"]}'
        assert updated_vendor["updated_at"] != vendor["updated_at"]

        # Verify phase change persisted
        retrieved_vendor = get_entity(vendor["id"], test_workspace)
        assert '{"vendor_code": "ABC", "phase": "active"' in retrieved_vendor["metadata"]

        # Step 7: Delete vendor (cascade to links)
        delete_result = delete_entity(vendor["id"], test_workspace)

        assert delete_result["success"] is True
        assert delete_result["entity_id"] == vendor["id"]
        assert delete_result["deleted_links"] == 1  # Should cascade delete the task link

        # Step 8: Verify vendor cannot be retrieved
        with pytest.raises(ValueError, match="Entity .* not found or has been deleted"):
            get_entity(vendor["id"], test_workspace)

        # Verify vendor not in list
        vendors_after_delete = list_entities(entity_type="other", workspace_path=test_workspace)
        assert len(vendors_after_delete) == 0

        # Verify task no longer has vendor linked
        task_entities_after_delete = get_task_entities(task["id"], test_workspace)
        assert len(task_entities_after_delete) == 0


class TestFileEntityWorkflow:
    """End-to-end test of file tracking use case."""

    def test_file_entity_complete_lifecycle(self, test_workspace: str) -> None:
        """
        Test complete file entity workflow:
        1. Create file entity with file path identifier
        2. Create task for refactoring
        3. Link file to task
        4. List all file entities
        5. Get files for task
        6. Update file metadata (line count change)
        7. Delete file (task completed)
        8. Verify soft delete allows re-creation
        """
        # Step 1: Create file entity with file path identifier
        file_entity = create_entity(
            entity_type="file",
            name="Auth API Controller",
            identifier="/src/api/auth.py",
            description="Authentication endpoint handler",
            metadata={"language": "python", "line_count": 250, "complexity": "medium"},
            tags="backend api authentication",
            workspace_path=test_workspace,
        )

        assert file_entity["id"] is not None
        assert file_entity["entity_type"] == "file"
        assert file_entity["name"] == "Auth API Controller"
        assert file_entity["identifier"] == "/src/api/auth.py"
        assert file_entity["description"] == "Authentication endpoint handler"
        assert file_entity["metadata"] == '{"language": "python", "line_count": 250, "complexity": "medium"}'
        assert file_entity["tags"] == "backend api authentication"
        assert file_entity["deleted_at"] is None

        # Step 2: Create task for refactoring
        refactor_task = create_task(
            title="Refactor authentication endpoint to use JWT tokens",
            description="Update /src/api/auth.py to implement JWT-based authentication",
            status="in_progress",
            priority="high",
            workspace_path=test_workspace,
        )

        assert refactor_task["id"] is not None
        assert refactor_task["status"] == "in_progress"

        # Step 3: Link file to task
        link = link_entity_to_task(
            refactor_task["id"],
            file_entity["id"],
            test_workspace,
        )

        assert link["link_id"] is not None
        assert link["task_id"] == refactor_task["id"]
        assert link["entity_id"] == file_entity["id"]
        assert link["created_at"] is not None

        # Step 4: List all file entities
        all_files = list_entities(
            entity_type="file",
            workspace_path=test_workspace,
        )

        assert len(all_files) == 1
        assert all_files[0]["id"] == file_entity["id"]
        assert all_files[0]["identifier"] == "/src/api/auth.py"

        # Step 5: Get files for task
        task_files = get_task_entities(
            refactor_task["id"],
            test_workspace,
        )

        assert len(task_files) == 1
        assert task_files[0]["id"] == file_entity["id"]
        assert task_files[0]["name"] == "Auth API Controller"
        assert task_files[0]["identifier"] == "/src/api/auth.py"
        assert task_files[0]["link_created_at"] is not None
        assert task_files[0]["link_created_by"] is None  # Direct call, no context

        # Step 6: Update file metadata (line count change after refactoring)
        updated_file = update_entity(
            file_entity["id"],
            metadata={"language": "python", "line_count": 180, "complexity": "low"},
            workspace_path=test_workspace,
        )

        assert updated_file["id"] == file_entity["id"]
        assert updated_file["metadata"] == '{"language": "python", "line_count": 180, "complexity": "low"}'
        assert updated_file["updated_at"] != file_entity["updated_at"]

        # Step 7: Delete file (task completed, file no longer tracked)
        delete_result = delete_entity(file_entity["id"], test_workspace)

        assert delete_result["success"] is True
        assert delete_result["entity_id"] == file_entity["id"]
        assert delete_result["deleted_links"] == 1  # Link to refactor_task was deleted

        # Verify file no longer appears in lists
        all_files_after_delete = list_entities(
            entity_type="file",
            workspace_path=test_workspace,
        )
        assert len(all_files_after_delete) == 0

        # Verify file no longer appears in task entities
        task_files_after_delete = get_task_entities(
            refactor_task["id"],
            test_workspace,
        )
        assert len(task_files_after_delete) == 0

        # Step 8: Verify soft delete allows re-creation with same identifier
        recreated_file = create_entity(
            entity_type="file",
            name="Auth API Controller (v2)",
            identifier="/src/api/auth.py",  # Same identifier as deleted entity
            description="Refactored authentication using JWT",
            metadata={"language": "python", "line_count": 180, "complexity": "low"},
            tags="backend api authentication jwt",
            workspace_path=test_workspace,
        )

        assert recreated_file["id"] != file_entity["id"]  # New entity has different ID
        assert recreated_file["identifier"] == "/src/api/auth.py"  # Same identifier allowed
        assert recreated_file["name"] == "Auth API Controller (v2)"
        assert recreated_file["tags"] == "backend api authentication jwt"
        assert recreated_file["deleted_at"] is None

        # Verify recreated file appears in lists
        all_files_final = list_entities(
            entity_type="file",
            workspace_path=test_workspace,
        )
        assert len(all_files_final) == 1
        assert all_files_final[0]["id"] == recreated_file["id"]
