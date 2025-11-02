"""Tests for workspace integrity audit functionality.

Type-safe test suite following TDD approach - these tests will fail until audit.py is implemented.
Tests validate all 5 contamination detection types and full audit workflow.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# NOTE: These imports will fail until audit.py is created
# This is intentional TDD - we define the API through tests first
from task_mcp.audit import (
    _calculate_statistics,
    _check_description_paths,
    _check_entity_identifiers,
    _check_file_references,
    _check_git_consistency,
    _check_suspicious_tags,
    _find_git_root,
    _generate_recommendations,
    _is_path_within,
    perform_workspace_audit,
)
from task_mcp.database import get_connection


class TestPathContainmentHelper:
    """Test helper function for path containment checking."""

    def test_is_path_within_child_inside_parent(self) -> None:
        """Test path is correctly identified as inside parent."""
        parent = Path("/home/user/project")
        child = Path("/home/user/project/src/file.py")

        assert _is_path_within(child, parent) is True

    def test_is_path_within_child_outside_parent(self) -> None:
        """Test path is correctly identified as outside parent."""
        parent = Path("/home/user/project")
        other = Path("/home/user/other-project/file.py")

        assert _is_path_within(other, parent) is False

    def test_is_path_within_same_path(self) -> None:
        """Test path is within itself."""
        path = Path("/home/user/project")

        assert _is_path_within(path, path) is True

    def test_is_path_within_parent_is_child(self) -> None:
        """Test parent path is not within child."""
        parent = Path("/home/user")
        child = Path("/home/user/project")

        assert _is_path_within(parent, child) is False

    def test_is_path_within_relative_paths_resolved(self) -> None:
        """Test relative paths are properly resolved before comparison."""
        parent = Path.cwd()
        child = Path("./subdir/file.py").resolve()

        result = _is_path_within(child, parent)
        assert isinstance(result, bool)  # Should not raise exception


class TestFileReferenceValidation:
    """Test file reference contamination detection."""

    @pytest.fixture
    def temp_workspace(self, tmp_path: Path) -> Generator[str, None, None]:
        """Create temporary workspace for testing."""
        workspace = str(tmp_path / "test-workspace")
        Path(workspace).mkdir()
        yield workspace

    @pytest.fixture
    def setup_contaminated_db(
        self, temp_workspace: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Generator[str, None, None]:
        """Setup test database with contaminated file references."""
        # Point to temp directory for databases
        test_home = tmp_path / ".task-mcp"
        test_home.mkdir()
        monkeypatch.setenv("HOME", str(tmp_path))

        conn = get_connection(temp_workspace)
        cursor = conn.cursor()

        # Insert task with mixed file references (some inside, some outside workspace)
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, file_references, tags, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                "Test task with external refs",
                "Task description",
                json.dumps([
                    f"{temp_workspace}/internal/file1.py",
                    "/other/workspace/external/file2.py",
                    "/completely/different/path/file3.py",
                ]),
                "test",
                "todo",
            ),
        )

        # Insert task with all internal file references
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, file_references, tags, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                "Clean task",
                "No external references",
                json.dumps([
                    f"{temp_workspace}/src/auth.py",
                    f"{temp_workspace}/tests/test_auth.py",
                ]),
                "clean",
                "todo",
            ),
        )

        # Insert task with malformed JSON (should be handled gracefully)
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, file_references, tags, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                "Malformed task",
                "Bad JSON",
                "not-valid-json",
                "malformed",
                "todo",
            ),
        )

        conn.commit()
        conn.close()

        yield temp_workspace

    def test_check_file_references_detects_external_paths(
        self, setup_contaminated_db: str
    ) -> None:
        """Test file reference validation detects paths outside workspace."""
        conn = get_connection(setup_contaminated_db)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE deleted_at IS NULL")
        tasks = [dict(row) for row in cursor.fetchall()]

        report: dict[str, Any] = {"issues": {"file_reference_mismatches": []}}
        _check_file_references(tasks, setup_contaminated_db, report)

        # Should find exactly 1 task with external references
        assert len(report["issues"]["file_reference_mismatches"]) == 1

        issue = report["issues"]["file_reference_mismatches"][0]
        assert issue["task_title"] == "Test task with external refs"
        assert "/other/workspace/external/file2.py" in issue["file_references"]
        assert "/completely/different/path/file3.py" in issue["file_references"]
        assert issue["severity"] == "high"
        assert "expected_prefix" in issue

        conn.close()

    def test_check_file_references_handles_malformed_json(
        self, setup_contaminated_db: str
    ) -> None:
        """Test file reference validation handles malformed JSON gracefully."""
        conn = get_connection(setup_contaminated_db)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE deleted_at IS NULL")
        tasks = [dict(row) for row in cursor.fetchall()]

        report: dict[str, Any] = {"issues": {"file_reference_mismatches": []}}

        # Should not raise exception on malformed JSON
        _check_file_references(tasks, setup_contaminated_db, report)

        # Malformed task should be skipped silently
        assert isinstance(report["issues"]["file_reference_mismatches"], list)

        conn.close()

    def test_check_file_references_empty_workspace(
        self, temp_workspace: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test file reference validation with empty workspace (no tasks)."""
        # Point to temp directory for databases
        test_home = tmp_path / ".task-mcp"
        test_home.mkdir()
        monkeypatch.setenv("HOME", str(tmp_path))

        conn = get_connection(temp_workspace)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE deleted_at IS NULL")
        tasks = [dict(row) for row in cursor.fetchall()]

        report: dict[str, Any] = {"issues": {"file_reference_mismatches": []}}
        _check_file_references(tasks, temp_workspace, report)

        # Should return empty list for empty workspace
        assert len(report["issues"]["file_reference_mismatches"]) == 0

        conn.close()


class TestSuspiciousTagDetection:
    """Test suspicious tag pattern detection."""

    @pytest.fixture
    def temp_workspace(self, tmp_path: Path) -> Generator[str, None, None]:
        """Create temporary workspace for testing."""
        workspace = str(tmp_path / "test-workspace")
        Path(workspace).mkdir()
        yield workspace

    @pytest.fixture
    def setup_tagged_db(
        self, temp_workspace: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Generator[str, None, None]:
        """Setup test database with suspicious tags."""
        # Point to temp directory for databases
        test_home = tmp_path / ".task-mcp"
        test_home.mkdir()
        monkeypatch.setenv("HOME", str(tmp_path))

        conn = get_connection(temp_workspace)
        cursor = conn.cursor()

        # Task with suspicious "other-project" tag
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, tags, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("Task from other project", "Description", "test other-project backend", "todo"),
        )

        # Task with "task-viewer" tag (known separate project)
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, tags, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("Task viewer feature", "Description", "frontend task-viewer", "todo"),
        )

        # Task with clean tags (should not be flagged)
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, tags, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("Clean task", "Description", "task-mcp backend testing", "todo"),
        )

        # Task with no tags
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, tags, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("No tags task", "Description", None, "todo"),
        )

        conn.commit()
        conn.close()

        yield temp_workspace

    def test_check_suspicious_tags_detects_patterns(
        self, setup_tagged_db: str
    ) -> None:
        """Test suspicious tag detection for known patterns."""
        conn = get_connection(setup_tagged_db)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE deleted_at IS NULL")
        tasks = [dict(row) for row in cursor.fetchall()]

        report: dict[str, Any] = {"issues": {"suspicious_tags": []}}
        _check_suspicious_tags(tasks, setup_tagged_db, report)

        # Should detect 2 tasks with suspicious tags
        assert len(report["issues"]["suspicious_tags"]) == 2

        # Verify other-project detected
        other_project_issues = [
            i for i in report["issues"]["suspicious_tags"]
            if "other-project" in i["tags"]
        ]
        assert len(other_project_issues) == 1
        assert other_project_issues[0]["severity"] == "medium"

        # Verify task-viewer detected
        task_viewer_issues = [
            i for i in report["issues"]["suspicious_tags"]
            if "task-viewer" in i["tags"]
        ]
        assert len(task_viewer_issues) == 1

        conn.close()

    def test_check_suspicious_tags_ignores_clean_tags(
        self, setup_tagged_db: str
    ) -> None:
        """Test suspicious tag detection ignores legitimate tags."""
        conn = get_connection(setup_tagged_db)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE title = 'Clean task'")
        tasks = [dict(row) for row in cursor.fetchall()]

        report: dict[str, Any] = {"issues": {"suspicious_tags": []}}
        _check_suspicious_tags(tasks, setup_tagged_db, report)

        # Should not flag legitimate task-mcp tag
        assert len(report["issues"]["suspicious_tags"]) == 0

        conn.close()


class TestDescriptionPathDetection:
    """Test description path reference detection."""

    @pytest.fixture
    def temp_workspace(self, tmp_path: Path) -> Generator[str, None, None]:
        """Create temporary workspace for testing."""
        workspace = str(tmp_path / "test-workspace")
        Path(workspace).mkdir()
        yield workspace

    @pytest.fixture
    def setup_description_db(
        self, temp_workspace: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Generator[str, None, None]:
        """Setup test database with path references in descriptions."""
        # Point to temp directory for databases
        test_home = tmp_path / ".task-mcp"
        test_home.mkdir()
        monkeypatch.setenv("HOME", str(tmp_path))

        conn = get_connection(temp_workspace)
        cursor = conn.cursor()

        # Task with external path in description
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                "Task with path reference",
                "See /other/workspace/docs/design.md for details. "
                "Also check /another/path/file.py for implementation.",
                "todo",
            ),
        )

        # Task with internal path (should not be flagged)
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                "Task with internal path",
                f"Refer to {temp_workspace}/docs/internal.md for context.",
                "todo",
            ),
        )

        # Task with no paths in description
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("Clean description task", "Just a regular description with no paths.", "todo"),
        )

        conn.commit()
        conn.close()

        yield temp_workspace

    def test_check_description_paths_detects_external_paths(
        self, setup_description_db: str
    ) -> None:
        """Test description path detection finds external absolute paths."""
        conn = get_connection(setup_description_db)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE deleted_at IS NULL")
        tasks = [dict(row) for row in cursor.fetchall()]

        report: dict[str, Any] = {"issues": {"description_path_references": []}}
        _check_description_paths(tasks, setup_description_db, report)

        # Should detect 1 task with external paths
        assert len(report["issues"]["description_path_references"]) == 1

        issue = report["issues"]["description_path_references"][0]
        assert issue["task_title"] == "Task with path reference"
        assert "/other/workspace/docs/design.md" in issue["detected_paths"]
        assert "/another/path/file.py" in issue["detected_paths"]
        assert issue["severity"] == "low"
        assert "description_excerpt" in issue

        conn.close()

    def test_check_description_paths_ignores_internal_paths(
        self, setup_description_db: str
    ) -> None:
        """Test description path detection ignores workspace-internal paths."""
        conn = get_connection(setup_description_db)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE title = 'Task with internal path'")
        tasks = [dict(row) for row in cursor.fetchall()]

        report: dict[str, Any] = {"issues": {"description_path_references": []}}
        _check_description_paths(tasks, setup_description_db, report)

        # Should not flag internal paths
        assert len(report["issues"]["description_path_references"]) == 0

        conn.close()


class TestEntityIdentifierValidation:
    """Test entity identifier contamination detection."""

    @pytest.fixture
    def temp_workspace(self, tmp_path: Path) -> Generator[str, None, None]:
        """Create temporary workspace for testing."""
        workspace = str(tmp_path / "test-workspace")
        Path(workspace).mkdir()
        yield workspace

    @pytest.fixture
    def setup_entity_db(
        self, temp_workspace: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Generator[str, None, None]:
        """Setup test database with entity identifiers."""
        # Point to temp directory for databases
        test_home = tmp_path / ".task-mcp"
        test_home.mkdir()
        monkeypatch.setenv("HOME", str(tmp_path))

        conn = get_connection(temp_workspace)
        cursor = conn.cursor()

        # File entity with external path identifier
        cursor.execute(
            """
            INSERT INTO entities (
                entity_type, name, identifier, created_at, updated_at
            ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("file", "External File", "/other/workspace/src/external.py"),
        )

        # File entity with internal path identifier
        cursor.execute(
            """
            INSERT INTO entities (
                entity_type, name, identifier, created_at, updated_at
            ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("file", "Internal File", f"{temp_workspace}/src/internal.py"),
        )

        # Non-file entity with code identifier (should be skipped)
        cursor.execute(
            """
            INSERT INTO entities (
                entity_type, name, identifier, created_at, updated_at
            ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("other", "Vendor Entity", "ABC-INS"),
        )

        # File entity with no identifier (should be skipped)
        cursor.execute(
            """
            INSERT INTO entities (
                entity_type, name, identifier, created_at, updated_at
            ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("file", "No Identifier", None),
        )

        conn.commit()
        conn.close()

        yield temp_workspace

    def test_check_entity_identifiers_detects_external_paths(
        self, setup_entity_db: str
    ) -> None:
        """Test entity identifier validation detects external paths."""
        conn = get_connection(setup_entity_db)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM entities WHERE deleted_at IS NULL")
        entities = [dict(row) for row in cursor.fetchall()]

        report: dict[str, Any] = {"issues": {"entity_identifier_mismatches": []}}
        _check_entity_identifiers(entities, setup_entity_db, report)

        # Should detect 1 entity with external identifier
        assert len(report["issues"]["entity_identifier_mismatches"]) == 1

        issue = report["issues"]["entity_identifier_mismatches"][0]
        assert issue["entity_type"] == "file"
        assert issue["name"] == "External File"
        assert issue["identifier"] == "/other/workspace/src/external.py"
        assert issue["severity"] == "high"
        assert "expected_prefix" in issue

        conn.close()

    def test_check_entity_identifiers_ignores_non_path_identifiers(
        self, setup_entity_db: str
    ) -> None:
        """Test entity identifier validation skips non-path identifiers."""
        conn = get_connection(setup_entity_db)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM entities WHERE identifier = 'ABC-INS'")
        entities = [dict(row) for row in cursor.fetchall()]

        report: dict[str, Any] = {"issues": {"entity_identifier_mismatches": []}}
        _check_entity_identifiers(entities, setup_entity_db, report)

        # Should not flag non-path identifiers
        assert len(report["issues"]["entity_identifier_mismatches"]) == 0

        conn.close()


class TestGitConsistencyCheck:
    """Test git repository consistency validation."""

    @pytest.fixture
    def temp_workspace(self, tmp_path: Path) -> Generator[str, None, None]:
        """Create temporary workspace for testing."""
        workspace = str(tmp_path / "test-workspace")
        Path(workspace).mkdir()
        yield workspace

    def test_find_git_root_returns_root_path(self) -> None:
        """Test _find_git_root returns git repository root."""
        # Use current repository for testing
        current_repo_root = _find_git_root(str(Path.cwd()))

        # Should return a path if in a git repo
        assert isinstance(current_repo_root, (str, type(None)))

        if current_repo_root is not None:
            assert Path(current_repo_root).exists()
            assert (Path(current_repo_root) / ".git").exists()

    def test_find_git_root_returns_none_for_non_repo(self, tmp_path: Path) -> None:
        """Test _find_git_root returns None for non-git directory."""
        non_repo_path = tmp_path / "not-a-repo"
        non_repo_path.mkdir()

        result = _find_git_root(str(non_repo_path))
        assert result is None

    @patch("task_mcp.audit.subprocess.run")
    def test_check_git_consistency_handles_subprocess_timeout(
        self, mock_run: MagicMock, temp_workspace: str
    ) -> None:
        """Test git consistency check handles subprocess timeouts gracefully."""
        # Simulate timeout exception
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=2)

        report: dict[str, Any] = {"issues": {"git_repo_mismatches": []}}

        # Should not raise exception
        git_info = _check_git_consistency([], [], temp_workspace, report)

        assert isinstance(git_info, dict)
        assert "git_repo_detected" in git_info

    @patch("task_mcp.audit.subprocess.run")
    def test_check_git_consistency_handles_git_not_installed(
        self, mock_run: MagicMock, temp_workspace: str
    ) -> None:
        """Test git consistency check handles missing git binary."""
        # Simulate FileNotFoundError when git is not installed
        mock_run.side_effect = FileNotFoundError("git not found")

        report: dict[str, Any] = {"issues": {"git_repo_mismatches": []}}

        # Should handle gracefully without crashing
        git_info = _check_git_consistency([], [], temp_workspace, report)

        assert isinstance(git_info, dict)
        assert git_info["git_repo_detected"] is False


class TestStatisticsCalculation:
    """Test audit statistics calculation."""

    def test_calculate_statistics_counts_unique_tasks(self) -> None:
        """Test statistics calculation counts unique contaminated tasks."""
        report: dict[str, Any] = {
            "total_tasks": 10,
            "total_entities": 5,
            "issues": {
                "file_reference_mismatches": [
                    {"task_id": 1, "severity": "high"},
                    {"task_id": 2, "severity": "high"},
                ],
                "suspicious_tags": [
                    {"task_id": 1, "severity": "medium"},  # Same task as above
                ],
                "description_path_references": [
                    {"task_id": 3, "severity": "low"},
                ],
                "entity_identifier_mismatches": [
                    {"entity_id": 1, "severity": "high"},
                ],
                "git_repo_mismatches": [],
            },
            "statistics": {},
        }

        _calculate_statistics(report)

        # Should count unique task IDs: 1, 2, 3 = 3 tasks
        assert report["statistics"]["contaminated_tasks"] == 3
        assert report["statistics"]["contaminated_entities"] == 1
        assert report["statistics"]["contamination_percentage"] == 26.7  # 4/15 * 100

        # Severity counts
        assert report["statistics"]["high_severity_issues"] == 3
        assert report["statistics"]["medium_severity_issues"] == 1
        assert report["statistics"]["low_severity_issues"] == 1

    def test_calculate_statistics_empty_issues(self) -> None:
        """Test statistics calculation with no issues found."""
        report: dict[str, Any] = {
            "total_tasks": 10,
            "total_entities": 5,
            "issues": {
                "file_reference_mismatches": [],
                "suspicious_tags": [],
                "description_path_references": [],
                "entity_identifier_mismatches": [],
                "git_repo_mismatches": [],
            },
            "statistics": {},
        }

        _calculate_statistics(report)

        assert report["statistics"]["contaminated_tasks"] == 0
        assert report["statistics"]["contaminated_entities"] == 0
        assert report["statistics"]["contamination_percentage"] == 0.0
        assert report["statistics"]["high_severity_issues"] == 0
        assert report["statistics"]["medium_severity_issues"] == 0
        assert report["statistics"]["low_severity_issues"] == 0


class TestRecommendationsGeneration:
    """Test actionable recommendations generation."""

    def test_generate_recommendations_with_issues(self) -> None:
        """Test recommendations generation with contamination detected."""
        report: dict[str, Any] = {
            "issues": {
                "file_reference_mismatches": [{"task_id": 1}, {"task_id": 2}],
                "entity_identifier_mismatches": [{"entity_id": 1}],
                "suspicious_tags": [{"task_id": 3}],
                "git_repo_mismatches": [{"task_id": 4}],
                "description_path_references": [{"task_id": 5}],
            },
            "recommendations": [],
        }

        _generate_recommendations(report)

        assert len(report["recommendations"]) > 0

        # Should have specific recommendations for each issue type
        recommendations_text = " ".join(report["recommendations"])
        assert "2 task(s)" in recommendations_text or "task" in recommendations_text
        assert "1 entity" in recommendations_text or "entity" in recommendations_text
        assert "cleanup" in recommendations_text.lower() or "resolve" in recommendations_text.lower()

    def test_generate_recommendations_no_issues(self) -> None:
        """Test recommendations generation with clean workspace."""
        report: dict[str, Any] = {
            "issues": {
                "file_reference_mismatches": [],
                "entity_identifier_mismatches": [],
                "suspicious_tags": [],
                "git_repo_mismatches": [],
                "description_path_references": [],
            },
            "recommendations": [],
        }

        _generate_recommendations(report)

        assert len(report["recommendations"]) > 0
        recommendations_text = " ".join(report["recommendations"])
        assert "no contamination" in recommendations_text.lower() or "good" in recommendations_text.lower()


class TestFullAuditWorkflow:
    """Integration tests for complete audit workflow."""

    @pytest.fixture
    def temp_workspace(self, tmp_path: Path) -> Generator[str, None, None]:
        """Create temporary workspace for testing."""
        workspace = str(tmp_path / "test-workspace")
        Path(workspace).mkdir()
        yield workspace

    @pytest.fixture
    def setup_contaminated_workspace(
        self, temp_workspace: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Generator[str, None, None]:
        """Setup fully contaminated workspace for integration testing."""
        # Point to temp directory for databases
        test_home = tmp_path / ".task-mcp"
        test_home.mkdir()
        monkeypatch.setenv("HOME", str(tmp_path))

        conn = get_connection(temp_workspace)
        cursor = conn.cursor()

        # Insert contaminated task with multiple issues
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, file_references, tags, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                "Contaminated task",
                "See /other/workspace/design.md for details. "
                "Implementation at /external/path/impl.py",
                json.dumps([
                    f"{temp_workspace}/internal.py",
                    "/other/workspace/external.py",
                ]),
                "test other-project",
                "todo",
            ),
        )

        # Insert clean task
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, file_references, tags, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                "Clean task",
                "Normal description",
                json.dumps([f"{temp_workspace}/src/file.py"]),
                "task-mcp testing",
                "todo",
            ),
        )

        # Insert contaminated entity
        cursor.execute(
            """
            INSERT INTO entities (
                entity_type, name, identifier, created_at, updated_at
            ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("file", "External Entity", "/other/workspace/entity.py"),
        )

        conn.commit()
        conn.close()

        yield temp_workspace

    def test_perform_workspace_audit_full_workflow(
        self, setup_contaminated_workspace: str
    ) -> None:
        """Test complete audit workflow with contaminated workspace."""
        report = perform_workspace_audit(
            workspace_path=setup_contaminated_workspace,
            include_deleted=False,
            check_git_repo=False,  # Skip git checks for deterministic testing
        )

        # Verify report structure
        assert "workspace_path" in report
        assert "audit_timestamp" in report
        assert "total_tasks" in report
        assert "total_entities" in report
        assert "contamination_found" in report
        assert "issues" in report
        assert "statistics" in report
        assert "recommendations" in report

        # Verify contamination detected
        assert report["contamination_found"] is True
        assert report["workspace_path"] == setup_contaminated_workspace
        assert report["total_tasks"] == 2
        assert report["total_entities"] == 1

        # Verify issues structure
        assert "file_reference_mismatches" in report["issues"]
        assert "suspicious_tags" in report["issues"]
        assert "description_path_references" in report["issues"]
        assert "entity_identifier_mismatches" in report["issues"]
        assert "git_repo_mismatches" in report["issues"]

        # Verify at least some issues detected
        assert len(report["issues"]["file_reference_mismatches"]) >= 1
        assert len(report["issues"]["suspicious_tags"]) >= 1
        assert len(report["issues"]["description_path_references"]) >= 1
        assert len(report["issues"]["entity_identifier_mismatches"]) >= 1

        # Verify statistics calculated
        assert report["statistics"]["contaminated_tasks"] >= 1
        assert report["statistics"]["contaminated_entities"] >= 1
        assert report["statistics"]["contamination_percentage"] > 0
        assert "high_severity_issues" in report["statistics"]
        assert "medium_severity_issues" in report["statistics"]
        assert "low_severity_issues" in report["statistics"]

        # Verify recommendations generated
        assert len(report["recommendations"]) > 0

    def test_perform_workspace_audit_clean_workspace(
        self, temp_workspace: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test audit workflow with clean workspace (no contamination)."""
        # Point to temp directory for databases
        test_home = tmp_path / ".task-mcp"
        test_home.mkdir()
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create clean database
        conn = get_connection(temp_workspace)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, file_references, tags, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                "Clean task",
                "Normal description",
                json.dumps([f"{temp_workspace}/src/file.py"]),
                "task-mcp testing",
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

        # Should detect no contamination
        assert report["contamination_found"] is False
        assert report["statistics"]["contaminated_tasks"] == 0
        assert report["statistics"]["contaminated_entities"] == 0
        assert report["statistics"]["contamination_percentage"] == 0.0

        # All issue categories should be empty
        for issue_list in report["issues"].values():
            assert len(issue_list) == 0

    def test_perform_workspace_audit_include_deleted(
        self, setup_contaminated_workspace: str
    ) -> None:
        """Test audit workflow includes soft-deleted items when requested."""
        # Add a soft-deleted contaminated task
        conn = get_connection(setup_contaminated_workspace)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, file_references, tags, status, created_at, updated_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now'))
            """,
            (
                "Deleted contaminated task",
                "Deleted",
                json.dumps(["/external/path/deleted.py"]),
                "deleted",
                "todo",
            ),
        )

        conn.commit()
        conn.close()

        # Audit without deleted items
        report_no_deleted = perform_workspace_audit(
            workspace_path=setup_contaminated_workspace,
            include_deleted=False,
            check_git_repo=False,
        )

        # Audit with deleted items
        report_with_deleted = perform_workspace_audit(
            workspace_path=setup_contaminated_workspace,
            include_deleted=True,
            check_git_repo=False,
        )

        # Should have more tasks when including deleted
        assert report_with_deleted["total_tasks"] > report_no_deleted["total_tasks"]

    def test_perform_workspace_audit_empty_workspace(
        self, temp_workspace: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test audit workflow with empty workspace (no tasks or entities)."""
        # Point to temp directory for databases
        test_home = tmp_path / ".task-mcp"
        test_home.mkdir()
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create empty database (just initialize schema)
        conn = get_connection(temp_workspace)
        conn.close()

        report = perform_workspace_audit(
            workspace_path=temp_workspace,
            include_deleted=False,
            check_git_repo=False,
        )

        # Should complete successfully with zero counts
        assert report["contamination_found"] is False
        assert report["total_tasks"] == 0
        assert report["total_entities"] == 0
        assert report["statistics"]["contamination_percentage"] == 0.0
