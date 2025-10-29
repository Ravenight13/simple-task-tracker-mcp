# list_entities Tool Implementation Report

**Tool**: `list_entities` - List entities with optional filters
**Phase**: Phase 3 - MCP Tools Implementation
**Status**: Complete
**Date**: 2025-10-29

## Implementation

### Tool Signature

```python
@mcp.tool()
def list_entities(
    workspace_path: str | None = None,
    entity_type: str | None = None,
    tags: str | None = None,
) -> list[dict[str, Any]]:
    """
    List entities with optional filters.

    Args:
        workspace_path: Optional workspace path (auto-detected)
        entity_type: Filter by entity type ('file' or 'other')
        tags: Filter by tags (space-separated, partial match)

    Returns:
        List of entity dicts matching filters
    """
```

### Complete Implementation

```python
@mcp.tool()
def list_entities(
    workspace_path: str | None = None,
    entity_type: str | None = None,
    tags: str | None = None,
) -> list[dict[str, Any]]:
    """
    List entities with optional filters.

    Args:
        workspace_path: Optional workspace path (auto-detected)
        entity_type: Filter by entity type ('file' or 'other')
        tags: Filter by tags (space-separated, partial match)

    Returns:
        List of entity dicts matching filters
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Build query with filters
        query = "SELECT * FROM entities WHERE deleted_at IS NULL"
        params: list[str] = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        if tags:
            # Partial match on tags (OR logic for multiple tags)
            tag_list = tags.split()
            if tag_list:
                tag_conditions = []
                for tag in tag_list:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                query += f" AND ({' OR '.join(tag_conditions)})"

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()
```

## Design Decisions

### Filter Logic

1. **Soft-delete filtering**: `WHERE deleted_at IS NULL` ensures only active entities are returned
2. **Entity type filter**: Exact match on entity_type ('file' or 'other')
3. **Tag filtering**: Partial match with OR logic
   - Multiple tags separated by spaces
   - Each tag matches using `LIKE %tag%`
   - Combined with OR (entity matches if ANY tag matches)
   - Example: `tags="vendor insurance"` matches entities with "vendor" OR "insurance" in tags

### Return Behavior

- Returns empty list if no matches (not an error)
- Orders by `created_at DESC` (newest first)
- Returns full entity dict including all fields

## Integration Pattern

Follows the same pattern as `list_tasks()`:

1. **Workspace resolution**: Auto-detect or use explicit path
2. **Project registration**: Update master.db on access
3. **Connection handling**: Get connection, execute query, close in finally block
4. **Filter building**: Dynamic SQL with parameterized queries (SQL injection safe)
5. **Return format**: List of dicts for FastMCP serialization

## Type Safety

```python
from typing import Any

@mcp.tool()
def list_entities(
    workspace_path: str | None = None,
    entity_type: str | None = None,
    tags: str | None = None,
) -> list[dict[str, Any]]:
```

- All parameters properly typed with `str | None`
- Return type: `list[dict[str, Any]]` (FastMCP standard format)
- Internal params list typed as `list[str]`

## Testing Recommendations

1. **Test empty result**: No entities should return `[]`
2. **Test entity_type filter**:
   - Filter by 'file' returns only file entities
   - Filter by 'other' returns only other entities
3. **Test tag filtering**:
   - Single tag partial match
   - Multiple tags with OR logic
   - Case-insensitive matching
4. **Test soft-delete filtering**: Soft-deleted entities excluded
5. **Test ordering**: Results ordered by created_at DESC

## Example Usage

```python
# List all entities
all_entities = list_entities()

# List only file entities
files = list_entities(entity_type="file")

# List entities tagged with "vendor"
vendors = list_entities(tags="vendor")

# List entities tagged with "vendor" OR "insurance"
insurance_vendors = list_entities(tags="vendor insurance")

# List file entities tagged with "backend"
backend_files = list_entities(entity_type="file", tags="backend")
```

## SQL Query Examples

```sql
-- No filters
SELECT * FROM entities WHERE deleted_at IS NULL ORDER BY created_at DESC

-- Entity type filter
SELECT * FROM entities WHERE deleted_at IS NULL AND entity_type = ? ORDER BY created_at DESC

-- Tag filter (single tag)
SELECT * FROM entities WHERE deleted_at IS NULL AND (tags LIKE ?) ORDER BY created_at DESC

-- Tag filter (multiple tags with OR)
SELECT * FROM entities WHERE deleted_at IS NULL AND (tags LIKE ? OR tags LIKE ?) ORDER BY created_at DESC

-- Combined filters
SELECT * FROM entities WHERE deleted_at IS NULL AND entity_type = ? AND (tags LIKE ? OR tags LIKE ?) ORDER BY created_at DESC
```

## Architectural Compliance

- **Pattern consistency**: Matches `list_tasks()` implementation
- **Workspace detection**: Uses `resolve_workspace()` utility
- **Project registration**: Updates master.db via `register_project()`
- **Connection safety**: try/finally ensures connection closure
- **SQL safety**: Parameterized queries prevent SQL injection
- **Soft delete**: Excludes deleted_at IS NOT NULL entities

## Next Steps

1. Add tool to `src/task_mcp/server.py` after existing entity tools
2. Run tests to validate filtering logic
3. Update MCP tool registration if needed
4. Document in API reference

## Implementation Location

Add to: `/Users/cliffclarke/Claude_Code/simple-task-tracker-mcp/src/task_mcp/server.py`

Insert after: `delete_entity()` tool (or at end of entity tools section)
