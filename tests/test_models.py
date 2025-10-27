"""Tests for Pydantic models and validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from task_mcp.models import (
    Task,
    TaskCreate,
    TaskUpdate,
    normalize_tags,
    validate_status_transition,
)


class TestTaskValidation:
    """Test Task model validation."""

    def test_description_max_length(self) -> None:
        """Test description length validation."""
        with pytest.raises(ValidationError, match="cannot exceed"):
            TaskCreate(title="Test", description="x" * 10001)

    def test_status_enum_validation(self) -> None:
        """Test status must be valid enum value."""
        with pytest.raises(ValidationError):
            TaskCreate(title="Test", status="invalid_status")

    def test_priority_enum_validation(self) -> None:
        """Test priority must be valid enum value."""
        with pytest.raises(ValidationError):
            TaskCreate(title="Test", priority="invalid_priority")

    def test_blocker_reason_required_when_blocked(self) -> None:
        """Test blocker_reason required for blocked status."""
        with pytest.raises(ValidationError, match="blocker_reason is required"):
            TaskCreate(title="Test", status="blocked")

    def test_blocker_reason_valid_when_provided(self) -> None:
        """Test blocked task with blocker_reason is valid."""
        task = TaskCreate(
            title="Test", status="blocked", blocker_reason="Waiting for API access"
        )
        assert task.status == "blocked"
        assert task.blocker_reason == "Waiting for API access"

    def test_depends_on_json_validation(self) -> None:
        """Test depends_on accepts list and converts to JSON."""
        task = TaskCreate(title="Test", depends_on="[1, 2, 3]")
        assert task.depends_on == "[1, 2, 3]"

        task2 = TaskCreate(title="Test")
        # Depends_on from list (via BeforeValidator)
        assert task2.depends_on is None

    def test_file_references_json_validation(self) -> None:
        """Test file_references accepts list and converts to JSON."""
        task = TaskCreate(title="Test", file_references='["file1.py", "file2.py"]')
        assert task.file_references == '["file1.py", "file2.py"]'

    def test_tags_normalization(self) -> None:
        """Test tags are normalized to lowercase with single spaces."""
        task = TaskCreate(title="Test", tags="  Python   Django  REST  ")
        assert task.tags == "python django rest"

    def test_default_values(self) -> None:
        """Test default status and priority."""
        task = TaskCreate(title="Test")
        assert task.status == "todo"
        assert task.priority == "medium"


class TestTaskHelperMethods:
    """Test Task helper methods."""

    def test_get_depends_on_list(self) -> None:
        """Test parsing depends_on JSON to list."""
        task = Task(id=1, title="Test", depends_on="[1, 2, 3]", status="todo")
        assert task.get_depends_on_list() == [1, 2, 3]

    def test_get_depends_on_list_empty(self) -> None:
        """Test parsing empty depends_on returns empty list."""
        task = Task(id=1, title="Test", status="todo")
        assert task.get_depends_on_list() == []

    def test_get_file_references_list(self) -> None:
        """Test parsing file_references JSON to list."""
        task = Task(
            id=1,
            title="Test",
            file_references='["file1.py", "file2.py"]',
            status="todo",
        )
        assert task.get_file_references_list() == ["file1.py", "file2.py"]

    def test_get_file_references_list_empty(self) -> None:
        """Test parsing empty file_references returns empty list."""
        task = Task(id=1, title="Test", status="todo")
        assert task.get_file_references_list() == []


class TestTagNormalization:
    """Test tag normalization helper."""

    def test_normalize_tags(self) -> None:
        """Test tag normalization."""
        assert normalize_tags("  Python   Django  ") == "python django"
        assert normalize_tags("REST API") == "rest api"
        assert normalize_tags("") == ""

    def test_normalize_tags_none(self) -> None:
        """Test normalize_tags with None input."""
        assert normalize_tags(None) == ""  # type: ignore[arg-type]


class TestStatusTransitions:
    """Test status transition validation."""

    def test_valid_transitions(self) -> None:
        """Test valid status transitions."""
        assert validate_status_transition("todo", "in_progress")
        assert validate_status_transition("in_progress", "done")
        assert validate_status_transition("blocked", "in_progress")

    def test_invalid_transitions(self) -> None:
        """Test invalid status transitions."""
        assert not validate_status_transition("done", "in_progress")
        assert not validate_status_transition("done", "todo")
        assert not validate_status_transition("cancelled", "todo")

    def test_same_status_allowed(self) -> None:
        """Test staying in same status is always valid."""
        assert validate_status_transition("todo", "todo")
        assert validate_status_transition("in_progress", "in_progress")
        assert validate_status_transition("done", "done")
        assert validate_status_transition("cancelled", "cancelled")


class TestTaskUpdate:
    """Test TaskUpdate model validation."""

    def test_partial_update(self) -> None:
        """Test TaskUpdate allows partial updates."""
        update = TaskUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.status is None
        assert update.priority is None

    def test_blocker_reason_validation_on_update(self) -> None:
        """Test blocker_reason required when updating status to blocked."""
        with pytest.raises(ValidationError, match="blocker_reason is required"):
            TaskUpdate(status="blocked")

    def test_blocker_reason_valid_on_update(self) -> None:
        """Test valid blocked status update."""
        update = TaskUpdate(status="blocked", blocker_reason="Waiting for review")
        assert update.status == "blocked"
        assert update.blocker_reason == "Waiting for review"
