# update_entity Tool Implementation Report

**Date**: 2025-10-29
**Phase**: Phase 3 - MCP Tools Implementation
**Tool**: `update_entity`
**Status**: Complete

## Overview

Implements the `update_entity` MCP tool for Entity System MVP v0.3.0. This tool enables partial updates to entities with identifier uniqueness validation and proper soft-delete handling.

## Implementation

### Type Stub

```python
# Type stub for update_entity tool
from typing import Any

def update_entity(
    entity_id: int,
    workspace_path: str | None = None,
    name: str | None = None,
    identifier: str | None = None,
    description: str | None = None,
    metadata: str | dict | list | None = None,
    tags: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing entity with partial updates.

    Only provided fields will be updated.

    Args:
        entity_id: Entity ID to update (required)
        workspace_path: Optional workspace path
        name: Updated name
        identifier: Updated identifier (checks for duplicates)
        description: Updated description
        metadata: Updated metadata
        tags: Updated tags

    Returns:
        Updated entity dict

    Raises:
        ValueError: If entity not found or identifier conflicts
    """
    ...
```

### Complete Implementation

```python
@mcp.tool()
def update_entity(
    entity_id: int,
    workspace_path: str | None = None,
    name: str | None = None,
    identifier: str | None = None,
    description: str | None = None,
    metadata: str | dict | list | None = None,
    tags: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing entity with partial updates.

    Only provided fields will be updated. Validates identifier uniqueness
    when changing identifiers to prevent duplicates within entity type.

    Args:
        entity_id: Entity ID to update (required)
        workspace_path: Optional workspace path (auto-detected if not provided)
        name: Updated name (1-500 chars)
        identifier: Updated identifier (max 1000 chars, must be unique per type)
        description: Updated description (max 10,000 chars)
        metadata: Updated metadata (JSON string, dict, or list)
        tags: Updated space-separated tags (normalized to lowercase)

    Returns:
        Updated entity object with all fields

    Raises:
        ValueError: If entity not found, soft-deleted, or identifier conflicts

    Examples:
        >>> # Update entity name
        >>> update_entity(1, name="New Name")

        >>> # Change identifier (validates uniqueness)
        >>> update_entity(1, identifier="/new/path/file.py")

        >>> # Update metadata
        >>> update_entity(1, metadata={"version": "2.0", "status": "active"})
    """
    # Import at function level
    import json
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .models import EntityUpdate
    from .utils import resolve_workspace, validate_description_length

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Validate description length if provided
    if description is not None:
        validate_description_length(description)

    # Convert metadata to JSON string if dict/list provided
    metadata_json: str | None = None
    if metadata is not None:
        if isinstance(metadata, str):
            metadata_json = metadata
        elif isinstance(metadata, (dict, list)):
            metadata_json = json.dumps(metadata)
        else:
            raise ValueError("metadata must be a JSON string, dict, or list")

    # Create EntityUpdate model to validate inputs
    update_data = EntityUpdate(
        name=name,
        identifier=identifier,
        description=description,
        metadata=metadata_json,
        tags=tags,
    )

    # Get database connection
    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Fetch current entity to validate changes
        cursor.execute(
            "SELECT * FROM entities WHERE id = ? AND deleted_at IS NULL",
            (entity_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Entity {entity_id} not found or has been deleted")

        current_entity = dict(row)

        # Validate identifier uniqueness if changing
        if identifier is not None and identifier != current_entity["identifier"]:
            cursor.execute(
                """
                SELECT id FROM entities
                WHERE entity_type = ? AND identifier = ? AND id != ? AND deleted_at IS NULL
                """,
                (current_entity["entity_type"], identifier, entity_id),
            )
            existing = cursor.fetchone()

            if existing:
                raise ValueError(
                    f"Entity of type '{current_entity['entity_type']}' already exists "
                    f"with identifier: {identifier}"
                )

        # Build UPDATE statement dynamically for provided fields only
        update_fields = []
        update_params: list[str | int | None] = []

        if update_data.name is not None:
            update_fields.append("name = ?")
            update_params.append(update_data.name)

        if update_data.identifier is not None:
            update_fields.append("identifier = ?")
            update_params.append(update_data.identifier)

        if update_data.description is not None:
            update_fields.append("description = ?")
            update_params.append(update_data.description)

        if update_data.metadata is not None:
            update_fields.append("metadata = ?")
            update_params.append(update_data.metadata)

        if update_data.tags is not None:
            update_fields.append("tags = ?")
            update_params.append(update_data.tags)

        # Always update updated_at timestamp
        update_fields.append("updated_at = ?")
        update_params.append(datetime.now().isoformat())

        # Execute update if there are fields to update
        if update_fields:
            update_params.append(entity_id)
            query = f"UPDATE entities SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_params)
            conn.commit()

        # Fetch and return updated entity
        cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()

        return dict(row)
    finally:
        conn.close()
```

## Key Design Decisions

### 1. Partial Update Pattern

Follows `update_task()` pattern from `server.py` (lines 233-414):
- Only updates fields explicitly provided (not None)
- Dynamic SQL generation for UPDATE statement
- Always updates `updated_at` timestamp

### 2. Identifier Uniqueness Validation

Critical validation logic (requirement from spec):
```python
# Only validate if identifier is changing
if identifier is not None and identifier != current_entity["identifier"]:
    # Check for conflicts within same entity_type
    cursor.execute(
        "SELECT id FROM entities WHERE entity_type = ? AND identifier = ? AND id != ? AND deleted_at IS NULL",
        (current_entity["entity_type"], identifier, entity_id)
    )
    if existing:
        raise ValueError(...)
```

Key aspects:
- Only validates if identifier is actually changing
- Scopes uniqueness check to same `entity_type`
- Excludes soft-deleted entities (`deleted_at IS NULL`)
- Excludes current entity (`id != ?`)

### 3. Metadata Handling

Accepts multiple input formats for convenience:
```python
# Accept string, dict, or list
if isinstance(metadata, str):
    metadata_json = metadata
elif isinstance(metadata, (dict, list)):
    metadata_json = json.dumps(metadata)
```

This allows both:
- Direct JSON strings: `metadata='{"key": "value"}'`
- Python objects: `metadata={"key": "value"}`

### 4. Validation with Pydantic

Uses `EntityUpdate` model from `models.py` (lines 759-787):
- Validates field constraints (lengths, format)
- Normalizes tags (lowercase, single spaces)
- Validates description length (max 10k chars)
- Validates metadata is valid JSON

## Error Handling

### Entity Not Found
```python
if not row:
    raise ValueError(f"Entity {entity_id} not found or has been deleted")
```

### Identifier Conflict
```python
if existing:
    raise ValueError(
        f"Entity of type '{current_entity['entity_type']}' already exists "
        f"with identifier: {identifier}"
    )
```

### Description Length
```python
if description is not None:
    validate_description_length(description)  # Max 10k chars
```

### Invalid Metadata
Pydantic validation via `EntityUpdate` raises `ValueError` for invalid JSON.

## Integration Points

### Dependencies
- `database.py`: `get_connection()` for SQLite access
- `master.py`: `register_project()` for project tracking
- `models.py`: `EntityUpdate` for validation
- `utils.py`: `resolve_workspace()`, `validate_description_length()`

### Database Schema
Operates on `entities` table (see `database.py` lines 156-169):
```sql
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    identifier TEXT,
    description TEXT,
    metadata TEXT,
    tags TEXT,
    created_by TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP
)
```

### Unique Index Interaction
Relies on partial unique index (lines 175-179):
```sql
CREATE UNIQUE INDEX idx_entity_unique
ON entities(entity_type, identifier)
WHERE deleted_at IS NULL AND identifier IS NOT NULL
```

This index:
- Enforces uniqueness for active entities only
- Scoped to `(entity_type, identifier)` pair
- Allows NULL identifiers (not unique)
- Allows soft-deleted duplicates

## Testing Considerations

### Critical Test Cases
1. **Partial updates**: Update single field, verify others unchanged
2. **Identifier uniqueness**: Reject duplicate identifiers within type
3. **Cross-type identifiers**: Allow same identifier for different types
4. **Null identifier**: Allow multiple entities with NULL identifier
5. **Soft delete handling**: Validate against only active entities
6. **Description length**: Reject >10k character descriptions
7. **Metadata formats**: Accept string, dict, list formats
8. **Tag normalization**: Convert "Python Django" → "python django"
9. **Entity not found**: Raise error for invalid entity_id
10. **Soft deleted entity**: Raise error for deleted entity

### Edge Cases
- Update identifier to same value (no-op, should succeed)
- Update identifier to value of soft-deleted entity (should succeed)
- Update with all None values (only updates `updated_at`)
- Concurrent updates to same entity (WAL mode handles)

## Type Safety Validation

### mypy Compliance
```bash
# All type annotations validated
mypy src/task_mcp/server.py --strict
```

Expected: 0 errors

### Type Annotations
- All parameters: fully typed
- Return type: `dict[str, Any]`
- Internal variables: typed where needed
- JSON handling: proper `str | dict | list` union types

## Performance Considerations

### Database Operations
1. **Fetch current entity**: 1 SELECT query
2. **Check identifier conflict**: 1 SELECT query (only if changing)
3. **Update entity**: 1 UPDATE query
4. **Fetch updated entity**: 1 SELECT query

Total: 3-4 queries per update (minimal overhead)

### Index Usage
- Primary key lookup for fetches (O(log n))
- Partial unique index for conflict detection (O(log n))
- No full table scans

## Integration with Server

### Add to server.py

Location: After `create_entity()` tool (maintain alphabetical tool order)

Import additions needed:
```python
# Already present in server.py
import json
from datetime import datetime
from .database import get_connection
from .master import register_project
from .models import EntityUpdate  # May need to add
from .utils import resolve_workspace, validate_description_length
```

## Documentation

### Tool Docstring
Comprehensive docstring includes:
- Purpose and behavior
- All parameter descriptions with constraints
- Return value specification
- All possible exceptions
- Usage examples

### Inline Comments
Key sections commented:
- Metadata format conversion
- Identifier uniqueness validation logic
- Dynamic SQL generation
- Timestamp handling

## Compliance Checklist

- [x] Follows `update_task()` pattern from server.py
- [x] Uses EntityUpdate model for validation
- [x] Validates identifier uniqueness (scoped to entity_type)
- [x] Handles soft deletes correctly
- [x] Updates updated_at timestamp
- [x] Dynamic SQL for partial updates
- [x] Proper error messages
- [x] Complete type annotations
- [x] Comprehensive docstring
- [x] Auto-registers project in master.db
- [x] Closes database connection in finally block

## Next Steps

1. Add implementation to `src/task_mcp/server.py`
2. Verify mypy compliance: `mypy src/task_mcp/server.py --strict`
3. Write unit tests in `tests/test_entity_tools.py`
4. Test identifier uniqueness validation
5. Test metadata format handling
6. Integration test with create/update/get flow

## References

- **Design**: `docs/feature-dev/entity-system/design/2025-10-27-1915-entity-system-design-plan.md`
- **Schema**: `src/task_mcp/database.py` lines 156-223
- **Models**: `src/task_mcp/models.py` lines 585-787
- **Pattern**: `src/task_mcp/server.py` lines 233-414 (`update_task()`)
