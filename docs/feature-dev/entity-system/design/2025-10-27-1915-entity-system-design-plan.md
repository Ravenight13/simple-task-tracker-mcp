# Entity System Design Plan for Task MCP Server

**Date:** 2025-10-27
**Author:** Claude Code (Subagent Analysis)
**Status:** Design Proposal

---

## Executive Summary

This document proposes a flexible **Entity system** for the Task MCP Server that enables AI agents to define domain-specific entities (files, PRs, issues, components, vendors, etc.) and link them bidirectionally to tasks. The design prioritizes type safety, extensibility, query performance, and seamless integration with the existing task tracking architecture.

**Key Design Decisions:**
- **Typed entities with JSON metadata**: Balance between structure and flexibility
- **Many-to-many linking**: Separate junction table for task-entity relationships
- **Schema per workspace**: Maintains project isolation pattern
- **Validation-first approach**: Pydantic models with strict type safety
- **Backward compatible**: No changes to existing task schema

---

## 1. Design Rationale

### 1.1 What is an "Entity"?

An **Entity** represents a domain concept that AI agents need to track and associate with tasks during development:

**Common Entity Types:**
- **File**: Source code files, config files, documentation
- **PR**: GitHub/GitLab pull requests
- **Issue**: Bug reports, feature requests, tickets
- **Component**: Architectural components, modules, services
- **Vendor**: External vendors in commission processing context
- **API**: External APIs, endpoints, integrations
- **Database**: Tables, schemas, migrations
- **Person**: Team members, stakeholders, reviewers

**Why Entities Matter:**
1. **Context Enrichment**: Tasks reference concrete artifacts (files, PRs, issues)
2. **Cross-Linking**: Discover all tasks related to a specific file or component
3. **Domain Modeling**: Agents can model domain-specific concepts beyond generic tasks
4. **Traceability**: Track which artifacts are associated with which work items

### 1.2 Design Philosophy

**Typed + Flexible Hybrid:**
- **Entity Type** (`entity_type` field): Categorical typing for queries and validation
- **Metadata** (JSON field): Schemaless storage for type-specific attributes
- **Links**: Explicit many-to-many relationships via junction table

**Why Not Fully Schemaless?**
- Need to query "all PR entities" efficiently → requires typed `entity_type` field
- Need referential integrity for task-entity links → requires relational structure
- Need validation rules per entity type → requires Pydantic models

**Why Not Fully Typed Tables?**
- AI agents discover new entity types during development
- Each domain has unique metadata (PR has `pr_number`, Vendor has `vendor_code`)
- Reduces schema migration complexity as new entity types emerge

---

## 2. Database Schema Design

### 2.1 New Tables

#### Table: `entities`

```sql
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN (
        'file', 'pr', 'issue', 'component', 'vendor',
        'api', 'database', 'person', 'other'
    )),
    name TEXT NOT NULL,
    identifier TEXT,  -- e.g., file path, PR number, issue ID
    description TEXT,
    metadata TEXT,    -- JSON object for type-specific fields
    tags TEXT,        -- Space-separated tags (consistent with tasks)
    created_by TEXT,  -- Conversation ID
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,  -- Soft delete
    UNIQUE(entity_type, identifier)  -- Prevent duplicate entities
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_identifier ON entities(identifier);
CREATE INDEX IF NOT EXISTS idx_entity_deleted ON entities(deleted_at);
CREATE INDEX IF NOT EXISTS idx_entity_tags ON entities(tags);
```

**Field Descriptions:**
- `id`: Auto-incrementing primary key
- `entity_type`: Categorical type for filtering and validation
- `name`: Human-readable name (e.g., "User Authentication Component")
- `identifier`: Unique identifier within type (e.g., "/src/auth/login.py", "PR-1234", "ISS-567")
- `description`: Optional detailed description
- `metadata`: JSON object containing type-specific attributes
- `tags`: Space-separated tags (normalized lowercase, same pattern as tasks)
- `created_by`: Conversation ID (auto-captured from MCP context)
- `created_at`, `updated_at`, `deleted_at`: Standard timestamp fields

#### Table: `task_entity_links`

```sql
CREATE TABLE IF NOT EXISTS task_entity_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    entity_id INTEGER NOT NULL,
    link_type TEXT DEFAULT 'references',  -- 'references', 'implements', 'blocks', 'depends_on', 'modifies'
    created_by TEXT,
    created_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,  -- Soft delete
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (entity_id) REFERENCES entities(id),
    UNIQUE(task_id, entity_id, link_type)  -- Prevent duplicate links
);

-- Indexes for bidirectional queries
CREATE INDEX IF NOT EXISTS idx_link_task ON task_entity_links(task_id);
CREATE INDEX IF NOT EXISTS idx_link_entity ON task_entity_links(entity_id);
CREATE INDEX IF NOT EXISTS idx_link_type ON task_entity_links(link_type);
CREATE INDEX IF NOT EXISTS idx_link_deleted ON task_entity_links(deleted_at);
```

**Field Descriptions:**
- `task_id`: Foreign key to tasks table
- `entity_id`: Foreign key to entities table
- `link_type`: Semantic relationship type between task and entity
- `created_by`: Conversation ID
- `created_at`, `deleted_at`: Standard timestamp fields

### 2.2 Schema Migration Strategy

**Location:** Add to `database.py` in `init_schema()` function:

```python
def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize schema with tasks, entities, and links tables."""
    # Existing tasks table creation...

    # Add entities table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL CHECK(entity_type IN (
                'file', 'pr', 'issue', 'component', 'vendor',
                'api', 'database', 'person', 'other'
            )),
            name TEXT NOT NULL,
            identifier TEXT,
            description TEXT,
            metadata TEXT,
            tags TEXT,
            created_by TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP,
            UNIQUE(entity_type, identifier)
        )
    """)

    # Add entity indexes...
    # Add task_entity_links table...
    # Add link indexes...

    conn.commit()
```

**Backward Compatibility:** Existing databases auto-upgrade on first connection (CREATE TABLE IF NOT EXISTS pattern).

---

## 3. Pydantic Models

### 3.1 Entity Models

**File:** `src/task_mcp/models.py` (extend existing file)

```python
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import json

# Constants
VALID_ENTITY_TYPES = ("file", "pr", "issue", "component", "vendor", "api", "database", "person", "other")
VALID_LINK_TYPES = ("references", "implements", "blocks", "depends_on", "modifies")

# Metadata Type Definitions (Type-safe metadata patterns)

class FileMetadata(BaseModel):
    """Metadata for file entities."""
    file_path: str = Field(..., description="Absolute or relative file path")
    language: Optional[str] = Field(None, description="Programming language")
    line_count: Optional[int] = Field(None, ge=0, description="Number of lines")
    last_modified: Optional[str] = Field(None, description="Last modification timestamp")

class PRMetadata(BaseModel):
    """Metadata for pull request entities."""
    pr_number: int = Field(..., ge=1, description="PR number")
    repository: str = Field(..., description="Repository name (org/repo)")
    url: str = Field(..., description="PR URL")
    status: Optional[str] = Field(None, description="open, closed, merged")
    author: Optional[str] = Field(None, description="PR author")

class IssueMetadata(BaseModel):
    """Metadata for issue entities."""
    issue_number: int = Field(..., ge=1, description="Issue number")
    repository: Optional[str] = Field(None, description="Repository name")
    url: Optional[str] = Field(None, description="Issue URL")
    status: Optional[str] = Field(None, description="open, closed")
    assignee: Optional[str] = Field(None, description="Assigned person")

class ComponentMetadata(BaseModel):
    """Metadata for architectural component entities."""
    module_path: Optional[str] = Field(None, description="Module or package path")
    layer: Optional[str] = Field(None, description="Architecture layer (ui, service, data)")
    dependencies: Optional[list[str]] = Field(None, description="List of component dependencies")

class VendorMetadata(BaseModel):
    """Metadata for vendor entities (commission processing)."""
    vendor_code: str = Field(..., description="Vendor identifier code")
    vendor_name: Optional[str] = Field(None, description="Vendor display name")
    file_format: Optional[str] = Field(None, description="Expected file format (xlsx, pdf, csv)")
    contact: Optional[str] = Field(None, description="Vendor contact information")

# Main Entity Model

class Entity(BaseModel):
    """
    Entity model representing domain concepts linked to tasks.

    Supports typed entity categories with flexible JSON metadata.
    """

    model_config = ConfigDict(
        strict=False,
        validate_assignment=True,
        extra='forbid',
    )

    id: Optional[int] = Field(None, description="Entity ID (auto-generated)")
    entity_type: str = Field(..., description=f"Entity type: {VALID_ENTITY_TYPES}")
    name: str = Field(..., min_length=1, max_length=500, description="Entity name")
    identifier: Optional[str] = Field(None, max_length=1000, description="Unique identifier")
    description: Optional[str] = Field(None, description="Entity description (max 10k chars)")
    metadata: Optional[str] = Field(None, description="JSON object with type-specific metadata")
    tags: Optional[str] = Field(None, description="Space-separated tags (normalized)")

    created_by: Optional[str] = Field(None, description="Conversation ID")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # Validators

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity_type is in allowed list."""
        if v not in VALID_ENTITY_TYPES:
            raise ValueError(f"entity_type must be one of {VALID_ENTITY_TYPES}, got '{v}'")
        return v

    @field_validator('description')
    @classmethod
    def validate_description_length(cls, v: Optional[str]) -> Optional[str]:
        """Enforce maximum description length."""
        if v is not None and len(v) > 10_000:
            raise ValueError(f"Description cannot exceed 10,000 characters (got {len(v)})")
        return v

    @field_validator('tags')
    @classmethod
    def normalize_tags(cls, v: Optional[str]) -> Optional[str]:
        """Normalize tags to lowercase with single spaces."""
        if v is None:
            return None
        return " ".join(filter(None, v.lower().split()))

    @field_validator('metadata')
    @classmethod
    def validate_metadata_json(cls, v: Optional[str]) -> Optional[str]:
        """Validate metadata is valid JSON."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            try:
                json.loads(v)  # Validate JSON syntax
                return v
            except json.JSONDecodeError as e:
                raise ValueError(f"metadata must be valid JSON: {e}") from e
        if isinstance(v, dict):
            return json.dumps(v)
        raise ValueError("metadata must be a JSON string or dict")

    # Helper Methods

    def get_metadata_dict(self) -> dict[str, Any]:
        """Parse metadata JSON string into dict."""
        if not self.metadata:
            return {}
        try:
            return json.loads(self.metadata)
        except json.JSONDecodeError:
            return {}

    def validate_metadata_schema(self) -> None:
        """Validate metadata matches expected schema for entity_type."""
        metadata_dict = self.get_metadata_dict()

        # Type-specific validation
        if self.entity_type == "file" and metadata_dict:
            FileMetadata(**metadata_dict)  # Will raise ValidationError if invalid
        elif self.entity_type == "pr" and metadata_dict:
            PRMetadata(**metadata_dict)
        elif self.entity_type == "issue" and metadata_dict:
            IssueMetadata(**metadata_dict)
        elif self.entity_type == "component" and metadata_dict:
            ComponentMetadata(**metadata_dict)
        elif self.entity_type == "vendor" and metadata_dict:
            VendorMetadata(**metadata_dict)


class EntityCreate(BaseModel):
    """Model for creating new entities."""

    model_config = ConfigDict(strict=False, extra='forbid')

    entity_type: str
    name: str = Field(..., min_length=1, max_length=500)
    identifier: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = None
    metadata: Optional[str | dict[str, Any]] = None
    tags: Optional[str] = None
    created_by: Optional[str] = None

    # Reuse validators from Entity model
    _validate_entity_type = field_validator('entity_type')(Entity.validate_entity_type.__func__)
    _validate_description = field_validator('description')(Entity.validate_description_length.__func__)
    _validate_tags = field_validator('tags')(Entity.normalize_tags.__func__)
    _validate_metadata = field_validator('metadata')(Entity.validate_metadata_json.__func__)


class EntityUpdate(BaseModel):
    """Model for updating existing entities."""

    model_config = ConfigDict(strict=False, extra='forbid')

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    identifier: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = None
    metadata: Optional[str | dict[str, Any]] = None
    tags: Optional[str] = None

    # Reuse validators
    _validate_description = field_validator('description')(Entity.validate_description_length.__func__)
    _validate_tags = field_validator('tags')(Entity.normalize_tags.__func__)
    _validate_metadata = field_validator('metadata')(Entity.validate_metadata_json.__func__)


class TaskEntityLink(BaseModel):
    """Model for task-entity links."""

    model_config = ConfigDict(strict=False, extra='forbid')

    id: Optional[int] = None
    task_id: int = Field(..., ge=1)
    entity_id: int = Field(..., ge=1)
    link_type: str = Field(default="references")
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @field_validator('link_type')
    @classmethod
    def validate_link_type(cls, v: str) -> str:
        """Validate link_type is in allowed list."""
        if v not in VALID_LINK_TYPES:
            raise ValueError(f"link_type must be one of {VALID_LINK_TYPES}, got '{v}'")
        return v


class TaskEntityLinkCreate(BaseModel):
    """Model for creating task-entity links."""

    model_config = ConfigDict(strict=False, extra='forbid')

    task_id: int = Field(..., ge=1)
    entity_id: int = Field(..., ge=1)
    link_type: str = Field(default="references")
    created_by: Optional[str] = None

    _validate_link_type = field_validator('link_type')(TaskEntityLink.validate_link_type.__func__)
```

---

## 4. MCP Tools Design

### 4.1 Entity CRUD Operations

#### Tool: `create_entity`

```python
@mcp.tool()
def create_entity(
    entity_type: str,
    name: str,
    ctx: Context | None = None,
    workspace_path: str | None = None,
    identifier: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
    tags: str | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """
    Create a new entity with validation.

    Args:
        entity_type: Entity type (file, pr, issue, component, vendor, api, database, person, other)
        name: Entity name (required, 1-500 chars)
        ctx: FastMCP context (auto-injected)
        workspace_path: Optional workspace path (auto-detected)
        identifier: Unique identifier (e.g., file path, PR number)
        description: Entity description (max 10k chars)
        metadata: Type-specific metadata as dict
        tags: Space-separated tags
        created_by: Conversation ID (auto-captured from context)

    Returns:
        Created entity object with all fields

    Examples:
        # Create file entity
        create_entity(
            entity_type="file",
            name="User Authentication",
            identifier="/src/auth/login.py",
            metadata={"language": "python", "line_count": 250},
            tags="auth security"
        )

        # Create PR entity
        create_entity(
            entity_type="pr",
            name="Add dark mode support",
            identifier="PR-1234",
            metadata={"pr_number": 1234, "repository": "org/repo", "status": "open"},
            tags="feature ui"
        )
    """
    # Implementation: Similar to create_task pattern
    # - Auto-capture created_by from context
    # - Validate with EntityCreate model
    # - Insert into entities table
    # - Return created entity dict
```

#### Tool: `update_entity`

```python
@mcp.tool()
def update_entity(
    entity_id: int,
    workspace_path: str | None = None,
    name: str | None = None,
    identifier: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
    tags: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing entity with validation.

    Args:
        entity_id: Entity ID to update (required)
        workspace_path: Optional workspace path (auto-detected)
        name: Updated entity name
        identifier: Updated identifier
        description: Updated description
        metadata: Updated metadata (replaces existing)
        tags: Updated tags

    Returns:
        Updated entity object

    Raises:
        ValueError: If entity not found or validation fails
    """
```

#### Tool: `get_entity`

```python
@mcp.tool()
def get_entity(
    entity_id: int,
    workspace_path: str | None = None,
) -> dict[str, Any]:
    """
    Get a single entity by ID.

    Args:
        entity_id: Entity ID to retrieve
        workspace_path: Optional workspace path

    Returns:
        Entity object with all fields

    Raises:
        ValueError: If entity not found or soft-deleted
    """
```

#### Tool: `list_entities`

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
        entity_type: Filter by entity type
        tags: Filter by tags (partial match)

    Returns:
        List of entity objects matching filters

    Examples:
        # List all file entities
        list_entities(entity_type="file")

        # List entities tagged with "auth"
        list_entities(tags="auth")
    """
```

#### Tool: `delete_entity`

```python
@mcp.tool()
def delete_entity(
    entity_id: int,
    workspace_path: str | None = None,
    cascade: bool = False,
) -> dict[str, Any]:
    """
    Soft delete an entity by setting deleted_at timestamp.

    Args:
        entity_id: Entity ID to delete
        workspace_path: Optional workspace path
        cascade: If True, also delete all task-entity links

    Returns:
        Success confirmation with deleted count

    Raises:
        ValueError: If entity not found or already deleted
    """
```

#### Tool: `search_entities`

```python
@mcp.tool()
def search_entities(
    search_term: str,
    workspace_path: str | None = None,
    entity_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search entities by name, identifier, or description (full-text).

    Args:
        search_term: Search term to match
        workspace_path: Optional workspace path
        entity_type: Optional filter by entity type

    Returns:
        List of matching entities
    """
```

### 4.2 Task-Entity Linking Operations

#### Tool: `link_entity_to_task`

```python
@mcp.tool()
def link_entity_to_task(
    task_id: int,
    entity_id: int,
    ctx: Context | None = None,
    workspace_path: str | None = None,
    link_type: str = "references",
    created_by: str | None = None,
) -> dict[str, Any]:
    """
    Create a link between a task and an entity.

    Args:
        task_id: Task ID to link
        entity_id: Entity ID to link
        ctx: FastMCP context (auto-injected)
        workspace_path: Optional workspace path
        link_type: Relationship type (references, implements, blocks, depends_on, modifies)
        created_by: Conversation ID (auto-captured)

    Returns:
        Created link object

    Raises:
        ValueError: If task or entity not found, or link already exists

    Examples:
        # Task references a file
        link_entity_to_task(task_id=42, entity_id=7, link_type="modifies")

        # Task implements a PR
        link_entity_to_task(task_id=42, entity_id=15, link_type="implements")
    """
```

#### Tool: `unlink_entity_from_task`

```python
@mcp.tool()
def unlink_entity_from_task(
    task_id: int,
    entity_id: int,
    workspace_path: str | None = None,
    link_type: str | None = None,
) -> dict[str, Any]:
    """
    Remove a link between a task and an entity (soft delete).

    Args:
        task_id: Task ID
        entity_id: Entity ID
        workspace_path: Optional workspace path
        link_type: Optional link type filter (if None, deletes all links)

    Returns:
        Success confirmation with deleted link count
    """
```

#### Tool: `get_task_entities`

```python
@mcp.tool()
def get_task_entities(
    task_id: int,
    workspace_path: str | None = None,
    entity_type: str | None = None,
    link_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get all entities linked to a task.

    Args:
        task_id: Task ID
        workspace_path: Optional workspace path
        entity_type: Optional filter by entity type
        link_type: Optional filter by link type

    Returns:
        List of entity objects with link metadata

    Example Response:
        [
            {
                "entity": {...entity fields...},
                "link": {"link_type": "modifies", "created_at": "2025-10-27T19:15:00"}
            }
        ]
    """
```

#### Tool: `get_entity_tasks`

```python
@mcp.tool()
def get_entity_tasks(
    entity_id: int,
    workspace_path: str | None = None,
    status: str | None = None,
    link_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get all tasks linked to an entity (reverse lookup).

    Args:
        entity_id: Entity ID
        workspace_path: Optional workspace path
        status: Optional filter by task status
        link_type: Optional filter by link type

    Returns:
        List of task objects with link metadata

    Example Use Case:
        # Find all tasks that modify a specific file
        get_entity_tasks(entity_id=7, link_type="modifies")

        # Find all in-progress tasks implementing a PR
        get_entity_tasks(entity_id=15, status="in_progress", link_type="implements")
    """
```

---

## 5. Validation Requirements

### 5.1 Entity Validation Rules

1. **Entity Type Validation**:
   - Must be in VALID_ENTITY_TYPES list
   - Case-sensitive (lowercase only)

2. **Unique Constraint**:
   - `(entity_type, identifier)` must be unique within workspace
   - Prevents duplicate "file:/src/auth/login.py" entities

3. **Description Length**:
   - Maximum 10,000 characters (same as tasks)

4. **Metadata Validation**:
   - Must be valid JSON syntax
   - Optional: Validate against type-specific schemas (FileMetadata, PRMetadata, etc.)

5. **Tags Normalization**:
   - Lowercase, single spaces, trimmed (same pattern as tasks)

### 5.2 Link Validation Rules

1. **Foreign Key Validation**:
   - `task_id` must exist in tasks table and not be soft-deleted
   - `entity_id` must exist in entities table and not be soft-deleted

2. **Link Type Validation**:
   - Must be in VALID_LINK_TYPES list

3. **Unique Constraint**:
   - `(task_id, entity_id, link_type)` must be unique
   - Allows multiple link types between same task-entity pair

4. **Soft Delete Behavior**:
   - Deleting task does NOT cascade delete entities (entities are independent)
   - Deleting entity with `cascade=True` soft-deletes all links
   - Links excluded from queries when `deleted_at IS NOT NULL`

---

## 6. Query Capabilities

### 6.1 Common Query Patterns

#### Find all files modified by a task

```sql
SELECT e.*
FROM entities e
JOIN task_entity_links l ON e.id = l.entity_id
WHERE l.task_id = ?
  AND e.entity_type = 'file'
  AND l.link_type = 'modifies'
  AND e.deleted_at IS NULL
  AND l.deleted_at IS NULL;
```

#### Find all tasks implementing a specific PR

```sql
SELECT t.*
FROM tasks t
JOIN task_entity_links l ON t.id = l.task_id
WHERE l.entity_id = ?
  AND l.link_type = 'implements'
  AND t.deleted_at IS NULL
  AND l.deleted_at IS NULL;
```

#### Find all components tagged with "security"

```sql
SELECT *
FROM entities
WHERE entity_type = 'component'
  AND tags LIKE '%security%'
  AND deleted_at IS NULL;
```

#### Get task with all linked entities (enriched view)

```sql
SELECT
    t.*,
    GROUP_CONCAT(e.name) AS linked_entities
FROM tasks t
LEFT JOIN task_entity_links l ON t.id = l.task_id AND l.deleted_at IS NULL
LEFT JOIN entities e ON l.entity_id = e.id AND e.deleted_at IS NULL
WHERE t.id = ?
GROUP BY t.id;
```

### 6.2 Performance Considerations

**Indexes Required:**
- `idx_entity_type`: Fast filtering by entity type
- `idx_entity_identifier`: Fast unique constraint checking
- `idx_link_task`: Fast lookup of entities for a task
- `idx_link_entity`: Fast lookup of tasks for an entity
- `idx_link_type`: Fast filtering by link type

**Query Optimization:**
- All queries filter `deleted_at IS NULL` (use index)
- Junction table enables efficient many-to-many joins
- `UNIQUE` constraints prevent duplicate processing

---

## 7. Use Cases and Examples

### 7.1 Use Case: File Tracking

**Scenario:** AI agent working on authentication feature needs to track which files are being modified.

```python
# Create file entities
file1 = create_entity(
    entity_type="file",
    name="Login Controller",
    identifier="/src/auth/login.py",
    metadata={"language": "python", "line_count": 250},
    tags="auth backend"
)

file2 = create_entity(
    entity_type="file",
    name="Login Template",
    identifier="/templates/auth/login.html",
    metadata={"language": "html"},
    tags="auth frontend"
)

# Link files to task
link_entity_to_task(task_id=42, entity_id=file1["id"], link_type="modifies")
link_entity_to_task(task_id=42, entity_id=file2["id"], link_type="modifies")

# Query: Get all files modified by task 42
entities = get_task_entities(task_id=42, entity_type="file", link_type="modifies")
# Returns: [file1, file2]

# Query: Find all tasks that modified login.py
tasks = get_entity_tasks(entity_id=file1["id"], link_type="modifies")
```

### 7.2 Use Case: PR-Task Linking

**Scenario:** Track which tasks implement changes for a specific pull request.

```python
# Create PR entity
pr = create_entity(
    entity_type="pr",
    name="Add dark mode support",
    identifier="PR-1234",
    metadata={
        "pr_number": 1234,
        "repository": "myorg/myrepo",
        "url": "https://github.com/myorg/myrepo/pull/1234",
        "status": "open",
        "author": "alice"
    },
    tags="feature ui"
)

# Link multiple tasks to PR
link_entity_to_task(task_id=10, entity_id=pr["id"], link_type="implements")
link_entity_to_task(task_id=11, entity_id=pr["id"], link_type="implements")
link_entity_to_task(task_id=12, entity_id=pr["id"], link_type="implements")

# Query: Get all tasks implementing this PR
tasks = get_entity_tasks(entity_id=pr["id"], link_type="implements")

# Query: Get PR status for task 10
pr_entities = get_task_entities(task_id=10, entity_type="pr")
```

### 7.3 Use Case: Component Dependencies

**Scenario:** Model architectural components and their relationships.

```python
# Create component entities
auth_component = create_entity(
    entity_type="component",
    name="Authentication Service",
    identifier="auth-service",
    metadata={
        "module_path": "src/services/auth",
        "layer": "service",
        "dependencies": ["user-service", "token-service"]
    },
    tags="auth service"
)

# Create task to refactor component
task = create_task(
    title="Refactor authentication service",
    description="Extract token validation into separate module",
    status="todo",
    tags="refactoring auth"
)

# Link component to task
link_entity_to_task(
    task_id=task["id"],
    entity_id=auth_component["id"],
    link_type="modifies"
)

# Query: Find all components being modified
components = list_entities(entity_type="component")
for comp in components:
    tasks = get_entity_tasks(entity_id=comp["id"], link_type="modifies", status="in_progress")
    if tasks:
        print(f"Component {comp['name']} is being modified by {len(tasks)} tasks")
```

### 7.4 Use Case: Vendor Tracking (Commission Processing)

**Scenario:** Track vendor-specific implementation tasks in commission processing system.

```python
# Create vendor entity
vendor = create_entity(
    entity_type="vendor",
    name="ABC Insurance Corp",
    identifier="ABC-INSURANCE",
    metadata={
        "vendor_code": "ABC-INS",
        "vendor_name": "ABC Insurance Corporation",
        "file_format": "xlsx",
        "contact": "vendor-support@abc-insurance.com"
    },
    tags="vendor insurance"
)

# Create tasks for vendor integration
task1 = create_task(
    title="Implement ABC Insurance file parser",
    description="Extract commission data from ABC Insurance Excel files"
)

task2 = create_task(
    title="Add ABC Insurance validation rules",
    description="Implement vendor-specific validation logic"
)

# Link tasks to vendor
link_entity_to_task(task_id=task1["id"], entity_id=vendor["id"], link_type="implements")
link_entity_to_task(task_id=task2["id"], entity_id=vendor["id"], link_type="implements")

# Query: Find all tasks for ABC Insurance vendor
tasks = get_entity_tasks(entity_id=vendor["id"])

# Query: Get all vendors with open tasks
all_vendors = list_entities(entity_type="vendor")
for v in all_vendors:
    open_tasks = get_entity_tasks(entity_id=v["id"], status="todo")
    print(f"Vendor {v['name']}: {len(open_tasks)} open tasks")
```

### 7.5 Use Case: Issue-Task Mapping

**Scenario:** Link GitHub issues to implementation tasks for traceability.

```python
# Create issue entity
issue = create_entity(
    entity_type="issue",
    name="Users cannot reset password",
    identifier="ISS-567",
    metadata={
        "issue_number": 567,
        "repository": "myorg/myapp",
        "url": "https://github.com/myorg/myapp/issues/567",
        "status": "open",
        "assignee": "bob"
    },
    tags="bug auth"
)

# Create task to fix issue
task = create_task(
    title="Fix password reset bug",
    description="Implement proper email validation in reset flow",
    status="in_progress"
)

# Link task to issue
link_entity_to_task(task_id=task["id"], entity_id=issue["id"], link_type="implements")

# Query: Find all tasks implementing this issue
tasks = get_entity_tasks(entity_id=issue["id"], link_type="implements")

# When task is done, update issue status
update_task(task_id=task["id"], status="done")
update_entity(entity_id=issue["id"], metadata={"status": "resolved"})
```

---

## 8. Implementation Plan

### 8.1 Phase 1: Core Schema and Models (High Priority)

**Files to Modify:**
1. `src/task_mcp/database.py`:
   - Add `entities` table creation in `init_schema()`
   - Add `task_entity_links` table creation
   - Add entity-related indexes

2. `src/task_mcp/models.py`:
   - Add `Entity`, `EntityCreate`, `EntityUpdate` models
   - Add `TaskEntityLink`, `TaskEntityLinkCreate` models
   - Add metadata models (FileMetadata, PRMetadata, etc.)
   - Add validation functions

**Testing:**
- Test entity table creation
- Test unique constraint `(entity_type, identifier)`
- Test metadata JSON validation
- Test soft delete filtering

### 8.2 Phase 2: Entity CRUD Tools (High Priority)

**Files to Modify:**
1. `src/task_mcp/server.py`:
   - Add `create_entity` tool
   - Add `update_entity` tool
   - Add `get_entity` tool
   - Add `list_entities` tool
   - Add `delete_entity` tool
   - Add `search_entities` tool

**Testing:**
- Test entity creation with all entity types
- Test metadata validation per type
- Test description length validation
- Test tags normalization
- Test soft delete behavior

### 8.3 Phase 3: Linking Tools (High Priority)

**Files to Modify:**
1. `src/task_mcp/server.py`:
   - Add `link_entity_to_task` tool
   - Add `unlink_entity_from_task` tool
   - Add `get_task_entities` tool
   - Add `get_entity_tasks` tool

**Testing:**
- Test link creation and validation
- Test unique constraint `(task_id, entity_id, link_type)`
- Test foreign key validation
- Test bidirectional queries (task→entities, entity→tasks)
- Test cascade delete behavior

### 8.4 Phase 4: Advanced Queries (Medium Priority)

**New Tools:**
1. `get_entities_by_file_path`: Convenience method for file lookups
2. `get_tasks_by_pr_number`: Find tasks implementing specific PR
3. `get_component_dependencies`: Analyze component relationships
4. `bulk_link_entities`: Link multiple entities to task in one call

### 8.5 Phase 5: Documentation and Examples (Medium Priority)

**Documentation:**
1. Update `CLAUDE.md` with entity system architecture
2. Add entity tools to MCP tool documentation
3. Create example workflows in `docs/examples/entity-workflows.md`
4. Update test documentation with entity test cases

---

## 9. Migration Strategy

### 9.1 Backward Compatibility

**Existing Installations:**
- Entity tables created on first connection (CREATE TABLE IF NOT EXISTS)
- No changes to existing `tasks` table schema
- Existing tasks continue to work without entities
- Zero downtime migration

**Rollback Strategy:**
- Entity system is additive (no breaking changes)
- Can disable entity tools in MCP configuration
- Can drop `entities` and `task_entity_links` tables to remove feature

### 9.2 Data Migration

**No data migration required:**
- Entity system is opt-in
- AI agents create entities as needed during development
- Historical tasks remain unlinked (valid state)

**Optional Migration Path:**
- Agents can retroactively create entities for existing tasks
- Example: Scan `file_references` field in tasks, create file entities, link them

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Test Coverage:**
1. Entity model validation (all entity types)
2. Metadata JSON validation and parsing
3. Link model validation
4. Unique constraint enforcement
5. Soft delete filtering
6. Tags normalization

### 10.2 Integration Tests

**Test Scenarios:**
1. Create entity → link to task → query task entities
2. Create task → create entity → link → query entity tasks
3. Delete entity with cascade → verify links deleted
4. Duplicate entity creation → verify unique constraint error
5. Link to non-existent task/entity → verify foreign key error

### 10.3 Performance Tests

**Benchmarks:**
1. Query 1000 entities by type (should use index)
2. Query task with 50 linked entities (should use index)
3. Bidirectional query (entity→tasks→entities) performance
4. Bulk linking performance (100 entities to 1 task)

---

## 11. Future Enhancements

### 11.1 Advanced Features (Low Priority)

1. **Entity Versioning**:
   - Track metadata changes over time
   - Snapshot entities when linked to completed tasks

2. **Entity Relationships**:
   - Link entities to other entities (not just tasks)
   - Model component dependencies, file imports, etc.

3. **Smart Suggestions**:
   - Auto-suggest entities based on task description
   - Detect file paths in task descriptions, offer to create entities

4. **Entity Templates**:
   - Predefined entity templates for common types
   - Custom entity types defined by users

5. **Bulk Operations**:
   - Bulk import entities from project files
   - Bulk link generation from Git history

### 11.2 Analytics and Reporting

1. **Entity Usage Statistics**:
   - Most-referenced entities
   - Entities with most task links
   - Orphaned entities (no links)

2. **Dependency Graphs**:
   - Visualize task-entity relationships
   - Component dependency trees

3. **Impact Analysis**:
   - Find all tasks affected by entity changes
   - Blast radius analysis for file modifications

---

## 12. Security and Privacy Considerations

### 12.1 Data Validation

- **Input Sanitization**: All entity fields validated through Pydantic models
- **JSON Injection Prevention**: Metadata validated as JSON before storage
- **SQL Injection Prevention**: Use parameterized queries exclusively

### 12.2 Access Control

- **Workspace Isolation**: Entities isolated per workspace (same pattern as tasks)
- **Soft Delete Safety**: 30-day retention before permanent deletion
- **Conversation Tracking**: `created_by` field tracks which agent created entity

### 12.3 Data Privacy

- **No Sensitive Data in Metadata**: Entities should not store credentials, API keys, etc.
- **Identifier Constraints**: Max 1000 chars to prevent data exfiltration via identifiers
- **Description Limits**: 10k char limit prevents token overflow attacks

---

## 13. Conclusion

The proposed Entity system provides a **flexible, type-safe, and performant** mechanism for AI agents to model domain concepts and link them to tasks. The design maintains architectural consistency with the existing Task MCP Server while enabling powerful new capabilities for context tracking, traceability, and domain modeling.

**Key Benefits:**
1. **Bidirectional Linking**: Query tasks by entity and entities by task
2. **Type Safety**: Pydantic validation with type-specific metadata schemas
3. **Extensibility**: Easy to add new entity types without schema changes
4. **Performance**: Indexed queries for common patterns
5. **Backward Compatible**: Zero breaking changes to existing deployments

**Recommended Next Steps:**
1. Review and approve design with stakeholders
2. Implement Phase 1 (schema and models) with comprehensive tests
3. Implement Phase 2 (CRUD tools) with integration tests
4. Implement Phase 3 (linking tools) with bidirectional query tests
5. Update documentation and examples
6. Gather feedback from AI agents using the system in production

---

## Appendix A: SQL Migration Script

```sql
-- Migration: Add Entity System
-- Version: 1.0.0
-- Date: 2025-10-27

-- Create entities table
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN (
        'file', 'pr', 'issue', 'component', 'vendor',
        'api', 'database', 'person', 'other'
    )),
    name TEXT NOT NULL,
    identifier TEXT,
    description TEXT,
    metadata TEXT,
    tags TEXT,
    created_by TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    UNIQUE(entity_type, identifier)
);

-- Create indexes for entities table
CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_identifier ON entities(identifier);
CREATE INDEX IF NOT EXISTS idx_entity_deleted ON entities(deleted_at);
CREATE INDEX IF NOT EXISTS idx_entity_tags ON entities(tags);

-- Create task_entity_links table
CREATE TABLE IF NOT EXISTS task_entity_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    entity_id INTEGER NOT NULL,
    link_type TEXT DEFAULT 'references',
    created_by TEXT,
    created_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (entity_id) REFERENCES entities(id),
    UNIQUE(task_id, entity_id, link_type)
);

-- Create indexes for task_entity_links table
CREATE INDEX IF NOT EXISTS idx_link_task ON task_entity_links(task_id);
CREATE INDEX IF NOT EXISTS idx_link_entity ON task_entity_links(entity_id);
CREATE INDEX IF NOT EXISTS idx_link_type ON task_entity_links(link_type);
CREATE INDEX IF NOT EXISTS idx_link_deleted ON task_entity_links(deleted_at);
```

---

## Appendix B: Example API Usage

```python
# Complete workflow example combining tasks and entities

# 1. Create a task
task = create_task(
    title="Implement user profile page",
    description="Build user profile page with edit capabilities",
    status="in_progress",
    tags="frontend ui"
)

# 2. Create file entities for files being modified
profile_view = create_entity(
    entity_type="file",
    name="Profile View Component",
    identifier="/src/components/ProfileView.tsx",
    metadata={"language": "typescript", "line_count": 150},
    tags="frontend react"
)

profile_api = create_entity(
    entity_type="file",
    name="Profile API Controller",
    identifier="/src/api/profile.py",
    metadata={"language": "python", "line_count": 80},
    tags="backend api"
)

# 3. Create PR entity
pr = create_entity(
    entity_type="pr",
    name="Add user profile page",
    identifier="PR-5678",
    metadata={
        "pr_number": 5678,
        "repository": "myorg/myapp",
        "url": "https://github.com/myorg/myapp/pull/5678",
        "status": "open"
    },
    tags="feature ui"
)

# 4. Link entities to task
link_entity_to_task(task_id=task["id"], entity_id=profile_view["id"], link_type="modifies")
link_entity_to_task(task_id=task["id"], entity_id=profile_api["id"], link_type="modifies")
link_entity_to_task(task_id=task["id"], entity_id=pr["id"], link_type="implements")

# 5. Query: Get all files modified by this task
modified_files = get_task_entities(
    task_id=task["id"],
    entity_type="file",
    link_type="modifies"
)
print(f"Modified {len(modified_files)} files")

# 6. Query: Find all tasks modifying ProfileView.tsx
related_tasks = get_entity_tasks(
    entity_id=profile_view["id"],
    link_type="modifies"
)
print(f"ProfileView.tsx is being modified by {len(related_tasks)} tasks")

# 7. Mark task as done
update_task(task_id=task["id"], status="done")

# 8. Update PR status
update_entity(
    entity_id=pr["id"],
    metadata={"status": "merged"}
)
```

---

**End of Document**
