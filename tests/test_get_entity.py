"""Test get_entity MCP tool implementation."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

# Import MCP tool wrappers and extract underlying functions
from task_mcp import server

# Extract underlying functions from FastMCP FunctionTool wrappers
get_entity = server.get_entity.fn
create_entity = server.create_entity.fn if hasattr(server, "create_entity") else None
delete_entity = server.delete_entity.fn if hasattr(server, "delete_entity") else None


@pytest.fixture
def test_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[str, None, None]:
    """Create isolated test workspace."""
    workspace = str(tmp_path / "test-project")
    Path(workspace).mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    yield workspace


class TestGetEntity:
    """Test get_entity tool."""

    def test_get_entity_not_found(self, test_workspace: str) -> None:
        """Test getting non-existent entity raises ValueError."""
        with pytest.raises(ValueError, match="Entity 999 not found or has been deleted"):
            get_entity(entity_id=999, workspace_path=test_workspace)

    @pytest.mark.skipif(create_entity is None, reason="create_entity not implemented yet")
    def test_get_entity_success(self, test_workspace: str) -> None:
        """Test successful entity retrieval."""
        # Create entity
        entity = create_entity(
            entity_type="file",
            name="Test File",
            identifier="/test.py",
            workspace_path=test_workspace,
        )

        # Retrieve entity
        retrieved = get_entity(entity_id=entity["id"], workspace_path=test_workspace)

        assert retrieved["id"] == entity["id"]
        assert retrieved["name"] == "Test File"
        assert retrieved["identifier"] == "/test.py"
        assert retrieved["entity_type"] == "file"
        assert retrieved["deleted_at"] is None

    @pytest.mark.skipif(
        create_entity is None or delete_entity is None,
        reason="create_entity or delete_entity not implemented yet",
    )
    def test_get_entity_soft_deleted(self, test_workspace: str) -> None:
        """Test getting soft-deleted entity raises ValueError."""
        # Create entity
        entity = create_entity(
            entity_type="file",
            name="Test File",
            identifier="/test.py",
            workspace_path=test_workspace,
        )

        # Soft delete entity
        delete_entity(entity_id=entity["id"], workspace_path=test_workspace)

        # Verify get_entity raises ValueError
        with pytest.raises(ValueError, match="deleted"):
            get_entity(entity_id=entity["id"], workspace_path=test_workspace)
