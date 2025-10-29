# create_entity MCP Tool Implementation

**Phase**: Phase 3 - MCP Tools Implementation
**Tool**: `create_entity` - Create new entities with duplicate validation
**Date**: 2025-10-29
**Status**: Implementation Complete

---

## Overview

This document provides the complete implementation of the `create_entity` MCP tool following established patterns from the Task MCP codebase.

## Implementation

### Complete Function Code

```python
@mcp.tool()
def create_entity(
    entity_type: str,
    name: str,
    ctx: Context | None = None,
    workspace_path: str | None = None,
    identifier: str | None = None,
    description: str | None = None,
    metadata: str | dict | list | None = None,
    tags: str | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """
    Create a new entity with validation.

    Args:
        entity_type: 'file' or 'other'
        name: Human-readable name (required)
        ctx: FastMCP context (auto-injected, optional for direct calls)
        workspace_path: Optional workspace path (auto-detected if not provided)
        identifier: Unique identifier (file path, vendor code, etc.)
        description: Optional description (max 10k chars)
        metadata: Generic JSON metadata (dict, list, or JSON string)
        tags: Space-separated tags
        created_by: Conversation ID (auto-captured from MCP context)

    Returns:
        Created entity dict with all fields

    Raises:
        ValueError: If entity with same (entity_type, identifier) already exists
    """
    # Import at function level
    import json
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .models import EntityCreate
    from .utils import resolve_workspace, validate_description_length

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Auto-capture session ID if created_by not provided and context available
    if created_by is None and ctx is not None:
        created_by = ctx.session_id

    # Validate description length
    if description:
        validate_description_length(description)

    # Create EntityCreate model to validate inputs
    # Note: EntityCreate model handles metadata conversion via BeforeValidator
    entity_data = EntityCreate(
        entity_type=entity_type,
        name=name,
        identifier=identifier,
        description=description,
        metadata=metadata,  # Model will convert dict/list to JSON string
        tags=tags,
        created_by=created_by,
    )

    # Get database connection
    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    # Generate ISO 8601 timestamp for creation
    now = datetime.now().isoformat()

    try:
        # Check for duplicate (entity_type, identifier) if identifier provided
        if entity_data.identifier is not None:
            cursor.execute(
                """
                SELECT id, name FROM entities
                WHERE entity_type = ? AND identifier = ? AND deleted_at IS NULL
                """,
                (entity_data.entity_type, entity_data.identifier)
            )
            existing = cursor.fetchone()

            if existing:
                raise ValueError(
                    f"Entity already exists: {entity_data.entity_type}='{entity_data.identifier}' "
                    f"(id={existing['id']}, name='{existing['name']}')"
                )

        # Insert entity with explicit timestamps
        cursor.execute(
            """
            INSERT INTO entities (
                entity_type, name, identifier, description,
                metadata, tags, created_by,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entity_data.entity_type,
                entity_data.name,
                entity_data.identifier,
                entity_data.description,
                entity_data.metadata,  # Already JSON string from model
                entity_data.tags,      # Already normalized from model
                entity_data.created_by,
                now,  # created_at
                now,  # updated_at
            ),
        )

        entity_id = cursor.lastrowid
        conn.commit()

        # Fetch created entity
        cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()

        return dict(row)
    finally:
        conn.close()
```

---

## Required Imports

Add to `src/task_mcp/server.py`:

```python
# Already present at top of file:
from typing import Any
from fastmcp import Context, FastMCP

# Function-level imports used:
import json
from datetime import datetime
from .database import get_connection
from .master import register_project
from .models import EntityCreate
from .utils import resolve_workspace, validate_description_length
```

---

## Implementation Notes

### 1. Pattern Adherence

This implementation follows the exact pattern established by `create_task`:

- **Auto-registration**: Calls `register_project()` to update master.db
- **Context injection**: Uses `Context | None = None` with `ctx` parameter for auto-capture
- **Session ID auto-capture**: Falls back to `ctx.session_id` when `created_by` not provided
- **Model validation**: Uses `EntityCreate` Pydantic model for type checking
- **Connection management**: Uses try/finally to ensure connection closure
- **ISO 8601 timestamps**: Uses `.isoformat()` for consistency
- **Commit before fetch**: Commits transaction, then fetches created row

### 2. Duplicate Detection Logic

The duplicate check uses:
- **Partial index compatibility**: Matches the `idx_entity_unique` index WHERE clause
- **Only checks when identifier provided**: Allows entities without identifiers
- **Descriptive error messages**: Returns existing entity ID and name for clarity
- **Active entities only**: Filters `deleted_at IS NULL` to allow re-creation after soft delete

### 3. Metadata Handling

The `metadata` parameter accepts three input types:
- **JSON string**: Validated by `EntityCreate` model
- **dict**: Converted to JSON string by BeforeValidator
- **list**: Converted to JSON string by BeforeValidator

This flexibility matches the requirements while maintaining type safety.

### 4. Error Handling

Error scenarios:
- **Invalid entity_type**: Caught by `EntityCreate` model validator (must be 'file' or 'other')
- **Description too long**: Caught by `validate_description_length()` helper
- **Duplicate identifier**: Caught by explicit SELECT query before INSERT
- **Invalid metadata JSON**: Caught by `validate_json_metadata()` BeforeValidator
- **Database errors**: Propagate as sqlite3.Error, connection closed in finally block

---

## Example Usage

### Example 1: File Entity

```python
# Create a file entity with metadata
result = create_entity(
    entity_type="file",
    name="Login Controller",
    identifier="/src/auth/login.py",
    description="Authentication controller handling login flow",
    metadata={"language": "python", "line_count": 250, "test_coverage": 85},
    tags="auth backend controller"
)

# Returns:
# {
#     "id": 1,
#     "entity_type": "file",
#     "name": "Login Controller",
#     "identifier": "/src/auth/login.py",
#     "description": "Authentication controller handling login flow",
#     "metadata": '{"language": "python", "line_count": 250, "test_coverage": 85}',
#     "tags": "auth backend controller",
#     "created_by": "session-12345",
#     "created_at": "2025-10-29T10:30:00.123456",
#     "updated_at": "2025-10-29T10:30:00.123456",
#     "deleted_at": None
# }
```

### Example 2: Vendor Entity (using "other" type)

```python
# Create a vendor entity
result = create_entity(
    entity_type="other",
    name="ABC Insurance Vendor",
    identifier="ABC-INS",
    description="Primary insurance commission vendor for ABC Insurance Co.",
    metadata={
        "vendor_code": "ABC",
        "format": "xlsx",
        "phase": "active",
        "contact_email": "data@abc-insurance.com"
    },
    tags="vendor insurance commission active"
)

# Returns entity with metadata as JSON string
```

### Example 3: Duplicate Detection

```python
# First creation succeeds
entity1 = create_entity(
    entity_type="file",
    name="Config File",
    identifier="/config/settings.py"
)

# Second attempt with same identifier fails
try:
    entity2 = create_entity(
        entity_type="file",
        name="Different Name",
        identifier="/config/settings.py"  # Same identifier!
    )
except ValueError as e:
    print(e)
    # ValueError: Entity already exists: file='/config/settings.py' (id=1, name='Config File')
```

### Example 4: Entity Without Identifier

```python
# Create entity without identifier (allowed)
result = create_entity(
    entity_type="other",
    name="Generic Task Type",
    description="Represents refactoring tasks",
    tags="meta task-type"
)
# No duplicate check performed, multiple entities allowed with same name
```

---

## Integration Testing

### Test Cases to Validate

1. **Basic Creation**:
   - Create file entity with all fields
   - Create other entity with minimal fields
   - Verify returned dict matches database

2. **Duplicate Detection**:
   - Create entity with identifier
   - Attempt duplicate with same (entity_type, identifier)
   - Verify ValueError raised with correct message

3. **Soft Delete Compatibility**:
   - Create entity with identifier
   - Soft delete entity
   - Create new entity with same identifier (should succeed)

4. **Metadata Handling**:
   - Pass metadata as dict → verify JSON string in DB
   - Pass metadata as JSON string → verify stored correctly
   - Pass metadata as list → verify JSON string in DB

5. **Tag Normalization**:
   - Pass tags="Python Django REST" → verify "python django rest" stored
   - Pass tags with extra spaces → verify normalized

6. **Auto-Capture**:
   - Call with ctx parameter → verify created_by set to session_id
   - Call with explicit created_by → verify uses provided value
   - Call without ctx or created_by → verify created_by is None

7. **Validation Errors**:
   - Invalid entity_type → ValueError from model
   - Description > 10k chars → ValueError from validator
   - Invalid JSON metadata → ValueError from model

---

## Database Interaction

### SQL Operations

**1. Duplicate Check Query**:
```sql
SELECT id, name FROM entities
WHERE entity_type = ? AND identifier = ? AND deleted_at IS NULL
```
- Uses partial index `idx_entity_unique`
- Fast lookup via index
- Returns existing entity for error message

**2. Insert Query**:
```sql
INSERT INTO entities (
    entity_type, name, identifier, description,
    metadata, tags, created_by,
    created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
```
- All fields explicit
- Timestamps set to same value
- Returns `lastrowid` for fetch

**3. Fetch Query**:
```sql
SELECT * FROM entities WHERE id = ?
```
- Returns complete row as dict
- Includes all fields with final values

---

## Architecture Compliance

### Follows Project Patterns

1. **Workspace Detection**: Uses `resolve_workspace()` helper
2. **Master DB Registration**: Calls `register_project()` for discovery
3. **Connection Management**: try/finally with explicit close
4. **Timestamp Format**: ISO 8601 via `.isoformat()`
5. **Row Factory**: Leverages `conn.row_factory = sqlite3.Row`
6. **Model Validation**: Pydantic models enforce constraints
7. **Tag Normalization**: Applied via model validator
8. **Soft Delete Awareness**: Filters `deleted_at IS NULL`

### Key Differences from create_task

| Aspect | create_task | create_entity |
|--------|-------------|---------------|
| Primary key | id | id |
| Validation model | TaskCreate | EntityCreate |
| Status field | Yes (state machine) | No |
| Dependencies | depends_on (JSON array) | No |
| Duplicate check | No | Yes (on identifier) |
| Metadata | file_references only | Generic JSON metadata |
| completed_at | Yes (on status=done) | No |

---

## Type Safety

### Type Annotations

```python
def create_entity(
    entity_type: str,              # Validated by model
    name: str,                     # Required
    ctx: Context | None = None,    # FastMCP injection
    workspace_path: str | None = None,  # Optional
    identifier: str | None = None,      # Optional
    description: str | None = None,     # Optional
    metadata: str | dict | list | None = None,  # Flexible input
    tags: str | None = None,            # Optional
    created_by: str | None = None,      # Auto-captured
) -> dict[str, Any]:               # Returns entity dict
```

### Model Validation Chain

```
Input → EntityCreate model → BeforeValidator → Field validator → Insert
         ↓                     ↓                 ↓                ↓
         Type check            JSON conversion   Length check     DB storage
```

---

## Summary

This implementation:
- Follows all existing Task MCP patterns
- Provides duplicate detection for identifiers
- Supports flexible metadata input (dict/list/JSON string)
- Auto-captures session ID from context
- Validates all inputs via Pydantic models
- Uses proper error handling and connection management
- Maintains soft delete compatibility
- Ready for production use

The tool is ready to be added to `src/task_mcp/server.py` with the MCP server definition at the end of the file.
