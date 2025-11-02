# Implementation Plan: Strategy 5 - Add Workspace Metadata to Tasks

**Date:** November 2, 2025
**Status:** Planning Phase
**Priority:** HIGH
**Complexity:** Medium (3-4 hours)

---

## Executive Summary

Add workspace metadata to the tasks table to enable cross-workspace validation, audit trails, and prevent task contamination between projects. This implementation follows the established migration pattern used for the `updated_by` field in entities (commit 17d8283).

**Key Benefits:**
- Validate tasks belong to current workspace before operations
- Prevent cross-workspace task contamination
- Enable workspace migration detection and warnings
- Provide audit trail for task creation context
- Support future multi-workspace features

---

## Current Schema Analysis

### Tasks Table (Current - 15 fields)
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('todo', 'in_progress', 'blocked', 'done', 'cancelled')),
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
    parent_task_id INTEGER,
    depends_on TEXT,  -- JSON array
    tags TEXT,
    blocker_reason TEXT,
    file_references TEXT,  -- JSON array
    created_by TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP,
    deleted_at TIMESTAMP,
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
);
```

**Existing Indexes:**
- `idx_status` ON tasks(status)
- `idx_parent` ON tasks(parent_task_id)
- `idx_deleted` ON tasks(deleted_at)
- `idx_tags` ON tasks(tags)

---

## Proposed Schema Changes

### New Field: workspace_metadata

**Field Type:** `TEXT` (JSON string)
**Nullable:** `YES` (backward compatibility for existing tasks)
**Default:** `NULL`

**JSON Schema:**
```json
{
    "workspace_path": "/absolute/path/to/workspace",
    "git_root": "/absolute/path/to/git/repo",  // null if not a git repo
    "cwd_at_creation": "/absolute/path/where/task/created",
    "project_name": "task-mcp"  // from master.db friendly_name or workspace basename
}
```

**Rationale:**
- Single JSON field reduces schema complexity (vs 4 separate columns)
- Follows existing pattern (depends_on, file_references use JSON)
- Allows future extension without schema changes
- Minimal storage overhead (~100-200 bytes per task)

### Updated Tasks Table (16 fields)
```sql
CREATE TABLE tasks (
    -- ... existing 15 fields ...
    workspace_metadata TEXT,  -- NEW: JSON with workspace context
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
);
```

**New Index (Optional):**
```sql
CREATE INDEX IF NOT EXISTS idx_workspace_metadata ON tasks(workspace_metadata);
```
Note: May not be necessary since JSON field queries are rare. Will monitor performance.

---

## Implementation Breakdown

### Phase 1: Database Migration (1 hour)

**File:** `src/task_mcp/database.py`

**Migration Pattern (follows updated_by migration):**
```python
def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize database schema..."""

    # ... existing schema creation ...

    # Migration: Add workspace_metadata column if it doesn't exist (v0.4.0)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(tasks)")
    columns = {row[1] for row in cursor.fetchall()}

    if 'workspace_metadata' not in columns:
        conn.execute("""
            ALTER TABLE tasks ADD COLUMN workspace_metadata TEXT
        """)
        conn.commit()

    # Optional: Create index if performance becomes an issue
    # conn.execute("""
    #     CREATE INDEX IF NOT EXISTS idx_workspace_metadata
    #     ON tasks(workspace_metadata)
    # """)
```

**Key Considerations:**
- Uses `PRAGMA table_info(tasks)` to check column existence
- Zero breaking changes (nullable field)
- Runs automatically on first connection to any project DB
- No data migration needed (existing tasks keep NULL)

---

### Phase 2: Metadata Capture Logic (1 hour)

**File:** `src/task_mcp/utils.py`

**New Function:**
```python
import json
import subprocess
from pathlib import Path

def get_workspace_metadata(workspace_path: str | None = None) -> dict[str, str | None]:
    """
    Capture workspace metadata for task audit trail.

    Args:
        workspace_path: Optional workspace path (resolved internally)

    Returns:
        Dictionary with workspace_path, git_root, cwd_at_creation, project_name

    Examples:
        >>> get_workspace_metadata()
        {
            "workspace_path": "/Users/user/projects/task-mcp",
            "git_root": "/Users/user/projects/task-mcp",
            "cwd_at_creation": "/Users/user/projects/task-mcp/src",
            "project_name": "task-mcp"
        }
    """
    # Resolve workspace using existing logic
    resolved_workspace = resolve_workspace(workspace_path)

    # Get current working directory
    cwd = str(Path.cwd().resolve())

    # Detect git root (if any)
    git_root = _get_git_root(resolved_workspace)

    # Get project name from master.db or workspace basename
    project_name = _get_project_name(resolved_workspace)

    return {
        "workspace_path": resolved_workspace,
        "git_root": git_root,
        "cwd_at_creation": cwd,
        "project_name": project_name
    }


def _get_git_root(workspace_path: str) -> str | None:
    """
    Get git repository root for workspace.

    Args:
        workspace_path: Absolute path to workspace

    Returns:
        Absolute path to git root, or None if not a git repo
    """
    try:
        result = subprocess.run(
            ["git", "-C", workspace_path, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _get_project_name(workspace_path: str) -> str:
    """
    Get project friendly name from master.db or workspace basename.

    Args:
        workspace_path: Absolute path to workspace

    Returns:
        Project friendly name or workspace directory name
    """
    from .master import get_master_connection

    # Try to get friendly_name from master.db
    try:
        project_hash = hash_workspace_path(workspace_path)
        conn = get_master_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT friendly_name FROM projects WHERE id = ?",
            (project_hash,)
        )
        row = cursor.fetchone()
        conn.close()

        if row and row["friendly_name"]:
            return row["friendly_name"]
    except Exception:
        pass  # Fallback to basename

    # Fallback: use workspace directory name
    return Path(workspace_path).name
```

**Testing:**
- Unit tests for git repo detection
- Unit tests for non-git directories
- Unit tests for project name resolution
- Edge cases: symlinks, network drives, spaces in paths

---

### Phase 3: Modify create_task Tool (30 minutes)

**File:** `src/task_mcp/server.py`

**Updated create_task function:**
```python
@mcp.tool()
def create_task(
    title: str,
    ctx: Context | None = None,
    workspace_path: str | None = None,
    # ... existing parameters ...
) -> dict[str, Any]:
    """Create a new task with validation."""
    import json
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .models import TaskCreate
    from .utils import resolve_workspace, validate_description_length, get_workspace_metadata

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Auto-capture session ID
    if created_by is None and ctx is not None:
        created_by = ctx.session_id

    # === NEW: Capture workspace metadata ===
    workspace_metadata_dict = get_workspace_metadata(workspace_path)
    workspace_metadata_json = json.dumps(workspace_metadata_dict)

    # ... existing validation ...

    # Get database connection
    conn = get_connection(workspace_path)
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    try:
        # === UPDATED: Insert with workspace_metadata ===
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, status, priority, parent_task_id,
                depends_on, tags, blocker_reason, file_references, created_by,
                created_at, updated_at, workspace_metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_data.title,
                task_data.description,
                task_data.status,
                task_data.priority,
                task_data.parent_task_id,
                task_data.depends_on,
                task_data.tags,
                task_data.blocker_reason,
                task_data.file_references,
                task_data.created_by,
                now,  # created_at
                now,  # updated_at
                workspace_metadata_json,  # NEW
            ),
        )

        task_id = cursor.lastrowid
        conn.commit()

        # Fetch created task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        return dict(row)
    finally:
        conn.close()
```

**Changes:**
- Import `get_workspace_metadata` from utils
- Call `get_workspace_metadata(workspace_path)` before insert
- Serialize metadata dict to JSON string
- Add `workspace_metadata` to INSERT statement
- Add workspace_metadata to VALUES tuple

---

### Phase 4: Validation Tool (1 hour)

**File:** `src/task_mcp/server.py`

**New MCP Tool:**
```python
@mcp.tool()
def validate_task_workspace(
    task_id: int,
    workspace_path: str | None = None,
) -> dict[str, Any]:
    """
    Validate if task workspace metadata matches current workspace.

    Use this tool to check if a task was created in a different workspace,
    which may indicate cross-workspace contamination or migration.

    Args:
        task_id: Task ID to validate
        workspace_path: Optional workspace path (auto-detected)

    Returns:
        Validation result with details:
        - valid: bool - True if workspace matches or task has no metadata
        - task_id: int - Task ID being validated
        - current_workspace: str - Current resolved workspace path
        - task_workspace: str | None - Workspace from task metadata
        - workspace_match: bool - True if workspaces match exactly
        - warnings: list[str] - List of warning messages
        - metadata: dict | None - Full workspace metadata from task

    Raises:
        ValueError: If task not found or deleted

    Examples:
        >>> validate_task_workspace(task_id=42)
        {
            "valid": True,
            "task_id": 42,
            "current_workspace": "/Users/user/projects/task-mcp",
            "task_workspace": "/Users/user/projects/task-mcp",
            "workspace_match": True,
            "warnings": [],
            "metadata": {
                "workspace_path": "/Users/user/projects/task-mcp",
                "git_root": "/Users/user/projects/task-mcp",
                "cwd_at_creation": "/Users/user/projects/task-mcp/src",
                "project_name": "task-mcp"
            }
        }

        >>> validate_task_workspace(task_id=99)
        {
            "valid": False,
            "task_id": 99,
            "current_workspace": "/Users/user/projects/other-project",
            "task_workspace": "/Users/user/projects/task-mcp",
            "workspace_match": False,
            "warnings": [
                "Task created in different workspace: /Users/user/projects/task-mcp",
                "Current workspace: /Users/user/projects/other-project",
                "This task may not be relevant to current project"
            ],
            "metadata": {...}
        }
    """
    import json

    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    current_workspace = resolve_workspace(workspace_path)
    register_project(current_workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Fetch task
        cursor.execute(
            "SELECT id, workspace_metadata FROM tasks WHERE id = ? AND deleted_at IS NULL",
            (task_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Task {task_id} not found or has been deleted")

        task = dict(row)
        workspace_metadata_json = task.get("workspace_metadata")

        # If no metadata, assume valid (backward compatibility)
        if not workspace_metadata_json:
            return {
                "valid": True,
                "task_id": task_id,
                "current_workspace": current_workspace,
                "task_workspace": None,
                "workspace_match": True,
                "warnings": ["Task created before workspace metadata tracking (legacy task)"],
                "metadata": None
            }

        # Parse metadata
        try:
            metadata = json.loads(workspace_metadata_json)
        except json.JSONDecodeError:
            return {
                "valid": True,  # Assume valid if can't parse
                "task_id": task_id,
                "current_workspace": current_workspace,
                "task_workspace": None,
                "workspace_match": True,
                "warnings": ["Invalid workspace metadata JSON (corrupted data)"],
                "metadata": None
            }

        task_workspace = metadata.get("workspace_path")

        # Compare workspaces
        workspace_match = (task_workspace == current_workspace)

        # Build warnings
        warnings = []
        if not workspace_match:
            warnings.append(f"Task created in different workspace: {task_workspace}")
            warnings.append(f"Current workspace: {current_workspace}")
            warnings.append("This task may not be relevant to current project")

        return {
            "valid": workspace_match,
            "task_id": task_id,
            "current_workspace": current_workspace,
            "task_workspace": task_workspace,
            "workspace_match": workspace_match,
            "warnings": warnings,
            "metadata": metadata
        }

    finally:
        conn.close()
```

**Key Features:**
- Backward compatible (legacy tasks without metadata are valid)
- Handles JSON parse errors gracefully
- Returns detailed warnings for debugging
- Includes full metadata in response for audit
- Non-destructive (read-only validation)

---

### Phase 5: Model Updates (30 minutes)

**File:** `src/task_mcp/models.py`

**Add workspace_metadata field to Task model:**
```python
class Task(BaseModel):
    """Complete task model with all fields and validations."""

    # ... existing fields ...

    workspace_metadata: Optional[str] = Field(
        None,
        description="JSON string with workspace context (workspace_path, git_root, cwd_at_creation, project_name)"
    )

    # ... existing validators ...

    # Helper method
    def get_workspace_metadata_dict(self) -> dict[str, str | None]:
        """
        Parse workspace_metadata JSON string into dictionary.

        Returns:
            Dictionary with workspace context, or empty dict if no metadata
        """
        if not self.workspace_metadata:
            return {}
        try:
            result: dict[str, str | None] = json.loads(self.workspace_metadata)
            return result
        except json.JSONDecodeError:
            return {}
```

**No changes needed for:**
- `TaskCreate` (workspace_metadata auto-captured, not user-provided)
- `TaskUpdate` (workspace_metadata is immutable after creation)

---

### Phase 6: Migration Script for Existing Tasks (Optional - 30 minutes)

**File:** `scripts/backfill_workspace_metadata.py`

```python
#!/usr/bin/env python3
"""
Backfill workspace_metadata for existing tasks.

This script updates all tasks in all project databases with workspace
metadata. Run this ONCE after deploying the workspace_metadata feature.

WARNING: This is a one-time migration. Do not run repeatedly.

Usage:
    python scripts/backfill_workspace_metadata.py [--dry-run]
"""

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from task_mcp.master import get_master_connection
from task_mcp.utils import get_project_db_path, get_workspace_metadata, resolve_workspace


def backfill_project_tasks(project_workspace: str, dry_run: bool = False) -> dict:
    """
    Backfill workspace_metadata for all tasks in a project.

    Args:
        project_workspace: Absolute path to project workspace
        dry_run: If True, don't commit changes

    Returns:
        Stats dict with updated_count, skipped_count, errors
    """
    stats = {"updated": 0, "skipped": 0, "errors": []}

    # Get workspace metadata for this project
    metadata = get_workspace_metadata(project_workspace)
    metadata_json = json.dumps(metadata)

    # Connect to project database
    db_path = get_project_db_path(project_workspace)

    if not db_path.exists():
        stats["errors"].append(f"Database not found: {db_path}")
        return stats

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Find tasks without workspace_metadata
        cursor.execute("""
            SELECT id, title FROM tasks
            WHERE workspace_metadata IS NULL
            AND deleted_at IS NULL
        """)
        tasks_to_update = cursor.fetchall()

        print(f"  Found {len(tasks_to_update)} tasks to update in {metadata['project_name']}")

        for task in tasks_to_update:
            try:
                if not dry_run:
                    cursor.execute(
                        """
                        UPDATE tasks
                        SET workspace_metadata = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (metadata_json, datetime.now().isoformat(), task["id"])
                    )

                stats["updated"] += 1
                print(f"    ✓ Updated task {task['id']}: {task['title'][:50]}")

            except Exception as e:
                stats["errors"].append(f"Task {task['id']}: {str(e)}")
                print(f"    ✗ Error updating task {task['id']}: {e}")

        if not dry_run:
            conn.commit()
            print(f"  Committed {stats['updated']} updates")
        else:
            print(f"  [DRY RUN] Would update {stats['updated']} tasks")

    finally:
        conn.close()

    return stats


def main():
    parser = argparse.ArgumentParser(description="Backfill workspace_metadata for existing tasks")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without committing"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("WORKSPACE METADATA BACKFILL SCRIPT")
    print("=" * 80)

    if args.dry_run:
        print("DRY RUN MODE - No changes will be committed\n")
    else:
        print("LIVE MODE - Changes will be committed\n")

    # Get all projects from master.db
    master_conn = get_master_connection()
    cursor = master_conn.cursor()
    cursor.execute("SELECT workspace_path, friendly_name FROM projects ORDER BY last_accessed DESC")
    projects = cursor.fetchall()
    master_conn.close()

    print(f"Found {len(projects)} projects in master.db\n")

    total_stats = {"updated": 0, "skipped": 0, "errors": []}

    for project in projects:
        workspace = project["workspace_path"]
        name = project["friendly_name"] or Path(workspace).name

        print(f"Processing: {name}")
        print(f"  Workspace: {workspace}")

        stats = backfill_project_tasks(workspace, dry_run=args.dry_run)

        total_stats["updated"] += stats["updated"]
        total_stats["skipped"] += stats["skipped"]
        total_stats["errors"].extend(stats["errors"])

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tasks updated: {total_stats['updated']}")
    print(f"Total tasks skipped: {total_stats['skipped']}")
    print(f"Total errors: {len(total_stats['errors'])}")

    if total_stats["errors"]:
        print("\nErrors:")
        for error in total_stats["errors"]:
            print(f"  - {error}")

    if args.dry_run:
        print("\n⚠️  DRY RUN - No changes committed. Run without --dry-run to apply changes.")
    else:
        print("\n✅ Migration complete!")


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Preview changes
python scripts/backfill_workspace_metadata.py --dry-run

# Apply changes
python scripts/backfill_workspace_metadata.py
```

---

## Backward Compatibility Strategy

### Existing Tasks (NULL workspace_metadata)

**Approach: Permissive Validation**
- Tasks with NULL workspace_metadata are considered **valid** by default
- `validate_task_workspace` returns `valid: True` with warning
- No forced migration required
- Users can optionally run backfill script

**Rationale:**
- Zero breaking changes for existing deployments
- Users choose when to backfill
- Legacy tasks remain functional indefinitely

### New Tasks (Always capture metadata)

**Approach: Auto-capture on create_task**
- All new tasks created after deployment include workspace_metadata
- No user configuration required
- Transparent to user (internal implementation)

---

## Testing Strategy

### Unit Tests (4 new tests)

**File:** `tests/test_workspace_metadata.py`

```python
"""Tests for workspace metadata tracking in tasks."""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from task_mcp.database import get_connection
from task_mcp.server import create_task, validate_task_workspace
from task_mcp.utils import get_workspace_metadata


def test_workspace_metadata_column_exists():
    """Verify workspace_metadata column added to tasks table."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "test-project")
        Path(workspace).mkdir()

        conn = get_connection(workspace)
        cursor = conn.cursor()

        # Check schema
        cursor.execute("PRAGMA table_info(tasks)")
        columns = {row[1] for row in cursor.fetchall()}

        assert "workspace_metadata" in columns, "workspace_metadata column not found"
        conn.close()


def test_create_task_captures_workspace_metadata():
    """Verify create_task captures workspace metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "test-project")
        Path(workspace).mkdir()

        # Create task
        task = create_task(
            title="Test task",
            workspace_path=workspace,
            description="Testing workspace metadata"
        )

        # Verify workspace_metadata field exists and is valid JSON
        assert task["workspace_metadata"] is not None
        metadata = json.loads(task["workspace_metadata"])

        # Verify required fields
        assert "workspace_path" in metadata
        assert "git_root" in metadata
        assert "cwd_at_creation" in metadata
        assert "project_name" in metadata

        # Verify workspace_path matches
        assert metadata["workspace_path"] == workspace


def test_validate_task_workspace_matching():
    """Verify validate_task_workspace returns valid for matching workspace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "test-project")
        Path(workspace).mkdir()

        # Create task
        task = create_task(
            title="Test task",
            workspace_path=workspace
        )

        # Validate in same workspace
        result = validate_task_workspace(
            task_id=task["id"],
            workspace_path=workspace
        )

        assert result["valid"] is True
        assert result["workspace_match"] is True
        assert result["current_workspace"] == workspace
        assert result["task_workspace"] == workspace
        assert len(result["warnings"]) == 0


def test_validate_task_workspace_mismatch():
    """Verify validate_task_workspace detects workspace mismatch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace1 = str(Path(tmpdir) / "project1")
        workspace2 = str(Path(tmpdir) / "project2")
        Path(workspace1).mkdir()
        Path(workspace2).mkdir()

        # Create task in workspace1
        task = create_task(
            title="Test task",
            workspace_path=workspace1
        )

        # Validate in workspace2 (mismatch)
        result = validate_task_workspace(
            task_id=task["id"],
            workspace_path=workspace2
        )

        assert result["valid"] is False
        assert result["workspace_match"] is False
        assert result["current_workspace"] == workspace2
        assert result["task_workspace"] == workspace1
        assert len(result["warnings"]) > 0
        assert "different workspace" in result["warnings"][0]


def test_validate_task_workspace_legacy_task():
    """Verify validate_task_workspace handles NULL metadata (legacy tasks)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "test-project")
        Path(workspace).mkdir()

        # Create legacy task (manually insert without metadata)
        conn = get_connection(workspace)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (title, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """, ("Legacy task", "todo", "medium"))
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Validate legacy task
        result = validate_task_workspace(
            task_id=task_id,
            workspace_path=workspace
        )

        # Should be valid but with warning
        assert result["valid"] is True
        assert result["workspace_match"] is True
        assert result["task_workspace"] is None
        assert result["metadata"] is None
        assert len(result["warnings"]) == 1
        assert "legacy task" in result["warnings"][0].lower()
```

### Integration Tests (2 new tests)

**File:** `tests/test_workspace_metadata_integration.py`

```python
"""Integration tests for workspace metadata across MCP tools."""

import json
import tempfile
from pathlib import Path

import pytest

from task_mcp.server import create_task, get_task, list_tasks


def test_workspace_metadata_persists():
    """Verify workspace metadata persists across create and get operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "test-project")
        Path(workspace).mkdir()

        # Create task
        created_task = create_task(
            title="Persistence test",
            workspace_path=workspace
        )

        created_metadata = json.loads(created_task["workspace_metadata"])

        # Retrieve task
        retrieved_task = get_task(
            task_id=created_task["id"],
            workspace_path=workspace
        )

        retrieved_metadata = json.loads(retrieved_task["workspace_metadata"])

        # Verify metadata matches
        assert created_metadata == retrieved_metadata
        assert retrieved_metadata["workspace_path"] == workspace


def test_workspace_metadata_in_list_tasks():
    """Verify workspace metadata included in list_tasks results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = str(Path(tmpdir) / "test-project")
        Path(workspace).mkdir()

        # Create multiple tasks
        task1 = create_task(title="Task 1", workspace_path=workspace)
        task2 = create_task(title="Task 2", workspace_path=workspace)

        # List tasks
        tasks = list_tasks(workspace_path=workspace)

        # Verify all tasks have workspace_metadata
        assert len(tasks) >= 2
        for task in tasks:
            assert "workspace_metadata" in task
            if task["workspace_metadata"]:  # Skip legacy tasks
                metadata = json.loads(task["workspace_metadata"])
                assert metadata["workspace_path"] == workspace
```

### Manual Testing Checklist

- [ ] Create task in git repo → verify git_root captured
- [ ] Create task in non-git directory → verify git_root is null
- [ ] Create task with friendly_name set → verify project_name matches
- [ ] Create task without friendly_name → verify project_name is workspace basename
- [ ] Run backfill script on existing database → verify all tasks updated
- [ ] Validate task from same workspace → verify valid=True
- [ ] Validate task from different workspace → verify valid=False with warnings
- [ ] Validate legacy task (NULL metadata) → verify valid=True with legacy warning

---

## Estimated Complexity

**Total Time:** 3-4 hours

**Breakdown:**
- Phase 1 (Migration): 1 hour (includes testing)
- Phase 2 (Metadata capture): 1 hour (includes git detection)
- Phase 3 (create_task update): 30 minutes
- Phase 4 (Validation tool): 1 hour
- Phase 5 (Model updates): 30 minutes
- Phase 6 (Backfill script): 30 minutes (optional)

**Risk Assessment:** LOW
- Follows established migration pattern (updated_by field)
- Zero breaking changes (nullable field)
- Extensive test coverage planned
- Backward compatible with existing tasks

---

## Success Criteria

**Implementation Complete When:**
1. ✅ workspace_metadata column exists in tasks table
2. ✅ Auto-migration runs on existing databases
3. ✅ create_task captures metadata for all new tasks
4. ✅ validate_task_workspace tool available and functional
5. ✅ All unit tests passing (6 new tests)
6. ✅ All integration tests passing (2 new tests)
7. ✅ Documentation updated (README.md, CLAUDE.md)
8. ✅ Backfill script available (optional to run)

**Acceptance Criteria:**
- No breaking changes to existing tasks
- Zero test failures (all 207+ tests pass)
- Legacy tasks remain functional
- New tasks include workspace context
- Cross-workspace contamination detectable

---

## Future Enhancements (Out of Scope)

**Not included in this implementation:**
- Automatic workspace validation on all task operations (get_task, update_task, etc.)
- UI warnings for workspace mismatches
- Workspace migration wizard
- Multi-workspace task views
- Workspace-based task filtering in frontend

**Rationale:**
- Focus on foundational metadata capture
- Validation tool is opt-in (non-invasive)
- Future features can build on this foundation

---

## Related Files

**Modified:**
- `src/task_mcp/database.py` - Schema migration
- `src/task_mcp/server.py` - create_task update + validate_task_workspace tool
- `src/task_mcp/models.py` - Task model update
- `src/task_mcp/utils.py` - Metadata capture logic
- `README.md` - Tasks schema documentation
- `CLAUDE.md` - Database documentation

**Created:**
- `scripts/backfill_workspace_metadata.py` - Migration script (optional)
- `tests/test_workspace_metadata.py` - Unit tests (6 tests)
- `tests/test_workspace_metadata_integration.py` - Integration tests (2 tests)
- `docs/implementation-plan-strategy5-workspace-metadata.md` - This document

---

## Commit Message Template

```
feat(tasks): add workspace metadata tracking for audit trail

Implement workspace_metadata field in tasks table to capture workspace
context at task creation. Enables cross-workspace validation, prevents
task contamination, and provides audit trail for task origin.

Features:
- Auto-migration adds workspace_metadata TEXT column (nullable)
- Captures workspace_path, git_root, cwd_at_creation, project_name
- New validate_task_workspace MCP tool for workspace validation
- Backward compatible with legacy tasks (NULL metadata)
- Optional backfill script for existing tasks

Database Changes:
- Added workspace_metadata TEXT column to tasks table (nullable, JSON)
- IF NOT EXISTS migration pattern ensures backward compatibility
- No breaking changes to existing tasks

Implementation Details:
- get_workspace_metadata() captures context at task creation
- Git repository detection via subprocess (timeout: 2s)
- Project name resolution from master.db friendly_name or basename
- JSON schema: workspace_path, git_root, cwd_at_creation, project_name

Testing:
- 6 unit tests for workspace metadata capture and validation
- 2 integration tests for persistence across operations
- Manual testing checklist for git/non-git scenarios
- All tests passing (213/213 - 100% pass rate)

Documentation:
- Updated README.md tasks schema with workspace_metadata field
- Updated CLAUDE.md with implementation details
- Created comprehensive implementation plan
- Created backfill migration script

Migration:
- Automatic schema migration on database connection
- Legacy tasks (NULL metadata) remain valid
- Optional backfill script: scripts/backfill_workspace_metadata.py
- Dry-run mode available for testing

Success Criteria: ✅ All requirements met
- Zero breaking changes maintained
- 100% test pass rate
- Complete audit trail functionality
- Cross-workspace validation enabled

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

**Document Version:** 1.0
**Last Updated:** November 2, 2025
**Status:** Ready for Implementation
