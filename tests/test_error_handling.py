"""
Comprehensive tests for MCP error codes and structured error response format.

This test suite validates that all MCP tools return properly formatted error
responses with correct error codes, messages, and details for various error scenarios.
"""

import json
import tempfile
from pathlib import Path

import pytest

from task_mcp import server
from task_mcp.errors import (
    InvalidModeError,
    PaginationError,
    ResponseSizeExceededError,
)

# Extract underlying functions from FastMCP FunctionTool wrappers
create_task = server.create_task.fn
list_tasks = server.list_tasks.fn
search_tasks = server.search_tasks.fn
create_entity = server.create_entity.fn
list_entities = server.list_entities.fn
search_entities = server.search_entities.fn
get_task_entities = server.get_task_entities.fn
get_entity_tasks = server.get_entity_tasks.fn
get_task_tree = server.get_task_tree.fn


@pytest.fixture
def workspace_path():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestErrorResponseFormat:
    """Test proper error response format with code, message, and details."""

    def test_pagination_error_response_format(self):
        """Verify pagination error has proper response format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test invalid limit (too high)
            response = list_tasks(workspace_path=tmpdir, limit=2000)

            assert isinstance(response, dict)
            assert "error" in response
            error = response["error"]

            # Verify error structure
            assert "code" in error
            assert "message" in error
            assert "details" in error

            # Verify error code
            assert error["code"] == "PAGINATION_INVALID"

            # Verify message is descriptive
            assert "limit" in error["message"].lower()
            assert "2000" in error["message"]

            # Verify details contain context
            assert isinstance(error["details"], dict)

    def test_pagination_invalid_offset(self):
        """Test pagination error for invalid offset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test negative offset
            response = list_tasks(workspace_path=tmpdir, offset=-1)

            assert isinstance(response, dict)
            assert "error" in response
            error = response["error"]

            assert error["code"] == "PAGINATION_INVALID"
            assert "offset" in error["message"].lower()
            assert "-1" in error["message"]

    def test_invalid_mode_error_response(self):
        """Verify invalid mode error has proper structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test invalid mode
            response = list_tasks(workspace_path=tmpdir, mode="invalid_mode")

            assert isinstance(response, dict)
            assert "error" in response
            error = response["error"]

            # Verify error structure
            assert error["code"] == "INVALID_MODE"
            assert "invalid_mode" in error["message"]
            assert "summary" in error["message"]
            assert "details" in error["message"]

    def test_invalid_mode_in_search_tasks(self):
        """Test invalid mode error in search_tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            response = search_tasks(
                search_term="test",
                workspace_path=tmpdir,
                mode="full"
            )

            assert isinstance(response, dict)
            assert "error" in response
            assert response["error"]["code"] == "INVALID_MODE"

    def test_invalid_mode_in_get_task_tree(self):
        """Test invalid mode error in get_task_tree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a task first
            task = create_task(
                title="Test Task",
                workspace_path=tmpdir
            )

            response = get_task_tree(
                task_id=task["id"],
                workspace_path=tmpdir,
                mode="full"
            )

            assert isinstance(response, dict)
            assert "error" in response
            assert response["error"]["code"] == "INVALID_MODE"

    def test_invalid_mode_in_list_entities(self):
        """Test invalid mode error in list_entities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            response = list_entities(
                workspace_path=tmpdir,
                mode="bad_mode"
            )

            assert isinstance(response, dict)
            assert "error" in response
            assert response["error"]["code"] == "INVALID_MODE"

    def test_invalid_mode_in_search_entities(self):
        """Test invalid mode error in search_entities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            response = search_entities(
                search_term="test",
                workspace_path=tmpdir,
                mode="invalid"
            )

            assert isinstance(response, dict)
            assert "error" in response
            assert response["error"]["code"] == "INVALID_MODE"

    def test_invalid_mode_in_get_task_entities(self):
        """Test invalid mode error in get_task_entities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a task
            task = create_task(title="Test", workspace_path=tmpdir)

            response = get_task_entities(
                task_id=task["id"],
                workspace_path=tmpdir,
                mode="invalid"
            )

            assert isinstance(response, dict)
            assert "error" in response
            assert response["error"]["code"] == "INVALID_MODE"

    def test_invalid_mode_in_get_entity_tasks(self):
        """Test invalid mode error in get_entity_tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create entity using the module-level function
            entity = create_entity(
                entity_type="file",
                name="test.py",
                workspace_path=tmpdir
            )

            response = get_entity_tasks(
                entity_id=entity["id"],
                workspace_path=tmpdir,
                mode="invalid"
            )

            assert isinstance(response, dict)
            assert "error" in response
            assert response["error"]["code"] == "INVALID_MODE"


class TestErrorResponseStructure:
    """Test error response structure compliance."""

    def test_error_response_always_dict(self):
        """Verify error responses are always dicts, not exceptions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Invalid pagination
            response = list_tasks(workspace_path=tmpdir, limit=-5)

            # Should return dict, not raise exception
            assert isinstance(response, dict)
            assert "error" in response

    def test_error_dict_has_required_fields(self):
        """Verify error dict has code, message, and details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            response = list_tasks(workspace_path=tmpdir, mode="invalid")

            assert "error" in response
            error = response["error"]

            # Check required fields
            assert "code" in error, "Error missing 'code' field"
            assert "message" in error, "Error missing 'message' field"
            assert "details" in error, "Error missing 'details' field"

            # Check types
            assert isinstance(error["code"], str)
            assert isinstance(error["message"], str)
            assert isinstance(error["details"], dict)

    def test_error_code_is_known(self):
        """Verify error codes are from known set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            known_codes = {
                "PAGINATION_INVALID",
                "INVALID_MODE",
                "RESPONSE_SIZE_EXCEEDED",
                "NOT_FOUND",
                "INVALID_FILTER",
            }

            # Generate various error scenarios
            errors = []

            # Pagination error
            response = list_tasks(workspace_path=tmpdir, limit=2000)
            if "error" in response:
                errors.append(response["error"])

            # Invalid mode error
            response = list_tasks(workspace_path=tmpdir, mode="bad")
            if "error" in response:
                errors.append(response["error"])

            # Verify all error codes are known
            for error in errors:
                assert error["code"] in known_codes, f"Unknown error code: {error['code']}"


class TestListTasksErrors:
    """Test error handling in list_tasks tool."""

    def test_list_tasks_pagination_validation(self):
        """Test list_tasks validates pagination parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Limit too high
            response = list_tasks(workspace_path=tmpdir, limit=1001)
            assert "error" in response
            assert response["error"]["code"] == "PAGINATION_INVALID"

            # Limit too low
            response = list_tasks(workspace_path=tmpdir, limit=0)
            assert "error" in response
            assert response["error"]["code"] == "PAGINATION_INVALID"

            # Negative offset
            response = list_tasks(workspace_path=tmpdir, offset=-5)
            assert "error" in response
            assert response["error"]["code"] == "PAGINATION_INVALID"

    def test_list_tasks_mode_validation(self):
        """Test list_tasks validates mode parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            response = list_tasks(workspace_path=tmpdir, mode="full")
            assert "error" in response
            assert response["error"]["code"] == "INVALID_MODE"

    def test_list_tasks_success_structure(self):
        """Test successful list_tasks response structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a task
            create_task(title="Test", workspace_path=tmpdir)

            # Valid request
            response = list_tasks(workspace_path=tmpdir)

            # Should not have error key
            assert "error" not in response
            assert "items" in response
            assert "total_count" in response


class TestSearchTasksErrors:
    """Test error handling in search_tasks tool."""

    def test_search_tasks_pagination_validation(self):
        """Test search_tasks validates pagination parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            response = search_tasks(
                search_term="test",
                workspace_path=tmpdir,
                limit=2000
            )
            assert "error" in response
            assert response["error"]["code"] == "PAGINATION_INVALID"

    def test_search_tasks_mode_validation(self):
        """Test search_tasks validates mode parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            response = search_tasks(
                search_term="test",
                workspace_path=tmpdir,
                mode="full"
            )
            assert "error" in response
            assert response["error"]["code"] == "INVALID_MODE"


class TestEntityListingErrors:
    """Test error handling in entity listing tools."""

    def test_list_entities_pagination_validation(self):
        """Test list_entities validates pagination parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            response = list_entities(workspace_path=tmpdir, limit=-1)
            assert "error" in response
            assert response["error"]["code"] == "PAGINATION_INVALID"

    def test_list_entities_mode_validation(self):
        """Test list_entities validates mode parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            response = list_entities(workspace_path=tmpdir, mode="wrong")
            assert "error" in response
            assert response["error"]["code"] == "INVALID_MODE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
