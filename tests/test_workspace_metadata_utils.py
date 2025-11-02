"""Tests for workspace metadata capture utilities."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from task_mcp.utils import (
    _get_git_root,
    _get_project_name,
    get_workspace_metadata,
)


def test_get_workspace_metadata_git_repo() -> None:
    """Verify get_workspace_metadata() captures all fields in git repo."""
    # Use actual task-mcp workspace (should be a git repo)
    workspace = str(Path(__file__).parent.parent.resolve())

    metadata = get_workspace_metadata(workspace)

    # Verify all required fields present
    assert "workspace_path" in metadata
    assert "git_root" in metadata
    assert "cwd_at_creation" in metadata
    assert "project_name" in metadata

    # Verify workspace_path matches
    assert metadata["workspace_path"] == workspace

    # Verify git_root is populated (task-mcp is a git repo)
    assert metadata["git_root"] is not None
    assert isinstance(metadata["git_root"], str)

    # Verify cwd_at_creation is populated
    assert metadata["cwd_at_creation"] is not None
    assert isinstance(metadata["cwd_at_creation"], str)

    # Verify project_name is populated
    assert metadata["project_name"] is not None
    assert isinstance(metadata["project_name"], str)


def test_get_workspace_metadata_non_git_directory() -> None:
    """Verify get_workspace_metadata() handles non-git directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "non-git-project")
        Path(workspace).mkdir()

        metadata = get_workspace_metadata(workspace)

        # Verify all required fields present
        assert "workspace_path" in metadata
        assert "git_root" in metadata
        assert "cwd_at_creation" in metadata
        assert "project_name" in metadata

        # Verify workspace_path matches (resolve both for macOS /var vs /private/var)
        assert Path(metadata["workspace_path"]).resolve() == Path(workspace).resolve()

        # Verify git_root is None (not a git repo)
        assert metadata["git_root"] is None

        # Verify cwd_at_creation is populated
        assert metadata["cwd_at_creation"] is not None

        # Verify project_name fallback to basename
        assert metadata["project_name"] == "non-git-project"


def test_get_git_root_in_git_repo() -> None:
    """Verify _get_git_root() returns git root for git repositories."""
    # Use actual task-mcp workspace (should be a git repo)
    workspace = str(Path(__file__).parent.parent.resolve())

    git_root = _get_git_root(workspace)

    # Should return non-None git root
    assert git_root is not None
    assert isinstance(git_root, str)
    assert Path(git_root).exists()


def test_get_git_root_non_git_directory() -> None:
    """Verify _get_git_root() returns None for non-git directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_git_path = str(Path(tmpdir) / "non-git")
        Path(non_git_path).mkdir()

        git_root = _get_git_root(non_git_path)

        # Should return None for non-git directory
        assert git_root is None


def test_get_git_root_timeout_handling() -> None:
    """Verify _get_git_root() handles subprocess timeout gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "timeout-test")
        Path(workspace).mkdir()

        # Mock subprocess.run to raise TimeoutExpired
        with patch("task_mcp.utils.subprocess.run") as mock_run:
            from subprocess import TimeoutExpired
            mock_run.side_effect = TimeoutExpired("git", 2)

            git_root = _get_git_root(workspace)

            # Should handle timeout and return None
            assert git_root is None


def test_get_git_root_git_not_installed() -> None:
    """Verify _get_git_root() handles missing git binary gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "no-git")
        Path(workspace).mkdir()

        # Mock subprocess.run to raise FileNotFoundError
        with patch("task_mcp.utils.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")

            git_root = _get_git_root(workspace)

            # Should handle missing git and return None
            assert git_root is None


def test_get_project_name_from_basename() -> None:
    """Verify _get_project_name() fallback to workspace basename."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "test-project-name")
        Path(workspace).mkdir()

        project_name = _get_project_name(workspace)

        # Should return workspace directory name
        assert project_name == "test-project-name"


def test_get_project_name_with_friendly_name() -> None:
    """Verify _get_project_name() retrieves friendly_name from master.db."""
    from task_mcp.master import get_master_connection, register_project
    from task_mcp.utils import ensure_absolute_path, hash_workspace_path

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "friendly-test")
        Path(workspace).mkdir()

        # Resolve workspace path (important for macOS /var vs /private/var)
        workspace_resolved = ensure_absolute_path(workspace)

        # Register project with friendly name
        register_project(workspace_resolved)

        # Set friendly name
        project_hash = hash_workspace_path(workspace_resolved)
        conn = get_master_connection()
        conn.execute(
            "UPDATE projects SET friendly_name = ? WHERE id = ?",
            ("My Friendly Project", project_hash)
        )
        conn.commit()
        conn.close()

        # Get project name
        project_name = _get_project_name(workspace_resolved)

        # Should return friendly_name from master.db
        assert project_name == "My Friendly Project"


def test_get_project_name_database_error_handling() -> None:
    """Verify _get_project_name() handles database errors gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "db-error-test")
        Path(workspace).mkdir()

        # Mock get_master_connection to raise exception (imported within function)
        with patch("task_mcp.master.get_master_connection") as mock_conn:
            mock_conn.side_effect = Exception("Database error")

            project_name = _get_project_name(workspace)

            # Should fallback to basename on error
            assert project_name == "db-error-test"


def test_get_workspace_metadata_fields_types() -> None:
    """Verify get_workspace_metadata() returns correct field types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "type-test")
        Path(workspace).mkdir()

        metadata = get_workspace_metadata(workspace)

        # Verify types
        assert isinstance(metadata["workspace_path"], str)
        assert metadata["git_root"] is None or isinstance(metadata["git_root"], str)
        assert isinstance(metadata["cwd_at_creation"], str)
        assert isinstance(metadata["project_name"], str)


def test_get_workspace_metadata_workspace_resolution() -> None:
    """Verify get_workspace_metadata() uses resolve_workspace logic (v0.4.0)."""
    import pytest

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "resolve-test")
        Path(workspace).mkdir()

        # Test with explicit workspace_path
        metadata = get_workspace_metadata(workspace)
        # Resolve both paths for macOS /var vs /private/var comparison
        assert Path(metadata["workspace_path"]).resolve() == Path(workspace).resolve()

        # Test with None (should raise ValueError in v0.4.0)
        with pytest.raises(ValueError, match="workspace_path is REQUIRED"):
            get_workspace_metadata(None)
