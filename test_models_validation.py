#!/usr/bin/env python3
"""
Quick validation script to test the models.py implementation.
Run this to verify all validators work correctly.
"""

import sys

sys.path.insert(0, 'src')

import json
from datetime import datetime

from task_mcp.models import (
    VALID_PRIORITIES,
    VALID_STATUSES,
    ProjectInfo,
    Task,
    TaskCreate,
    TaskUpdate,
    normalize_tags,
    validate_status_transition,
)


def test_normalize_tags():
    """Test tag normalization."""
    print("Testing normalize_tags...")
    assert normalize_tags("  Python   Django  REST  ") == "python django rest"
    assert normalize_tags("API Backend") == "api backend"
    assert normalize_tags("") == ""
    print("  ✓ Tag normalization works correctly")


def test_status_transitions():
    """Test status transition validation."""
    print("\nTesting validate_status_transition...")

    # Valid transitions
    assert validate_status_transition("todo", "in_progress")
    assert validate_status_transition("in_progress", "done")
    assert validate_status_transition("blocked", "in_progress")

    # Invalid transitions (terminal states)
    assert not validate_status_transition("done", "in_progress")
    assert not validate_status_transition("cancelled", "todo")

    # Same status is allowed
    assert validate_status_transition("todo", "todo")

    print("  ✓ Status transitions work correctly")


def test_task_creation():
    """Test basic Task model creation."""
    print("\nTesting Task creation...")

    # Valid task
    task = Task(
        id=1,
        title="Test Task",
        description="A test description",
        status="todo",
        priority="high",
        tags="python testing"
    )
    assert task.id == 1
    assert task.title == "Test Task"
    assert task.status == "todo"
    assert task.tags == "python testing"  # Should be normalized
    print("  ✓ Basic task creation works")


def test_description_length_validation():
    """Test description length enforcement."""
    print("\nTesting description length validation...")

    # Valid description
    task = Task(title="Test", description="x" * 10000)
    assert len(task.description) == 10000

    # Invalid description (too long)
    try:
        task = Task(title="Test", description="x" * 10001)
        print("  ✗ Should have raised ValueError for description > 10000 chars")
        sys.exit(1)
    except ValueError as e:
        assert "cannot exceed 10000 characters" in str(e).lower()
        print("  ✓ Description length validation works")


def test_status_validation():
    """Test status enum validation."""
    print("\nTesting status validation...")

    # Valid statuses (skip 'blocked' since it requires blocker_reason)
    for status in VALID_STATUSES:
        if status == 'blocked':
            task = Task(title="Test", status=status, blocker_reason="Test blocker")
        else:
            task = Task(title="Test", status=status)
        assert task.status == status

    # Invalid status
    try:
        task = Task(title="Test", status="invalid_status")
        print("  ✗ Should have raised ValueError for invalid status")
        sys.exit(1)
    except ValueError as e:
        assert "status must be one of" in str(e).lower()
        print("  ✓ Status validation works")


def test_priority_validation():
    """Test priority enum validation."""
    print("\nTesting priority validation...")

    # Valid priorities
    for priority in VALID_PRIORITIES:
        task = Task(title="Test", priority=priority)
        assert task.priority == priority

    # Invalid priority
    try:
        task = Task(title="Test", priority="urgent")
        print("  ✗ Should have raised ValueError for invalid priority")
        sys.exit(1)
    except ValueError as e:
        assert "priority must be one of" in str(e).lower()
        print("  ✓ Priority validation works")


def test_blocker_reason_validation():
    """Test blocker_reason requirement when status is blocked."""
    print("\nTesting blocker_reason validation...")

    # Blocked status without blocker_reason should fail
    try:
        task = Task(title="Test", status="blocked")
        print("  ✗ Should have raised ValueError for blocked without blocker_reason")
        sys.exit(1)
    except ValueError as e:
        assert "blocker_reason is required" in str(e).lower()

    # Blocked status with blocker_reason should succeed
    task = Task(title="Test", status="blocked", blocker_reason="Waiting for API")
    assert task.blocker_reason == "Waiting for API"

    print("  ✓ Blocker reason validation works")


def test_depends_on_validation():
    """Test depends_on JSON validation."""
    print("\nTesting depends_on validation...")

    # Valid JSON string
    task = Task(title="Test", depends_on='[1, 2, 3]')
    assert task.depends_on == '[1, 2, 3]'
    assert task.get_depends_on_list() == [1, 2, 3]

    # Valid list (should convert to JSON)
    task = Task(title="Test", depends_on=[4, 5, 6])
    assert json.loads(task.depends_on) == [4, 5, 6]

    # Invalid JSON
    try:
        task = Task(title="Test", depends_on='not json')
        print("  ✗ Should have raised ValueError for invalid JSON")
        sys.exit(1)
    except ValueError as e:
        assert "must be valid json" in str(e).lower()

    # Invalid type in array
    try:
        task = Task(title="Test", depends_on='["string"]')
        print("  ✗ Should have raised ValueError for non-integer in depends_on")
        sys.exit(1)
    except ValueError as e:
        assert "must contain only integers" in str(e).lower()

    print("  ✓ depends_on validation works")


def test_file_references_validation():
    """Test file_references JSON validation."""
    print("\nTesting file_references validation...")

    # Valid JSON string
    task = Task(title="Test", file_references='["file1.py", "file2.py"]')
    assert task.file_references == '["file1.py", "file2.py"]'
    assert task.get_file_references_list() == ["file1.py", "file2.py"]

    # Valid list (should convert to JSON)
    task = Task(title="Test", file_references=["test.py", "main.py"])
    assert json.loads(task.file_references) == ["test.py", "main.py"]

    # Invalid type in array
    try:
        task = Task(title="Test", file_references='[123]')
        print("  ✗ Should have raised ValueError for non-string in file_references")
        sys.exit(1)
    except ValueError as e:
        assert "must contain only strings" in str(e).lower()

    print("  ✓ file_references validation works")


def test_tag_normalization():
    """Test automatic tag normalization."""
    print("\nTesting automatic tag normalization...")

    task = Task(title="Test", tags="  Python   Django  REST  ")
    assert task.tags == "python django rest"

    task = Task(title="Test", tags="API Backend")
    assert task.tags == "api backend"

    print("  ✓ Automatic tag normalization works")


def test_task_create_model():
    """Test TaskCreate model."""
    print("\nTesting TaskCreate model...")

    task_create = TaskCreate(
        title="New Task",
        description="Test description",
        tags="test python",
        status="blocked",
        blocker_reason="Waiting for approval"
    )
    assert task_create.title == "New Task"
    assert task_create.tags == "test python"
    assert task_create.status == "blocked"
    assert task_create.blocker_reason == "Waiting for approval"

    print("  ✓ TaskCreate model works")


def test_task_update_model():
    """Test TaskUpdate model."""
    print("\nTesting TaskUpdate model...")

    # Update with optional fields
    task_update = TaskUpdate(
        status="in_progress",
        priority="high"
    )
    assert task_update.status == "in_progress"
    assert task_update.priority == "high"
    assert task_update.title is None  # Optional field

    # Update to blocked must include blocker_reason
    try:
        task_update = TaskUpdate(status="blocked")
        print("  ✗ Should have raised ValueError for blocked without blocker_reason")
        sys.exit(1)
    except ValueError as e:
        assert "blocker_reason is required" in str(e).lower()

    print("  ✓ TaskUpdate model works")


def test_project_info_model():
    """Test ProjectInfo model."""
    print("\nTesting ProjectInfo model...")

    project = ProjectInfo(
        id="abc12345",
        workspace_path="/home/user/project",
        friendly_name="My Project",
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow()
    )
    assert project.id == "abc12345"
    assert project.workspace_path == "/home/user/project"

    # Test workspace path validation (must be absolute)
    try:
        project = ProjectInfo(
            id="abc12345",
            workspace_path="relative/path",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )
        print("  ✗ Should have raised ValueError for relative path")
        sys.exit(1)
    except ValueError as e:
        assert "must be an absolute path" in str(e).lower()

    print("  ✓ ProjectInfo model works")


def test_completed_at_auto_set():
    """Test automatic completed_at timestamp."""
    print("\nTesting auto-set completed_at...")

    task = Task(title="Test", status="done")
    assert task.completed_at is not None
    assert isinstance(task.completed_at, datetime)

    task = Task(title="Test", status="todo")
    assert task.completed_at is None

    print("  ✓ Auto-set completed_at works")


def main():
    """Run all tests."""
    print("=" * 60)
    print("PYDANTIC V2 MODELS VALIDATION TEST SUITE")
    print("=" * 60)

    try:
        test_normalize_tags()
        test_status_transitions()
        test_task_creation()
        test_description_length_validation()
        test_status_validation()
        test_priority_validation()
        test_blocker_reason_validation()
        test_depends_on_validation()
        test_file_references_validation()
        test_tag_normalization()
        test_task_create_model()
        test_task_update_model()
        test_project_info_model()
        test_completed_at_auto_set()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
