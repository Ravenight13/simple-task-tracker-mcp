"""Tests for workspace integrity audit functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from task_mcp.audit import (
    _check_description_paths,
    _check_entity_identifiers,
    _check_file_references,
    _check_suspicious_tags,
    _is_path_within,
    perform_workspace_audit,
)
from task_mcp.database import get_connection


@pytest.fixture
def temp_workspace() -> str:
    """Create temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def setup_test_db(temp_workspace: str) -> str:
    """Setup test database with sample tasks and entities."""
    conn = get_connection(temp_workspace)
    cursor = conn.cursor()

    # Insert test task with file references
    cursor.execute(
        """
        INSERT INTO tasks (
            title, description, file_references, tags, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        (
            "Test task",
            "See /other/workspace/file.py for details",
            json.dumps([f"{temp_workspace}/file1.py", "/other/workspace/file2.py"]),
            "test other-project",
            "todo",
        ),
    )

    # Insert entity with identifier
    cursor.execute(
        """
        INSERT INTO entities (
            entity_type, name, identifier, created_at, updated_at
        ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """,
        ("file", "Test File", "/other/workspace/src/test.py"),
    )

    conn.commit()
    conn.close()

    return temp_workspace


def test_is_path_within() -> None:
    """Test path containment check."""
    parent = Path("/home/user/project")
    child = Path("/home/user/project/src/file.py")
    other = Path("/home/user/other/file.py")

    assert _is_path_within(child, parent) is True
    assert _is_path_within(other, parent) is False


def test_check_file_references(setup_test_db: str) -> None:
    """Test file reference validation."""
    conn = get_connection(setup_test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")
    tasks = [dict(row) for row in cursor.fetchall()]

    report = {"issues": {"file_reference_mismatches": []}}
    _check_file_references(tasks, setup_test_db, report)

    assert len(report["issues"]["file_reference_mismatches"]) == 1
    assert (
        "/other/workspace/file2.py"
        in report["issues"]["file_reference_mismatches"][0]["file_references"]
    )

    conn.close()


def test_check_suspicious_tags(setup_test_db: str) -> None:
    """Test suspicious tag detection."""
    conn = get_connection(setup_test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")
    tasks = [dict(row) for row in cursor.fetchall()]

    report = {"issues": {"suspicious_tags": []}}
    _check_suspicious_tags(tasks, setup_test_db, report)

    assert len(report["issues"]["suspicious_tags"]) == 1
    assert "other-project" in report["issues"]["suspicious_tags"][0]["tags"]

    conn.close()


def test_check_description_paths(setup_test_db: str) -> None:
    """Test description path detection."""
    conn = get_connection(setup_test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")
    tasks = [dict(row) for row in cursor.fetchall()]

    report = {"issues": {"description_path_references": []}}
    _check_description_paths(tasks, setup_test_db, report)

    assert len(report["issues"]["description_path_references"]) == 1
    assert (
        "/other/workspace/file.py"
        in report["issues"]["description_path_references"][0]["detected_paths"]
    )

    conn.close()


def test_check_entity_identifiers(setup_test_db: str) -> None:
    """Test entity identifier validation."""
    conn = get_connection(setup_test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM entities")
    entities = [dict(row) for row in cursor.fetchall()]

    report = {"issues": {"entity_identifier_mismatches": []}}
    _check_entity_identifiers(entities, setup_test_db, report)

    assert len(report["issues"]["entity_identifier_mismatches"]) == 1
    assert (
        report["issues"]["entity_identifier_mismatches"][0]["identifier"]
        == "/other/workspace/src/test.py"
    )

    conn.close()


def test_full_audit(setup_test_db: str) -> None:
    """Test complete audit workflow."""
    report = perform_workspace_audit(
        workspace_path=setup_test_db,
        include_deleted=False,
        check_git_repo=False,  # Skip git checks in test
    )

    # Verify report structure
    assert "workspace_path" in report
    assert "audit_timestamp" in report
    assert "contamination_found" in report
    assert "issues" in report
    assert "statistics" in report
    assert "recommendations" in report

    # Verify contamination detected
    assert report["contamination_found"] is True

    # Verify statistics calculated
    assert report["statistics"]["contaminated_tasks"] >= 1
    assert report["statistics"]["contaminated_entities"] >= 1
    assert report["statistics"]["contamination_percentage"] > 0

    # Verify recommendations generated
    assert len(report["recommendations"]) > 0


def test_clean_workspace_audit(temp_workspace: str) -> None:
    """Test audit on clean workspace with no contamination."""
    conn = get_connection(temp_workspace)
    cursor = conn.cursor()

    # Insert clean task with valid file references
    cursor.execute(
        """
        INSERT INTO tasks (
            title, description, file_references, tags, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        (
            "Clean task",
            "This is a clean task",
            json.dumps([f"{temp_workspace}/src/file.py"]),
            "test clean",
            "todo",
        ),
    )

    conn.commit()
    conn.close()

    report = perform_workspace_audit(
        workspace_path=temp_workspace,
        include_deleted=False,
        check_git_repo=False,
    )

    # Verify no contamination found
    assert report["contamination_found"] is False
    assert report["statistics"]["contaminated_tasks"] == 0
    assert report["statistics"]["contaminated_entities"] == 0
    assert report["statistics"]["contamination_percentage"] == 0.0


def test_malformed_json_handling(temp_workspace: str) -> None:
    """Test that malformed JSON in file_references is handled gracefully."""
    conn = get_connection(temp_workspace)
    cursor = conn.cursor()

    # Insert task with malformed file_references
    cursor.execute(
        """
        INSERT INTO tasks (
            title, description, file_references, tags, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        ("Malformed task", "Test", "not valid json", "test", "todo"),
    )

    conn.commit()
    conn.close()

    # Should not crash on malformed JSON
    report = perform_workspace_audit(
        workspace_path=temp_workspace,
        include_deleted=False,
        check_git_repo=False,
    )

    assert "workspace_path" in report
    assert report["contamination_found"] is False


def test_entity_without_identifier(temp_workspace: str) -> None:
    """Test that entities without identifiers are handled correctly."""
    conn = get_connection(temp_workspace)
    cursor = conn.cursor()

    # Insert entity without identifier
    cursor.execute(
        """
        INSERT INTO entities (
            entity_type, name, identifier, created_at, updated_at
        ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """,
        ("other", "Test Entity", None),
    )

    conn.commit()
    conn.close()

    report = perform_workspace_audit(
        workspace_path=temp_workspace,
        include_deleted=False,
        check_git_repo=False,
    )

    # Should not find entity contamination for entities without identifiers
    assert len(report["issues"]["entity_identifier_mismatches"]) == 0


def test_include_deleted_parameter(setup_test_db: str) -> None:
    """Test that include_deleted parameter works correctly."""
    conn = get_connection(setup_test_db)
    cursor = conn.cursor()

    # Soft delete the test task
    cursor.execute("UPDATE tasks SET deleted_at = datetime('now') WHERE id = 1")
    conn.commit()
    conn.close()

    # Audit without deleted tasks
    report1 = perform_workspace_audit(
        workspace_path=setup_test_db,
        include_deleted=False,
        check_git_repo=False,
    )

    # Audit with deleted tasks
    report2 = perform_workspace_audit(
        workspace_path=setup_test_db,
        include_deleted=True,
        check_git_repo=False,
    )

    # Report without deleted should have no tasks
    assert report1["total_tasks"] == 0

    # Report with deleted should have the task
    assert report2["total_tasks"] == 1
    assert report2["contamination_found"] is True


def test_multiple_contamination_types(temp_workspace: str) -> None:
    """Test detection of multiple contamination types in single task."""
    conn = get_connection(temp_workspace)
    cursor = conn.cursor()

    # Insert task with multiple contamination issues
    cursor.execute(
        """
        INSERT INTO tasks (
            title, description, file_references, tags, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        (
            "Multi-issue task",
            "See /external/path/file.py and /another/external/doc.md",
            json.dumps(["/external/workspace/src/file.py"]),
            "test task-viewer other-project",
            "todo",
        ),
    )

    conn.commit()
    conn.close()

    report = perform_workspace_audit(
        workspace_path=temp_workspace,
        include_deleted=False,
        check_git_repo=False,
    )

    # Should detect file reference mismatch
    assert len(report["issues"]["file_reference_mismatches"]) == 1

    # Should detect suspicious tags
    assert len(report["issues"]["suspicious_tags"]) == 1

    # Should detect description paths
    assert len(report["issues"]["description_path_references"]) == 1

    # Statistics should count task only once
    assert report["statistics"]["contaminated_tasks"] == 1

    # Should have high severity issues
    assert report["statistics"]["high_severity_issues"] >= 1
