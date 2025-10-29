# link_entity_to_task MCP Tool Implementation

**Entity System MVP v0.3.0 - Phase 3 Tool Implementation**

**Status**: Complete
**Tool**: `link_entity_to_task`
**File**: `src/task_mcp/server.py`
**Lines**: 892-980

---

## Implementation Summary

Successfully implemented the `link_entity_to_task` MCP tool that creates bidirectional links between tasks and entities with comprehensive validation, error handling, and auto-capture of session metadata.

---

## Type-First Development Process

### 1. Type Stub Analysis
Analyzed existing tool patterns in `server.py` to ensure type consistency:
- Return type: `dict[str, Any]` (FastMCP standard)
- Parameter types: `int`, `str | None`, `Context | None`
- Exception types: `ValueError` for user-facing errors

### 2. Type Validation
**mypy --strict**: PASSED
```bash
Success: no issues found in 1 source file
```

**ruff check**: PASSED
```bash
All checks passed!
```

---

## Complete Implementation

### Function Signature
```python
@mcp.tool()
def link_entity_to_task(
    task_id: int,
    entity_id: int,
    workspace_path: str | None = None,
    ctx: Context | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """
    Create a link between a task and an entity.

    Args:
        task_id: Task ID to link
        entity_id: Entity ID to link
        workspace_path: Optional workspace path (auto-detected if not provided)
        ctx: FastMCP context (auto-injected, optional for direct calls)
        created_by: Conversation ID (auto-captured from session if not provided)

    Returns:
        Link dict with link_id, task_id, entity_id, created_at

    Raises:
        ValueError: If task/entity not found, deleted, or link already exists
    """
```

### Core Implementation Features

#### 1. Workspace Detection & Project Registration
```python
# Auto-register project and update last_accessed
workspace = resolve_workspace(workspace_path)
register_project(workspace)
```

**Pattern Compliance**: Follows standard workspace detection priority
- Explicit parameter → env var → cwd fallback
- Auto-registers in master.db
- Updates last_accessed timestamp

#### 2. Session Context Auto-Capture
```python
# Auto-capture session ID if created_by not provided and context available
if created_by is None and ctx is not None:
    created_by = ctx.session_id
```

**Pattern Compliance**: Matches `create_task` tool pattern (lines 122-123)

#### 3. Task Validation
```python
# Validate task exists and is not deleted
cursor.execute(
    "SELECT id FROM tasks WHERE id = ? AND deleted_at IS NULL",
    (task_id,),
)
task_row = cursor.fetchone()
if not task_row:
    raise ValueError(f"Task {task_id} not found or has been deleted")
```

**Validation Rules**:
- Task must exist in database
- Task must not be soft-deleted (`deleted_at IS NULL`)
- User-friendly error message

#### 4. Entity Validation
```python
# Validate entity exists and is not deleted
cursor.execute(
    "SELECT id FROM entities WHERE id = ? AND deleted_at IS NULL",
    (entity_id,),
)
entity_row = cursor.fetchone()
if not entity_row:
    raise ValueError(f"Entity {entity_id} not found or has been deleted")
```

**Validation Rules**:
- Entity must exist in database
- Entity must not be soft-deleted (`deleted_at IS NULL`)
- User-friendly error message

#### 5. Link Creation with Duplicate Detection
```python
# Create link with timestamp
now = datetime.now().isoformat()
try:
    cursor.execute(
        """
        INSERT INTO task_entity_links (task_id, entity_id, created_by, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (task_id, entity_id, created_by, now),
    )
    link_id = cursor.lastrowid
    conn.commit()
except sqlite3.IntegrityError as e:
    if "UNIQUE constraint failed" in str(e):
        raise ValueError(
            f"Link already exists between task {task_id} and entity {entity_id}"
        ) from e
    raise
```

**Error Handling**:
- Catches `sqlite3.IntegrityError` from UNIQUE(task_id, entity_id) constraint
- Converts to user-friendly `ValueError`
- Proper exception chaining with `from e` (ruff B904 compliance)
- Re-raises other IntegrityErrors unchanged

#### 6. Response Format
```python
return {
    "link_id": link_id,
    "task_id": task_id,
    "entity_id": entity_id,
    "created_by": created_by,
    "created_at": now,
}
```

**Return Fields**:
- `link_id`: Auto-generated primary key
- `task_id`: Input task ID (echoed for confirmation)
- `entity_id`: Input entity ID (echoed for confirmation)
- `created_by`: Session ID (auto-captured or explicit)
- `created_at`: ISO 8601 timestamp

#### 7. Resource Cleanup
```python
try:
    # ... implementation ...
finally:
    conn.close()
```

**Pattern Compliance**: Ensures connection closes even on exceptions

---

## Validation & Compliance

### Type Safety Checklist
- [x] 100% type annotations on all parameters
- [x] Explicit return type (`dict[str, Any]`)
- [x] No `Any` types except in return dict (FastMCP standard)
- [x] mypy --strict passes without errors
- [x] Proper exception type annotations

### Code Quality Checklist
- [x] ruff linter passes all checks
- [x] Proper exception chaining (B904)
- [x] PEP 8 compliant formatting
- [x] Comprehensive docstring with Args/Returns/Raises

### Architectural Compliance Checklist
- [x] Follows workspace detection pattern
- [x] Uses `register_project()` for master.db updates
- [x] Auto-captures session context via `ctx.session_id`
- [x] Filters soft-deleted records (`deleted_at IS NULL`)
- [x] Uses ISO 8601 timestamps
- [x] Proper connection cleanup in finally block
- [x] User-friendly error messages

### Database Schema Compliance
- [x] Uses correct table name: `task_entity_links`
- [x] Respects UNIQUE(task_id, entity_id) constraint
- [x] Properly sets all required fields (task_id, entity_id, created_at)
- [x] Optional created_by field handled correctly
- [x] No deleted_at on creation (soft delete not used for links in MVP)

---

## Error Scenarios Handled

### 1. Task Not Found
```python
ValueError: Task 999 not found or has been deleted
```

### 2. Entity Not Found
```python
ValueError: Entity 999 not found or has been deleted
```

### 3. Duplicate Link
```python
ValueError: Link already exists between task 123 and entity 456
```

### 4. Database Errors
- Other IntegrityErrors are re-raised unchanged
- Connection errors propagate naturally
- Transaction rollback handled by SQLite

---

## Integration Notes

### Usage Example
```python
# Link entity to task (auto-captures session ID from context)
result = link_entity_to_task(
    task_id=123,
    entity_id=456
)

# Result:
{
    "link_id": 1,
    "task_id": 123,
    "entity_id": 456,
    "created_by": "session-abc-123",
    "created_at": "2025-10-29T12:34:56.789012"
}
```

### Testing Scenarios

1. **Happy Path**: Link task to entity → Success
2. **Duplicate Prevention**: Link again → ValueError
3. **Task Validation**: Invalid task_id → ValueError
4. **Entity Validation**: Invalid entity_id → ValueError
5. **Soft Delete Handling**: Deleted task/entity → ValueError
6. **Session Capture**: Context available → auto-captures session_id

---

## Future Enhancements (Post-MVP)

1. **Bulk Linking**: Link multiple entities to task in single call
2. **Link Metadata**: Add optional context/notes to links
3. **Link Types**: Support different relationship types (implements, tests, documents)
4. **Soft Delete Links**: Add deleted_at support for link archiving
5. **Bidirectional Queries**: Tools to get tasks by entity and entities by task

---

## Quality Gates Passed

- Type Safety: mypy --strict ✓
- Code Quality: ruff check ✓
- Pattern Compliance: Matches project standards ✓
- Database Schema: Correct table and constraints ✓
- Error Handling: Comprehensive validation ✓
- Documentation: Complete docstring ✓

---

**Implementation Date**: 2025-10-29
**Implementer**: Claude (python-wizard)
**Review Status**: Ready for integration testing
