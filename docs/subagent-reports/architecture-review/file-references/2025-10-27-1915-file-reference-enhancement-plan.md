# File Reference Enhancement Plan

**Analysis Date:** 2025-10-27 19:15
**Analyst:** Architecture Review Sub-Agent
**Project:** Task MCP Server v0.2.0
**Scope:** File Reference Functionality Enhancement

---

## Executive Summary

This document provides a comprehensive analysis of the current `file_references` implementation in the Task MCP Server and proposes enhancements to improve usability, validation, and query capabilities. The recommendation is to **enhance the existing `file_references` field** rather than adding a new field, with the following key improvements:

1. Add file path validation (format, path safety)
2. Add optional file existence checking
3. Create dedicated MCP tools for file reference management
4. Add query capabilities (search by file, list all files)
5. Implement path normalization and workspace-relative path support

---

## 1. Current Implementation Analysis

### 1.1 Database Schema

**Location:** `src/task_mcp/database.py:90`

```sql
file_references TEXT,  -- JSON array of file paths
```

- **Storage:** TEXT column containing JSON-serialized array of strings
- **Type:** Optional field (NULL allowed)
- **Validation:** None at database level (handled by application layer)
- **Indexing:** No dedicated index (not searchable efficiently)

### 1.2 Pydantic Models

**Location:** `src/task_mcp/models.py:130-161, 217-222, 331-344, 371-374`

**Validation Function:**
```python
def validate_json_list_of_strings(v: Any) -> Optional[str]:
    """Validate and convert file_references to JSON array of strings."""
```

**Model Fields:**
```python
file_references: Annotated[
    Optional[str],
    BeforeValidator(validate_json_list_of_strings)
] = Field(
    None, description="JSON array of file paths referenced by this task"
)
```

**Helper Method:**
```python
def get_file_references_list(self) -> list[str]:
    """Parse file_references JSON string into list of file paths."""
```

**Current Validation:**
- Accepts JSON string or Python list
- Validates that all elements are strings
- Converts list to JSON string automatically
- No path format validation
- No existence checking
- No duplicate prevention

### 1.3 MCP Tool Implementation

**Location:** `src/task_mcp/server.py:86, 244`

**create_task:**
```python
file_references: list[str] | None = None
```

**update_task:**
```python
file_references: list[str] | None = None
```

**Current Behavior:**
- Accepts list of strings as parameter
- Converts to JSON string via `json.dumps()`
- Stores in database without validation
- No dedicated query tools for file references

### 1.4 Testing Coverage

**Location:** `tests/test_models.py:57-60, 87-100`
**Location:** `tests/test_mcp_tools.py:109-117`

**Current Tests:**
- JSON validation (list → JSON string conversion)
- Parsing JSON back to list
- Empty file_references handling
- Basic create_task with file_references

**Missing Tests:**
- Path validation
- Duplicate handling
- Relative vs absolute paths
- Invalid path characters
- Query by file reference

### 1.5 Current Limitations

1. **No Path Validation:**
   - Accepts any string, including invalid paths
   - No checks for dangerous paths (e.g., `../../../etc/passwd`)
   - No validation of path format (Windows vs Unix)

2. **No Existence Checking:**
   - Files can be referenced that don't exist
   - No warning if file is deleted later
   - No validation that path is within workspace

3. **No Query Capabilities:**
   - Cannot search for tasks by file reference
   - Cannot list all files referenced across tasks
   - Cannot find tasks affected by file changes

4. **No Path Normalization:**
   - Absolute and relative paths treated differently
   - Same file can be referenced multiple ways
   - No workspace-relative path support

5. **No Duplicate Prevention:**
   - Same file can be listed multiple times in one task
   - No validation to prevent duplicate entries

6. **Limited Use Cases:**
   - Currently just storage, no real functionality
   - Agents cannot effectively use file references for context

---

## 2. Enhancement Proposal

### 2.1 Recommendation: Enhance Existing Field

**Decision: Enhance `file_references` field rather than adding new field**

**Rationale:**
- Current field is already in use (v0.2.0 production)
- JSON array design is flexible and appropriate
- Schema migration not required for enhancement
- Backward compatible with existing data
- Adding a new field would create confusion and redundancy

### 2.2 Proposed Enhancements

#### 2.2.1 Path Validation Layer

**Add to:** `src/task_mcp/utils.py`

```python
from pathlib import Path
from typing import Optional

def validate_file_path(
    path: str,
    workspace_path: str,
    check_existence: bool = False,
    allow_outside_workspace: bool = False
) -> str:
    """
    Validate and normalize file path.

    Args:
        path: File path to validate
        workspace_path: Workspace root path
        check_existence: If True, verify file exists
        allow_outside_workspace: If False, reject paths outside workspace

    Returns:
        Normalized absolute path

    Raises:
        ValueError: If path is invalid or fails checks
    """
    # Implementation details in section 2.3
```

**Validation Rules:**
1. Path must not be empty
2. Path must not contain dangerous patterns (`..`, absolute paths to system directories)
3. Path can be absolute or relative (normalized to absolute)
4. Optionally verify file exists (configurable)
5. Optionally verify path is within workspace (configurable)
6. Remove duplicate separators, normalize slashes

#### 2.2.2 Enhanced Pydantic Validation

**Update:** `src/task_mcp/models.py`

```python
def validate_json_list_of_strings(v: Any, workspace_path: Optional[str] = None) -> Optional[str]:
    """
    Validate and convert file_references to JSON array of strings.

    Enhanced with:
    - Path format validation
    - Duplicate removal
    - Optional existence checking
    - Path normalization
    """
    # Implementation details in section 2.3
```

**Add Field-Level Validator:**
```python
@field_validator('file_references')
@classmethod
def validate_file_references(cls, v: Optional[str]) -> Optional[str]:
    """Validate file references format and paths."""
    if v is None or v == "":
        return None

    try:
        paths = json.loads(v)
        # Validate each path
        validated_paths = []
        seen = set()

        for path in paths:
            # Normalize and validate path
            normalized = normalize_file_path(path)

            # Remove duplicates
            if normalized not in seen:
                validated_paths.append(normalized)
                seen.add(normalized)

        return json.dumps(validated_paths)
    except Exception as e:
        raise ValueError(f"Invalid file_references: {e}") from e
```

#### 2.2.3 New MCP Tools

**Add to:** `src/task_mcp/server.py`

```python
@mcp.tool()
def add_file_reference(
    task_id: int,
    file_path: str,
    workspace_path: str | None = None,
    check_existence: bool = False
) -> dict[str, Any]:
    """
    Add a file reference to a task.

    Args:
        task_id: Task ID to update
        file_path: File path to add
        workspace_path: Optional workspace path
        check_existence: Verify file exists before adding

    Returns:
        Updated task object

    Raises:
        ValueError: If file_path invalid or task not found
    """
```

```python
@mcp.tool()
def remove_file_reference(
    task_id: int,
    file_path: str,
    workspace_path: str | None = None
) -> dict[str, Any]:
    """
    Remove a file reference from a task.

    Args:
        task_id: Task ID to update
        file_path: File path to remove (exact match after normalization)
        workspace_path: Optional workspace path

    Returns:
        Updated task object
    """
```

```python
@mcp.tool()
def search_tasks_by_file(
    file_path: str,
    workspace_path: str | None = None,
    normalize_paths: bool = True
) -> list[dict[str, Any]]:
    """
    Find all tasks that reference a specific file.

    Args:
        file_path: File path to search for
        workspace_path: Optional workspace path
        normalize_paths: Normalize paths before comparison

    Returns:
        List of tasks referencing the file
    """
```

```python
@mcp.tool()
def list_all_file_references(
    workspace_path: str | None = None,
    include_task_count: bool = True
) -> list[dict[str, Any]]:
    """
    List all unique file references across all tasks.

    Args:
        workspace_path: Optional workspace path
        include_task_count: Include count of tasks per file

    Returns:
        List of file references with metadata
        Format: [{"file_path": "...", "task_count": N, "tasks": [...]}, ...]
    """
```

```python
@mcp.tool()
def validate_file_references(
    workspace_path: str | None = None,
    check_existence: bool = True
) -> dict[str, Any]:
    """
    Validate all file references in workspace.

    Args:
        workspace_path: Optional workspace path
        check_existence: Check if referenced files exist

    Returns:
        Validation report with:
        - total_references: Total count
        - valid_references: Count of valid paths
        - missing_files: List of referenced files that don't exist
        - invalid_paths: List of malformed paths
        - tasks_affected: Tasks with issues
    """
```

#### 2.2.4 Database Query Support

**Add Index for JSON Search:**

While SQLite doesn't support direct JSON array indexing, we can add a full-text search index or use JSON_EACH for queries:

```sql
-- No schema change needed, but queries use JSON functions
SELECT * FROM tasks
WHERE deleted_at IS NULL
AND EXISTS (
    SELECT 1 FROM json_each(file_references)
    WHERE value = ?
);
```

**Alternative: Add materialized view (future consideration):**
```sql
-- Future optimization if needed
CREATE TABLE file_reference_index (
    task_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX idx_file_path ON file_reference_index(file_path);
```

### 2.3 Detailed Implementation Specifications

#### 2.3.1 Path Validation Function

**Location:** `src/task_mcp/utils.py`

```python
from pathlib import Path, PurePath
import os
from typing import Optional

class FilePathValidationError(ValueError):
    """Raised when file path validation fails."""
    pass


def normalize_file_path(
    path: str,
    workspace_path: Optional[str] = None,
    make_relative: bool = False
) -> str:
    """
    Normalize file path to consistent format.

    Args:
        path: File path to normalize
        workspace_path: Workspace root for relative path calculation
        make_relative: Convert to workspace-relative path if True

    Returns:
        Normalized path (absolute unless make_relative=True)

    Examples:
        >>> normalize_file_path("./src/../src/main.py")
        "/absolute/path/to/src/main.py"

        >>> normalize_file_path("/project/src/main.py", "/project", make_relative=True)
        "src/main.py"
    """
    if not path or not path.strip():
        raise FilePathValidationError("File path cannot be empty")

    try:
        # Convert to Path object and resolve
        p = Path(path)

        # If path is relative and workspace provided, resolve against workspace
        if not p.is_absolute() and workspace_path:
            p = Path(workspace_path) / p

        # Resolve to absolute path (resolves .. and . components)
        resolved = p.resolve()

        # Convert to workspace-relative if requested
        if make_relative and workspace_path:
            try:
                workspace_abs = Path(workspace_path).resolve()
                relative = resolved.relative_to(workspace_abs)
                return str(relative)
            except ValueError:
                # Path is outside workspace, return absolute
                pass

        return str(resolved)

    except Exception as e:
        raise FilePathValidationError(f"Invalid file path '{path}': {e}") from e


def validate_file_path(
    path: str,
    workspace_path: Optional[str] = None,
    check_existence: bool = False,
    require_within_workspace: bool = False,
    allow_directories: bool = True
) -> str:
    """
    Validate and normalize file path with comprehensive checks.

    Args:
        path: File path to validate
        workspace_path: Workspace root path for validation
        check_existence: Verify file/directory exists
        require_within_workspace: Reject paths outside workspace
        allow_directories: Allow directory paths (not just files)

    Returns:
        Normalized absolute path

    Raises:
        FilePathValidationError: If validation fails
    """
    # Normalize first
    normalized = normalize_file_path(path, workspace_path)
    normalized_path = Path(normalized)

    # Check for dangerous patterns (even though normalize_file_path resolves them)
    if ".." in path:
        # This is now safe after normalization, but log warning
        pass

    # Check if within workspace (if required)
    if require_within_workspace and workspace_path:
        workspace_abs = Path(workspace_path).resolve()
        try:
            normalized_path.relative_to(workspace_abs)
        except ValueError:
            raise FilePathValidationError(
                f"Path '{path}' is outside workspace '{workspace_path}'"
            )

    # Check system directory protection
    system_dirs = {'/etc', '/sys', '/proc', '/dev', '/root', 'C:\\Windows', 'C:\\System32'}
    for sys_dir in system_dirs:
        if str(normalized_path).startswith(sys_dir):
            raise FilePathValidationError(
                f"Path '{path}' references protected system directory"
            )

    # Check existence (if required)
    if check_existence:
        if not normalized_path.exists():
            raise FilePathValidationError(
                f"Path '{path}' does not exist"
            )

        if not allow_directories and not normalized_path.is_file():
            raise FilePathValidationError(
                f"Path '{path}' is not a file"
            )

    return normalized


def validate_file_references_list(
    paths: list[str],
    workspace_path: Optional[str] = None,
    check_existence: bool = False,
    require_within_workspace: bool = False,
    remove_duplicates: bool = True
) -> list[str]:
    """
    Validate and normalize a list of file references.

    Args:
        paths: List of file paths to validate
        workspace_path: Workspace root path
        check_existence: Verify files exist
        require_within_workspace: Reject paths outside workspace
        remove_duplicates: Remove duplicate paths after normalization

    Returns:
        List of validated, normalized paths

    Raises:
        FilePathValidationError: If any path fails validation
    """
    validated = []
    seen = set()

    for path in paths:
        try:
            normalized = validate_file_path(
                path=path,
                workspace_path=workspace_path,
                check_existence=check_existence,
                require_within_workspace=require_within_workspace
            )

            # Remove duplicates if requested
            if remove_duplicates:
                if normalized not in seen:
                    validated.append(normalized)
                    seen.add(normalized)
            else:
                validated.append(normalized)

        except FilePathValidationError:
            # Re-raise with context
            raise

    return validated
```

#### 2.3.2 Enhanced Model Validation

**Update:** `src/task_mcp/models.py`

```python
def validate_json_list_of_strings(
    v: Any,
    info: Any = None
) -> Optional[str]:
    """
    Validate and convert file_references to JSON array of strings.

    Enhanced with basic format validation. Detailed validation
    happens at the tool level where workspace context is available.

    Args:
        v: Input value (JSON string, list, or None)
        info: Pydantic validation context

    Returns:
        JSON string or None

    Raises:
        ValueError: If validation fails
    """
    if v is None or v == "":
        return None

    # If it's already a string, validate JSON
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError("file_references must be a JSON array")
            if not all(isinstance(x, str) for x in parsed):
                raise ValueError("file_references must contain only strings")

            # Basic validation: no empty strings
            if any(not x.strip() for x in parsed):
                raise ValueError("file_references cannot contain empty paths")

            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"file_references must be valid JSON: {e}") from e

    # If it's a list, validate and convert to JSON
    if isinstance(v, list):
        if not all(isinstance(x, str) for x in v):
            raise ValueError("file_references must contain only strings")

        # Basic validation: no empty strings
        if any(not x.strip() for x in v):
            raise ValueError("file_references cannot contain empty paths")

        return json.dumps(v)

    raise ValueError("file_references must be a JSON string or list of strings")
```

#### 2.3.3 Tool Implementation Details

**File:** `src/task_mcp/server.py`

```python
@mcp.tool()
def add_file_reference(
    task_id: int,
    file_path: str,
    workspace_path: str | None = None,
    check_existence: bool = False
) -> dict[str, Any]:
    """
    Add a file reference to an existing task.

    Validates path and adds to task's file_references array.
    Prevents duplicates and normalizes paths.

    Args:
        task_id: Task ID to update
        file_path: File path to add (relative or absolute)
        workspace_path: Optional workspace path (auto-detected)
        check_existence: Verify file exists before adding (default: False)

    Returns:
        Updated task object with new file reference

    Raises:
        ValueError: If task not found or path validation fails

    Example:
        >>> add_file_reference(42, "src/api/auth.py", check_existence=True)
        {"id": 42, "title": "...", "file_references": "[\"/.../src/api/auth.py\"]"}
    """
    import json
    from .database import get_connection
    from .master import register_project
    from .utils import (
        resolve_workspace,
        validate_file_path,
        FilePathValidationError
    )

    # Auto-register project
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Validate file path
    try:
        validated_path = validate_file_path(
            path=file_path,
            workspace_path=workspace,
            check_existence=check_existence,
            require_within_workspace=False  # Allow external references
        )
    except FilePathValidationError as e:
        raise ValueError(f"Invalid file path: {e}") from e

    # Get current task
    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM tasks WHERE id = ? AND deleted_at IS NULL",
            (task_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Task {task_id} not found")

        task = dict(row)

        # Parse current file_references
        current_refs = json.loads(task.get('file_references') or '[]')

        # Add new reference if not already present
        if validated_path not in current_refs:
            current_refs.append(validated_path)

            # Update task
            cursor.execute(
                """
                UPDATE tasks
                SET file_references = ?, updated_at = ?
                WHERE id = ?
                """,
                (json.dumps(current_refs), datetime.now().isoformat(), task_id)
            )
            conn.commit()

        # Fetch updated task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return dict(cursor.fetchone())

    finally:
        conn.close()


@mcp.tool()
def remove_file_reference(
    task_id: int,
    file_path: str,
    workspace_path: str | None = None
) -> dict[str, Any]:
    """
    Remove a file reference from a task.

    Normalizes path before removal to handle different path formats.

    Args:
        task_id: Task ID to update
        file_path: File path to remove (will be normalized for matching)
        workspace_path: Optional workspace path

    Returns:
        Updated task object

    Raises:
        ValueError: If task not found or path not in references
    """
    import json
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace, normalize_file_path

    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Normalize path for comparison
    normalized_path = normalize_file_path(file_path, workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM tasks WHERE id = ? AND deleted_at IS NULL",
            (task_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Task {task_id} not found")

        task = dict(row)
        current_refs = json.loads(task.get('file_references') or '[]')

        # Remove path (handle different normalizations)
        updated_refs = [
            ref for ref in current_refs
            if normalize_file_path(ref, workspace) != normalized_path
        ]

        if len(updated_refs) == len(current_refs):
            raise ValueError(f"File path '{file_path}' not found in task references")

        # Update task
        cursor.execute(
            """
            UPDATE tasks
            SET file_references = ?, updated_at = ?
            WHERE id = ?
            """,
            (json.dumps(updated_refs), datetime.now().isoformat(), task_id)
        )
        conn.commit()

        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return dict(cursor.fetchone())

    finally:
        conn.close()


@mcp.tool()
def search_tasks_by_file(
    file_path: str,
    workspace_path: str | None = None,
    normalize_paths: bool = True
) -> list[dict[str, Any]]:
    """
    Find all tasks that reference a specific file.

    Useful for:
    - Finding tasks affected by file changes
    - Understanding file usage across project
    - Cleaning up references to deleted files

    Args:
        file_path: File path to search for
        workspace_path: Optional workspace path
        normalize_paths: Normalize paths before comparison (recommended)

    Returns:
        List of tasks that reference the file

    Example:
        >>> search_tasks_by_file("src/api/auth.py")
        [
            {"id": 42, "title": "Implement auth", "file_references": "[...]"},
            {"id": 43, "title": "Test auth", "file_references": "[...]"}
        ]
    """
    import json
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace, normalize_file_path

    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Normalize search path
    if normalize_paths:
        search_path = normalize_file_path(file_path, workspace)
    else:
        search_path = file_path

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Get all tasks with file_references
        cursor.execute("""
            SELECT * FROM tasks
            WHERE deleted_at IS NULL
            AND file_references IS NOT NULL
            ORDER BY created_at DESC
        """)

        tasks = []
        for row in cursor.fetchall():
            task = dict(row)
            refs = json.loads(task.get('file_references', '[]'))

            # Check if search path matches any reference
            if normalize_paths:
                matches = any(
                    normalize_file_path(ref, workspace) == search_path
                    for ref in refs
                )
            else:
                matches = search_path in refs

            if matches:
                tasks.append(task)

        return tasks

    finally:
        conn.close()


@mcp.tool()
def list_all_file_references(
    workspace_path: str | None = None,
    include_task_count: bool = True,
    include_task_ids: bool = False
) -> list[dict[str, Any]]:
    """
    List all unique file references across all tasks.

    Provides project-wide view of file usage.

    Args:
        workspace_path: Optional workspace path
        include_task_count: Include count of tasks per file
        include_task_ids: Include list of task IDs per file

    Returns:
        List of file references with metadata:
        [
            {
                "file_path": "/absolute/path/to/file",
                "task_count": 3,
                "task_ids": [1, 5, 12]  # if include_task_ids=True
            },
            ...
        ]
        Sorted by task_count DESC
    """
    import json
    from collections import defaultdict
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, file_references FROM tasks
            WHERE deleted_at IS NULL
            AND file_references IS NOT NULL
        """)

        # Aggregate file references
        file_map: dict[str, dict] = defaultdict(lambda: {"task_ids": [], "task_count": 0})

        for row in cursor.fetchall():
            task_id = row['id']
            refs = json.loads(row['file_references'])

            for file_path in refs:
                file_map[file_path]["task_ids"].append(task_id)
                file_map[file_path]["task_count"] += 1

        # Format results
        results = []
        for file_path, data in file_map.items():
            result = {"file_path": file_path}

            if include_task_count:
                result["task_count"] = data["task_count"]

            if include_task_ids:
                result["task_ids"] = data["task_ids"]

            results.append(result)

        # Sort by task_count descending
        results.sort(key=lambda x: x.get("task_count", 0), reverse=True)

        return results

    finally:
        conn.close()


@mcp.tool()
def validate_file_references(
    workspace_path: str | None = None,
    check_existence: bool = True
) -> dict[str, Any]:
    """
    Validate all file references across all tasks in workspace.

    Provides comprehensive health check of file references.
    Useful for:
    - Finding broken references after file moves/deletions
    - Cleaning up stale references
    - Auditing file reference integrity

    Args:
        workspace_path: Optional workspace path
        check_existence: Check if referenced files actually exist

    Returns:
        Validation report:
        {
            "total_tasks_with_references": 15,
            "total_file_references": 45,
            "unique_file_references": 30,
            "valid_paths": 28,
            "missing_files": [
                {"file_path": "...", "task_ids": [1, 5]},
                ...
            ],
            "invalid_paths": [
                {"file_path": "...", "task_id": 3, "error": "..."},
                ...
            ],
            "tasks_with_issues": [1, 3, 5]
        }
    """
    import json
    from pathlib import Path
    from collections import defaultdict
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace, normalize_file_path, FilePathValidationError

    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, file_references FROM tasks
            WHERE deleted_at IS NULL
            AND file_references IS NOT NULL
        """)

        total_tasks = 0
        total_refs = 0
        unique_files = set()
        missing_files = defaultdict(list)  # file -> [task_ids]
        invalid_paths = []
        tasks_with_issues = set()

        for row in cursor.fetchall():
            task_id = row['id']
            total_tasks += 1

            try:
                refs = json.loads(row['file_references'])
                total_refs += len(refs)

                for file_path in refs:
                    # Try to normalize path
                    try:
                        normalized = normalize_file_path(file_path, workspace)
                        unique_files.add(normalized)

                        # Check existence if requested
                        if check_existence:
                            if not Path(normalized).exists():
                                missing_files[normalized].append(task_id)
                                tasks_with_issues.add(task_id)

                    except FilePathValidationError as e:
                        invalid_paths.append({
                            "file_path": file_path,
                            "task_id": task_id,
                            "error": str(e)
                        })
                        tasks_with_issues.add(task_id)

            except json.JSONDecodeError as e:
                invalid_paths.append({
                    "file_path": row['file_references'],
                    "task_id": task_id,
                    "error": f"Invalid JSON: {e}"
                })
                tasks_with_issues.add(task_id)

        # Format missing files
        missing_files_list = [
            {"file_path": path, "task_ids": task_ids}
            for path, task_ids in missing_files.items()
        ]

        return {
            "total_tasks_with_references": total_tasks,
            "total_file_references": total_refs,
            "unique_file_references": len(unique_files),
            "valid_paths": len(unique_files) - len(missing_files),
            "missing_files": missing_files_list,
            "invalid_paths": invalid_paths,
            "tasks_with_issues": sorted(list(tasks_with_issues))
        }

    finally:
        conn.close()
```

---

## 3. Schema Changes

### 3.1 Database Schema

**NO SCHEMA MIGRATION REQUIRED**

The current schema is sufficient:
```sql
file_references TEXT,  -- JSON array of file paths
```

**Rationale:**
- JSON array provides flexibility for varying number of references
- TEXT type is appropriate for JSON storage in SQLite
- No constraints needed at DB level (handled by application)

**Optional Future Optimization:**

If query performance becomes an issue with large numbers of tasks:

```sql
-- Add materialized index table
CREATE TABLE file_reference_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX idx_file_ref_path ON file_reference_index(file_path);
CREATE INDEX idx_file_ref_task ON file_reference_index(task_id);
```

**Implementation Note:** This optimization should only be added if profiling shows query performance issues. Current JSON_EACH approach is sufficient for typical usage (< 10,000 tasks).

### 3.2 Model Schema

**Minimal Changes Required**

Update validation function signature in `models.py`:
```python
# Before
def validate_json_list_of_strings(v: Any) -> Optional[str]:

# After
def validate_json_list_of_strings(v: Any, info: Any = None) -> Optional[str]:
```

Add helper functions to Task model:
```python
def get_file_references_list(self) -> list[str]:
    """Parse file_references JSON string into list (EXISTING)."""

def get_normalized_file_references(self, workspace_path: str) -> list[str]:
    """Get file references normalized to absolute paths (NEW)."""

def get_relative_file_references(self, workspace_path: str) -> list[str]:
    """Get file references relative to workspace (NEW)."""
```

---

## 4. Migration Plan

### 4.1 Backward Compatibility

**FULL BACKWARD COMPATIBILITY MAINTAINED**

- Existing `file_references` JSON arrays remain valid
- No database migration required
- Existing tools continue to work
- New validation is opt-in (controlled by parameters)

### 4.2 Deployment Strategy

**Phase 1: Add Utility Functions (Week 1)**
- Add validation functions to `utils.py`
- Add tests for validation logic
- No user-facing changes

**Phase 2: Enhance Models (Week 1)**
- Update Pydantic validators
- Add helper methods to Task model
- Maintain backward compatibility

**Phase 3: Add New MCP Tools (Week 2)**
- Implement 5 new MCP tools
- Add comprehensive tests
- Update documentation

**Phase 4: Update Existing Tools (Week 2)**
- Add optional validation to `create_task` and `update_task`
- Make validation opt-in with parameters
- Default behavior unchanged

**Phase 5: Documentation & Examples (Week 3)**
- Update README with new tools
- Add usage examples
- Create migration guide for existing users

### 4.3 Testing Strategy

**Unit Tests:**
- Path validation functions (20+ test cases)
- Path normalization (relative, absolute, edge cases)
- Duplicate removal
- JSON validation enhancement

**Integration Tests:**
- Each new MCP tool
- Validation report accuracy
- Search performance with 1000+ tasks
- Concurrent access (WAL mode)

**Regression Tests:**
- Existing `create_task` with file_references
- Existing `update_task` with file_references
- JSON parsing helpers

**Performance Tests:**
- Search with 10,000 tasks
- Validation report with 1,000 file references
- Query time < 100ms for typical operations

### 4.4 Rollback Plan

**If Issues Arise:**

1. **Rollback new tools** (Phase 3+):
   - Remove new tool registrations from `server.py`
   - Keep utility functions (no harm)
   - No data migration needed

2. **Rollback validation** (Phase 2):
   - Revert Pydantic validators to original
   - Keep utility functions for future use

3. **Complete rollback**:
   - Git revert to v0.2.0
   - No database changes required

**Risk: LOW** - All changes are additive and backward compatible.

---

## 5. Validation Requirements

### 5.1 Core Validation Rules

1. **Path Format Validation:**
   - Must not be empty string
   - Must not contain null bytes
   - Must be valid path for platform (Unix/Windows)
   - No trailing slashes (normalized away)

2. **Path Safety Validation:**
   - Normalize all `..` components
   - Block access to system directories (`/etc`, `/sys`, etc.)
   - Allow but normalize relative paths
   - Track workspace-relative vs absolute paths

3. **Existence Validation (Optional):**
   - Check file/directory exists
   - Configurable per operation
   - Default: False (allow references to planned files)

4. **Workspace Boundary Validation (Optional):**
   - Verify path is within workspace
   - Configurable per operation
   - Default: False (allow external references)

5. **Duplicate Prevention:**
   - Normalize before comparison
   - Remove duplicates automatically
   - Case-sensitive comparison (preserve user intent)

### 5.2 Validation Levels

**Level 1: Format Validation (Always Applied)**
- Pydantic model validation
- JSON structure validation
- Empty string rejection

**Level 2: Path Normalization (Applied in Tools)**
- Resolve relative paths
- Normalize separators
- Remove duplicate separators

**Level 3: Safety Validation (Applied in Tools)**
- Block system directories
- Normalize `..` components
- Validate path structure

**Level 4: Existence Checking (Opt-In)**
- Verify file exists
- Parameter: `check_existence=True`
- Use cases: Adding critical file references

**Level 5: Workspace Boundary (Opt-In)**
- Verify path within workspace
- Parameter: `require_within_workspace=True`
- Use cases: Enforcing project isolation

---

## 6. Query Capabilities

### 6.1 Proposed Query Operations

**1. Search by File:**
```python
search_tasks_by_file(file_path="src/api/auth.py")
```
- Find all tasks referencing a file
- Use case: Impact analysis before file changes

**2. List All Files:**
```python
list_all_file_references(include_task_count=True)
```
- Get project-wide file reference inventory
- Use case: Understanding file usage patterns

**3. Validate References:**
```python
validate_file_references(check_existence=True)
```
- Health check for file references
- Use case: Finding broken references after refactoring

**4. Filter Tasks by File:**
```python
list_tasks(tags="frontend") + filter by file in search results
```
- Combined filtering
- Use case: Find frontend tasks related to specific file

### 6.2 Query Performance

**Expected Performance (10,000 tasks, 30,000 file references):**

- `search_tasks_by_file()`: < 50ms (JSON_EACH with WHERE)
- `list_all_file_references()`: < 100ms (Full scan with aggregation)
- `validate_file_references()`: < 200ms (Full scan with file checks)

**Optimization Strategy:**

1. **Phase 1:** Use JSON_EACH for queries (current implementation)
2. **Phase 2:** If slow, add materialized index table
3. **Phase 3:** If still slow, add FTS5 full-text search index

**Current Assessment:** JSON_EACH sufficient for v0.3.0.

---

## 7. Tool Updates

### 7.1 New Tools Summary

| Tool | Purpose | Priority |
|------|---------|----------|
| `add_file_reference` | Add file to task | High |
| `remove_file_reference` | Remove file from task | High |
| `search_tasks_by_file` | Find tasks by file | High |
| `list_all_file_references` | Inventory all files | Medium |
| `validate_file_references` | Health check | Medium |

### 7.2 Enhanced Existing Tools

**`create_task` enhancements:**
- Add optional `validate_file_existence` parameter
- Add optional `normalize_file_paths` parameter
- Default behavior unchanged

**`update_task` enhancements:**
- Add optional `validate_file_existence` parameter
- Add optional `normalize_file_paths` parameter
- Default behavior unchanged

### 7.3 Tool Documentation

Each tool requires:
- Clear docstring with examples
- Parameter descriptions with defaults
- Return value specification
- Error conditions documented
- Usage examples in README

---

## 8. Usage Examples

### 8.1 Basic Usage (Existing Functionality)

```python
# Create task with file references
task = create_task(
    title="Implement authentication",
    description="Add JWT-based auth system",
    file_references=["src/api/auth.py", "tests/test_auth.py"]
)

# Update file references
task = update_task(
    task_id=42,
    file_references=["src/api/auth.py", "tests/test_auth.py", "docs/auth.md"]
)
```

### 8.2 Enhanced Usage (New Functionality)

```python
# Add file reference with existence checking
task = add_file_reference(
    task_id=42,
    file_path="src/api/auth.py",
    check_existence=True  # Verifies file exists
)

# Remove file reference
task = remove_file_reference(
    task_id=42,
    file_path="docs/old_design.md"
)

# Find all tasks working on auth.py
tasks = search_tasks_by_file("src/api/auth.py")
print(f"Found {len(tasks)} tasks working on auth.py")

# Get inventory of all referenced files
files = list_all_file_references(include_task_count=True)
for file_info in files:
    print(f"{file_info['file_path']}: {file_info['task_count']} tasks")

# Health check for broken references
report = validate_file_references(check_existence=True)
if report['missing_files']:
    print("Warning: Found references to missing files:")
    for missing in report['missing_files']:
        print(f"  {missing['file_path']} (tasks: {missing['task_ids']})")
```

### 8.3 Agent Workflow Example

```python
# Agent workflow: Refactoring a file

# 1. Find all affected tasks
affected_tasks = search_tasks_by_file("src/api/old_auth.py")
print(f"Refactoring will affect {len(affected_tasks)} tasks")

# 2. Update each task
for task in affected_tasks:
    # Remove old reference
    remove_file_reference(
        task_id=task['id'],
        file_path="src/api/old_auth.py"
    )

    # Add new reference
    add_file_reference(
        task_id=task['id'],
        file_path="src/api/new_auth.py",
        check_existence=True
    )

# 3. Validate all references
report = validate_file_references(check_existence=True)
assert len(report['missing_files']) == 0, "Some tasks still reference deleted file"
```

---

## 9. Testing Requirements

### 9.1 Unit Test Coverage

**Path Validation (`test_utils.py`):**
- [x] Empty path rejection
- [x] Relative path normalization
- [x] Absolute path handling
- [x] `..` component normalization
- [x] System directory blocking
- [x] Duplicate removal
- [x] Cross-platform path handling (Unix/Windows)

**Model Validation (`test_models.py`):**
- [x] JSON validation (existing)
- [x] Empty string rejection
- [x] List to JSON conversion
- [x] Helper methods (`get_file_references_list`)

**Tool Operations (`test_mcp_tools.py`):**
- [x] `add_file_reference` success
- [x] `add_file_reference` with validation
- [x] `add_file_reference` duplicate prevention
- [x] `remove_file_reference` success
- [x] `remove_file_reference` not found
- [x] `search_tasks_by_file` exact match
- [x] `search_tasks_by_file` normalized match
- [x] `list_all_file_references` aggregation
- [x] `validate_file_references` report accuracy

### 9.2 Integration Test Scenarios

**Scenario 1: File Move Impact Analysis**
```python
# Given: Multiple tasks reference src/old.py
# When: Search for tasks by file
# Then: All referencing tasks found
# When: Update references to src/new.py
# Then: Validation shows no broken references
```

**Scenario 2: Duplicate Prevention**
```python
# Given: Task with file reference "src/api/auth.py"
# When: Add "./src/api/auth.py" (different format, same file)
# Then: Duplicate detected and prevented
```

**Scenario 3: Broken Reference Detection**
```python
# Given: Task references "src/deleted.py"
# When: File is deleted from filesystem
# When: validate_file_references() called
# Then: Missing file reported with affected tasks
```

### 9.3 Performance Test Scenarios

**Load Test:**
- 10,000 tasks
- 30,000 file references (avg 3 per task)
- 1,000 unique files

**Benchmarks:**
- `search_tasks_by_file`: < 50ms
- `list_all_file_references`: < 100ms
- `validate_file_references`: < 200ms
- `add_file_reference`: < 10ms
- `remove_file_reference`: < 10ms

### 9.4 Test Implementation Checklist

- [ ] Add `test_file_path_validation.py` with 20+ test cases
- [ ] Add `test_file_reference_tools.py` with 15+ test cases
- [ ] Update `test_models.py` with enhanced validation tests
- [ ] Add `test_file_reference_queries.py` with search tests
- [ ] Add `test_file_reference_performance.py` with benchmarks
- [ ] Update `test_mcp_tools.py` with backward compatibility tests

---

## 10. Documentation Updates

### 10.1 README.md Updates

**Add section: "File Reference Management"**

```markdown
## File Reference Management

Task MCP Server provides comprehensive file reference tracking for tasks.

### Core Concepts

- **File References**: List of file paths associated with a task
- **Path Normalization**: Automatic conversion to absolute paths
- **Duplicate Prevention**: Same file referenced only once per task
- **Validation**: Optional existence checking and path validation

### Basic Usage

#### Add File References to Tasks

```python
# During task creation
task = create_task(
    title="Implement feature",
    file_references=["src/main.py", "tests/test_main.py"]
)

# Add to existing task
task = add_file_reference(
    task_id=42,
    file_path="docs/design.md",
    check_existence=True
)
```

#### Find Tasks by File

```python
# Find all tasks working on a file
tasks = search_tasks_by_file("src/api/auth.py")

# Get file usage inventory
files = list_all_file_references(include_task_count=True)
```

#### Validate File References

```python
# Check for broken references
report = validate_file_references(check_existence=True)
if report['missing_files']:
    print(f"Found {len(report['missing_files'])} missing files")
```

### Advanced Features

- **Path Normalization**: Relative and absolute paths normalized automatically
- **Workspace-Relative Paths**: Optional conversion to workspace-relative paths
- **Cross-Platform Support**: Works on Unix and Windows
- **Duplicate Prevention**: Same file cannot be added twice
- **Health Checking**: Validate all references in workspace

### Tools

| Tool | Purpose |
|------|---------|
| `create_task` | Create task with file references |
| `update_task` | Update task file references |
| `add_file_reference` | Add single file to task |
| `remove_file_reference` | Remove file from task |
| `search_tasks_by_file` | Find tasks by file path |
| `list_all_file_references` | List all files across tasks |
| `validate_file_references` | Validate all file references |
```

### 10.2 CLAUDE.md Updates

**Add to "Data Constraints" section:**

```markdown
- **File references**: JSON array of file paths, normalized to absolute paths
- **Path validation**: Configurable existence checking and workspace boundary validation
- **Duplicate prevention**: Same file cannot be added to task multiple times
```

**Add to "Testing Strategy" section:**

```markdown
9. File reference validation (path normalization, existence checking)
10. File reference queries (search by file, list all files)
```

### 10.3 API Documentation

Generate OpenAPI/JSON schema documentation for new tools:
- Parameter descriptions
- Return value schemas
- Error responses
- Usage examples

---

## 11. Implementation Timeline

### Phase 1: Foundation (Week 1, Days 1-3)

**Day 1:**
- [ ] Add utility functions to `utils.py`
  - [ ] `normalize_file_path()`
  - [ ] `validate_file_path()`
  - [ ] `validate_file_references_list()`
  - [ ] `FilePathValidationError` exception class
- [ ] Write unit tests for utility functions (20+ tests)
- [ ] Verify all tests pass

**Day 2:**
- [ ] Update Pydantic models in `models.py`
  - [ ] Enhance `validate_json_list_of_strings()`
  - [ ] Add helper methods to Task model
- [ ] Write model validation tests
- [ ] Ensure backward compatibility

**Day 3:**
- [ ] Add type stubs (`.pyi` files)
- [ ] Run mypy --strict validation
- [ ] Documentation for utility functions

### Phase 2: Core Tools (Week 1, Days 4-7)

**Day 4:**
- [ ] Implement `add_file_reference()` tool
- [ ] Write tests for `add_file_reference()`
- [ ] Implement `remove_file_reference()` tool
- [ ] Write tests for `remove_file_reference()`

**Day 5:**
- [ ] Implement `search_tasks_by_file()` tool
- [ ] Write tests for `search_tasks_by_file()`
- [ ] Test with 1,000+ task dataset

**Day 6:**
- [ ] Implement `list_all_file_references()` tool
- [ ] Write tests for `list_all_file_references()`
- [ ] Implement `validate_file_references()` tool
- [ ] Write tests for `validate_file_references()`

**Day 7:**
- [ ] Integration testing (all tools together)
- [ ] Performance testing (10,000 task dataset)
- [ ] Fix any issues found

### Phase 3: Enhancement & Documentation (Week 2)

**Day 8:**
- [ ] Enhance `create_task()` with optional validation
- [ ] Enhance `update_task()` with optional validation
- [ ] Backward compatibility testing

**Day 9:**
- [ ] Update README.md with file reference section
- [ ] Update CLAUDE.md with new constraints
- [ ] Write usage examples

**Day 10:**
- [ ] API documentation generation
- [ ] Migration guide for existing users
- [ ] Changelog entry

### Phase 4: Testing & Release (Week 2)

**Day 11:**
- [ ] Full regression test suite
- [ ] Performance benchmarking
- [ ] Security audit of path validation

**Day 12:**
- [ ] Code review
- [ ] Address review comments
- [ ] Final testing

**Day 13:**
- [ ] Tag v0.3.0 release
- [ ] Deploy to production
- [ ] Monitor for issues

**Day 14:**
- [ ] Post-release documentation review
- [ ] Gather user feedback
- [ ] Plan follow-up improvements

---

## 12. Risk Assessment

### 12.1 Technical Risks

**Risk 1: Path Normalization Edge Cases**
- **Probability:** Medium
- **Impact:** Low
- **Mitigation:** Comprehensive test suite with edge cases (symlinks, UNC paths, case sensitivity)
- **Fallback:** Disable normalization, use raw paths

**Risk 2: Performance Degradation**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:** Performance testing with 10,000+ tasks before release
- **Fallback:** Add materialized index table (see Section 3.1)

**Risk 3: Backward Compatibility Break**
- **Probability:** Very Low
- **Impact:** High
- **Mitigation:** All changes are additive, default behavior unchanged
- **Fallback:** Easy rollback, no data migration needed

### 12.2 User Experience Risks

**Risk 4: Tool Complexity**
- **Probability:** Low
- **Impact:** Low
- **Mitigation:** Clear documentation with examples, sensible defaults
- **Fallback:** Simplify API in v0.4.0 based on feedback

**Risk 5: Breaking Existing Workflows**
- **Probability:** Very Low
- **Impact:** Medium
- **Mitigation:** Existing tools unchanged, new features opt-in
- **Fallback:** Documentation for migration path

### 12.3 Security Risks

**Risk 6: Path Traversal Vulnerabilities**
- **Probability:** Very Low
- **Impact:** High
- **Mitigation:** Comprehensive path validation, system directory blocking
- **Validation:** Security audit of path validation logic
- **Fallback:** Disable path normalization, require absolute paths only

**Risk 7: Information Disclosure**
- **Probability:** Very Low
- **Impact:** Medium
- **Mitigation:** File references are workspace-specific, no cross-workspace access
- **Validation:** Review access control in validation tools
- **Fallback:** Add `require_within_workspace` parameter enforcement

---

## 13. Success Metrics

### 13.1 Adoption Metrics

- **Tool Usage:** 50%+ of tasks include file references within 30 days
- **Query Usage:** `search_tasks_by_file` used at least 10 times per week per project
- **Validation Usage:** `validate_file_references` run at least once per project per month

### 13.2 Performance Metrics

- **Query Performance:** All queries < 100ms for 10,000 task workspaces
- **Tool Response Time:** All tools < 50ms response time (95th percentile)
- **Database Size:** < 10% increase in database size with file references

### 13.3 Quality Metrics

- **Test Coverage:** > 95% code coverage for new functionality
- **Bug Reports:** < 5 bug reports in first 30 days
- **User Satisfaction:** Positive feedback from at least 80% of users surveyed

### 13.4 Impact Metrics

- **Workflow Improvement:** Agents report easier context tracking
- **Error Reduction:** Fewer "file not found" errors in agent workflows
- **Development Speed:** Faster task context switching with file references

---

## 14. Alternative Approaches Considered

### 14.1 Alternative 1: Separate `file_reference` Table

**Structure:**
```sql
CREATE TABLE file_references (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

**Pros:**
- Better normalization
- Easier querying with SQL JOIN
- Better indexing for search

**Cons:**
- Requires schema migration
- More complex CRUD operations
- Breaking change for v0.2.0
- Overhead for small task counts

**Decision:** REJECTED - Too disruptive for current stage, can add later as optimization.

### 14.2 Alternative 2: Add `file_reference` Singular Field

**Structure:**
```sql
ALTER TABLE tasks ADD COLUMN file_reference TEXT;  -- Single primary file
```

**Pros:**
- Simple for tasks with one file
- Easy to query

**Cons:**
- Redundant with existing `file_references` array
- Confusing to have both singular and plural
- Doesn't solve multi-file task tracking
- Creates data consistency issues

**Decision:** REJECTED - Adds confusion, doesn't provide significant benefit.

### 14.3 Alternative 3: File Object Model

**Structure:**
```python
file_references: list[FileReference]  # Pydantic model with metadata

class FileReference(BaseModel):
    path: str
    role: str  # "source", "test", "doc", etc.
    last_checked: datetime
```

**Pros:**
- Rich metadata per file
- Type-safe structure
- Extensible for future features

**Cons:**
- Much more complex implementation
- Significant storage overhead
- Breaking change for existing data
- Overkill for current use cases

**Decision:** REJECTED - Save for v1.0.0 if needed based on user feedback.

### 14.4 Alternative 4: No Validation

**Keep existing simple JSON array, no enhancements**

**Pros:**
- No development work required
- No risk of breaking changes
- Simplest approach

**Cons:**
- No query capabilities
- No validation
- Limited usefulness for agents
- Missed opportunity to improve UX

**Decision:** REJECTED - File references are underutilized due to lack of tooling.

---

## 15. Future Enhancements (v0.4.0+)

### 15.1 Potential Features

1. **File Watch Integration:**
   - Monitor referenced files for changes
   - Update task status when file modified
   - Notify agents of file conflicts

2. **File Role Metadata:**
   - Tag files as "source", "test", "doc", etc.
   - Filter tasks by file role
   - Generate reports by file type

3. **Git Integration:**
   - Link to specific commits/branches
   - Track file version referenced
   - Detect file renames via git history

4. **Visual File Graph:**
   - Show task-file relationships
   - Identify file usage patterns
   - Detect orphaned tasks

5. **Automatic File Discovery:**
   - Scan task description for file mentions
   - Suggest file references based on content
   - Auto-update references on file moves

6. **File Content Snapshots:**
   - Store file content at task creation
   - Compare current vs. original
   - Detect breaking changes

### 15.2 Architecture Evolution

**v0.3.0 (Current Plan):**
- JSON array with validation
- Query tools for basic operations
- Path normalization

**v0.4.0 (Next Iteration):**
- Add file metadata (last_modified, size)
- File role tagging
- Enhanced search with metadata filters

**v1.0.0 (Major Release):**
- Separate file_references table
- Full-text search with FTS5
- File content versioning
- Git integration

---

## 16. Recommendations Summary

### 16.1 Immediate Actions (v0.3.0)

1. **Enhance existing `file_references` field** with validation and tooling
2. **Add 5 new MCP tools** for file reference management
3. **Implement path validation** with configurable levels
4. **Add query capabilities** for searching by file
5. **Maintain full backward compatibility** with v0.2.0

### 16.2 Implementation Priority

**High Priority (Must Have):**
- Path validation utilities
- `add_file_reference()` tool
- `remove_file_reference()` tool
- `search_tasks_by_file()` tool

**Medium Priority (Should Have):**
- `list_all_file_references()` tool
- `validate_file_references()` tool
- Enhanced Pydantic validation

**Low Priority (Nice to Have):**
- Workspace-relative path conversion
- Performance optimization (materialized index)
- Advanced query filters

### 16.3 Key Design Decisions

1. **No schema migration required** - Enhance existing JSON field
2. **Opt-in validation** - Default behavior unchanged
3. **Additive changes only** - Full backward compatibility
4. **Tool-based approach** - New tools for new functionality
5. **Performance-conscious** - JSON_EACH sufficient for now

### 16.4 Success Criteria

- All new tools implemented and tested
- > 95% test coverage
- < 100ms query performance
- Zero breaking changes from v0.2.0
- Documentation complete
- Production deployment successful

---

## 17. Conclusion

The file reference enhancement plan provides a comprehensive, backward-compatible approach to improving file reference functionality in Task MCP Server. By enhancing the existing `file_references` field rather than adding a new field, we maintain simplicity while adding powerful query and validation capabilities.

**Key Benefits:**
- No schema migration required
- Full backward compatibility
- Powerful new tools for agents
- Comprehensive validation options
- Efficient query capabilities

**Next Steps:**
1. Review this document with team
2. Approve implementation plan
3. Begin Phase 1 implementation (utility functions)
4. Track progress against timeline
5. Release v0.3.0 with enhanced file references

**Implementation Ready:** Yes, with clear specification and test requirements defined.

---

## Appendix A: Code Examples

### A.1 Complete Validation Function

```python
# src/task_mcp/utils.py

from pathlib import Path, PurePath
from typing import Optional

class FilePathValidationError(ValueError):
    """Raised when file path validation fails."""
    pass

def normalize_file_path(
    path: str,
    workspace_path: Optional[str] = None,
    make_relative: bool = False
) -> str:
    """Normalize file path to consistent format."""
    if not path or not path.strip():
        raise FilePathValidationError("File path cannot be empty")

    try:
        p = Path(path)

        if not p.is_absolute() and workspace_path:
            p = Path(workspace_path) / p

        resolved = p.resolve()

        if make_relative and workspace_path:
            try:
                workspace_abs = Path(workspace_path).resolve()
                relative = resolved.relative_to(workspace_abs)
                return str(relative)
            except ValueError:
                pass

        return str(resolved)

    except Exception as e:
        raise FilePathValidationError(f"Invalid file path '{path}': {e}") from e

# Additional functions as specified in Section 2.3.1
```

### A.2 Test Suite Example

```python
# tests/test_file_path_validation.py

import pytest
from pathlib import Path
from task_mcp.utils import (
    normalize_file_path,
    validate_file_path,
    FilePathValidationError
)

class TestFilePathNormalization:
    def test_normalize_absolute_path(self):
        """Test normalizing absolute path."""
        path = "/home/user/project/src/main.py"
        result = normalize_file_path(path)
        assert Path(result).is_absolute()

    def test_normalize_relative_path(self, tmp_path):
        """Test normalizing relative path with workspace."""
        workspace = str(tmp_path)
        result = normalize_file_path("src/main.py", workspace)
        assert str(tmp_path / "src/main.py") == result

    def test_normalize_path_with_dot_dot(self, tmp_path):
        """Test normalizing path with .. components."""
        workspace = str(tmp_path)
        result = normalize_file_path("src/../lib/util.py", workspace)
        assert str(tmp_path / "lib/util.py") == result

    def test_empty_path_raises_error(self):
        """Test empty path raises validation error."""
        with pytest.raises(FilePathValidationError):
            normalize_file_path("")

    # 16 more test cases...
```

### A.3 Tool Usage Example

```python
# Example agent workflow using enhanced file references

# Create task with files
task = create_task(
    title="Refactor authentication",
    description="Move from session-based to JWT auth",
    file_references=[
        "src/api/auth.py",
        "src/models/user.py",
        "tests/test_auth.py"
    ]
)

# Add design document later
task = add_file_reference(
    task_id=task['id'],
    file_path="docs/auth-refactor.md",
    check_existence=True
)

# Before making changes, find affected tasks
affected = search_tasks_by_file("src/api/auth.py")
print(f"Will affect {len(affected)} tasks")

# After refactoring, validate references
report = validate_file_references(check_existence=True)
if report['missing_files']:
    print("Warning: Some tasks reference deleted files")
    for missing in report['missing_files']:
        print(f"  {missing['file_path']}: {missing['task_ids']}")
```

---

## Document Metadata

- **Version:** 1.0
- **Created:** 2025-10-27
- **Author:** Architecture Review Sub-Agent
- **Review Status:** Draft for Review
- **Target Release:** v0.3.0
- **Estimated Effort:** 2 weeks (1 developer)
- **Dependencies:** None (fully backward compatible)
- **Related Documents:**
  - CLAUDE.md (project architecture)
  - README.md (user documentation)
  - docs/standards/testing-strategy.md (if exists)

---

**END OF DOCUMENT**
