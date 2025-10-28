# Entity System MVP v1 - Detailed Implementation Plan

**Date:** 2025-10-27 21:00
**Target Version:** v0.3.0
**Timeline:** 10 working days (2 calendar weeks)
**Based On:** Efficiency Review MVP Specification (2025-10-27 19:30)

---

## Executive Summary

This plan implements the Entity System MVP v1 with **51% scope reduction** from the original design while delivering **80% of core value**. The implementation focuses on the essential use case: **file tracking for tasks with extensibility via generic entity types**.

### Key Deliverables

- **2 Entity Types**: `file` and `other` (defer 7 specialized types)
- **1 Link Type**: `references` (defer 4 semantic types)
- **7 MCP Tools**: Core CRUD + linking operations
- **2 Database Tables**: `entities` + `task_entity_links`
- **Generic Metadata**: JSON blob (defer typed schemas)

### Timeline Overview

| Phase | Duration | Description |
|-------|----------|-------------|
| **Phase 1: Database Schema** | Days 1-2 | Add tables, indexes, migration |
| **Phase 2: Pydantic Models** | Days 2-3 | Add validation models |
| **Phase 3: MCP Tools** | Days 3-7 | Implement 7 core tools |
| **Phase 4: Testing** | Days 7-10 | Unit + integration tests |
| **Phase 5: Documentation** | Day 10 | Update docs + examples |

### Success Metrics

- ✅ All 54 existing tests pass (zero regressions)
- ✅ 30+ new entity system tests (70%+ coverage)
- ✅ Vendor use case validated with examples
- ✅ mypy --strict compliance (100% type safety)
- ✅ Production deployment ready

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Phase 1: Database Schema](#phase-1-database-schema-days-1-2)
3. [Phase 2: Pydantic Models](#phase-2-pydantic-models-days-2-3)
4. [Phase 3: MCP Tools](#phase-3-mcp-tools-days-3-7)
5. [Phase 4: Testing](#phase-4-testing-days-7-10)
6. [Phase 5: Documentation](#phase-5-documentation-day-10)
7. [Vendor Use Case Implementation](#vendor-use-case-implementation)
8. [Risk Mitigation](#risk-mitigation)
9. [Appendix: Complete Code Examples](#appendix-complete-code-examples)

---

## Architecture Overview

### Design Principles

The entity system follows **exact architectural patterns** from the existing task system:

| Pattern | Tasks Implementation | Entities Implementation |
|---------|---------------------|------------------------|
| **Soft Delete** | `deleted_at TIMESTAMP` | `deleted_at TIMESTAMP` |
| **Timestamps** | `created_at`, `updated_at` | `created_at`, `updated_at` |
| **Conversation Tracking** | `created_by TEXT` | `created_by TEXT` |
| **Tags** | Space-separated string | Space-separated string |
| **JSON Fields** | `depends_on`, `file_references` | `metadata` (generic JSON) |
| **Pydantic Models** | `Task`, `TaskCreate`, `TaskUpdate` | `Entity`, `EntityCreate`, `EntityUpdate` |
| **WAL Mode** | Enabled | Enabled (same connection) |

### Database Architecture

```
project_database.db (per workspace)
├── tasks                 # Existing table
├── entities              # NEW - Domain concepts (files, vendors, etc.)
└── task_entity_links     # NEW - Many-to-many junction table
```

**Key Architectural Decisions:**

1. **2-Table Design**: Normalized many-to-many pattern (not JSON field)
2. **Generic Types**: Start with `file` + `other`, expand based on usage
3. **Bidirectional Queries**: Fast lookups in both directions via indexes
4. **Zero-Config Migration**: `CREATE TABLE IF NOT EXISTS` auto-creates schema
5. **Same WAL Connection**: No new concurrency concerns

---

## Phase 1: Database Schema (Days 1-2)

### Objectives

- Add `entities` table with 2 entity types
- Add `task_entity_links` junction table
- Create 6 performance indexes
- Validate schema with migration tests
- Zero breaking changes to existing schema

### Files Modified

- `src/task_mcp/database.py` (~80 LOC added)

### 1.1 Entities Table Schema

**Location:** `src/task_mcp/database.py:init_schema()`

Add after tasks table creation (line ~118):

```python
def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize schema with tasks, entities, and links tables."""

    # Existing tasks table creation...
    # (lines 79-118)

    # === NEW: Create entities table ===
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL CHECK(entity_type IN ('file', 'other')),
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

    # === NEW: Create indexes for entities ===
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_type
        ON entities(entity_type)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_identifier
        ON entities(identifier)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_deleted
        ON entities(deleted_at)
    """)

    # === NEW: Create task_entity_links junction table ===
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_entity_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            entity_id INTEGER NOT NULL,
            created_by TEXT,
            created_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
            UNIQUE(task_id, entity_id)
        )
    """)

    # === NEW: Create indexes for links ===
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_link_task
        ON task_entity_links(task_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_link_entity
        ON task_entity_links(entity_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_link_deleted
        ON task_entity_links(deleted_at)
    """)

    # Commit all schema changes
    conn.commit()
```

**Schema Design Notes:**

1. **entity_type CHECK Constraint**: Enforces only `'file'` and `'other'` types
2. **UNIQUE(entity_type, identifier)**: Prevents duplicate entities (e.g., same file path)
3. **metadata TEXT**: Generic JSON blob (no typed validation in MVP)
4. **ON DELETE CASCADE**: Links automatically deleted when task/entity deleted
5. **UNIQUE(task_id, entity_id)**: Prevents duplicate links

### 1.2 Schema Field Specifications

#### Entities Table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique entity ID |
| `entity_type` | TEXT | NOT NULL, CHECK IN ('file', 'other') | Entity category |
| `name` | TEXT | NOT NULL | Human-readable name |
| `identifier` | TEXT | NULL, UNIQUE with entity_type | Unique identifier (file path, ID, etc.) |
| `description` | TEXT | NULL, max 10k chars (app validation) | Optional description |
| `metadata` | TEXT | NULL, JSON blob | Generic metadata (language, formats, etc.) |
| `tags` | TEXT | NULL, space-separated | Normalized tags |
| `created_by` | TEXT | NULL | Conversation/session ID |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp (ISO 8601) |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |
| `deleted_at` | TIMESTAMP | NULL | Soft delete timestamp |

#### Task Entity Links Table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique link ID |
| `task_id` | INTEGER | NOT NULL, FK to tasks(id) | Task reference |
| `entity_id` | INTEGER | NOT NULL, FK to entities(id) | Entity reference |
| `created_by` | TEXT | NULL | Conversation/session ID |
| `created_at` | TIMESTAMP | NOT NULL | Link creation timestamp |
| `deleted_at` | TIMESTAMP | NULL | Soft delete timestamp |

### 1.3 Index Strategy

**Purpose:** Enable fast bidirectional queries and filtering

```sql
-- Entity Indexes (3)
CREATE INDEX idx_entity_type ON entities(entity_type);        -- Filter by type
CREATE INDEX idx_entity_identifier ON entities(identifier);   -- Lookup by identifier
CREATE INDEX idx_entity_deleted ON entities(deleted_at);      -- Exclude soft-deleted

-- Link Indexes (3)
CREATE INDEX idx_link_task ON task_entity_links(task_id);     -- Get entities for task
CREATE INDEX idx_link_entity ON task_entity_links(entity_id); -- Get tasks for entity
CREATE INDEX idx_link_deleted ON task_entity_links(deleted_at); -- Exclude soft-deleted
```

**Query Performance:**

| Query | Index Used | Complexity |
|-------|------------|------------|
| Get entities for task | `idx_link_task` | O(log n) |
| Get tasks for entity | `idx_link_entity` | O(log n) |
| Filter by entity type | `idx_entity_type` | O(log n) |
| Lookup by identifier | `idx_entity_identifier` | O(log n) |

### 1.4 Migration Testing

**Test File:** `tests/test_schema_migration.py` (NEW)

```python
"""Test schema migration and backward compatibility."""

import sqlite3
import tempfile
from pathlib import Path

def test_schema_creates_entities_table():
    """Verify entities table is created with correct schema."""
    from task_mcp.database import init_schema

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))

        init_schema(conn)

        # Verify entities table exists
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='entities'
        """)
        assert cursor.fetchone() is not None

        # Verify columns
        cursor.execute("PRAGMA table_info(entities)")
        columns = {row[1] for row in cursor.fetchall()}
        expected = {
            'id', 'entity_type', 'name', 'identifier',
            'description', 'metadata', 'tags', 'created_by',
            'created_at', 'updated_at', 'deleted_at'
        }
        assert columns == expected

        conn.close()

def test_schema_creates_links_table():
    """Verify task_entity_links table is created."""
    from task_mcp.database import init_schema

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))

        init_schema(conn)

        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='task_entity_links'
        """)
        assert cursor.fetchone() is not None

        conn.close()

def test_schema_creates_indexes():
    """Verify all 6 indexes are created."""
    from task_mcp.database import init_schema

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))

        init_schema(conn)

        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_%entity%'
        """)
        indexes = {row[0] for row in cursor.fetchall()}
        expected = {
            'idx_entity_type',
            'idx_entity_identifier',
            'idx_entity_deleted',
            'idx_link_task',
            'idx_link_entity',
            'idx_link_deleted'
        }
        assert indexes == expected

        conn.close()

def test_existing_tasks_unaffected():
    """Verify existing task operations still work."""
    from task_mcp.database import get_connection
    from task_mcp.server import create_task, list_tasks

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create task (should work with new schema)
        task = create_task(
            title="Test Task",
            workspace_path=tmpdir,
            description="Test description"
        )

        assert task['id'] is not None
        assert task['title'] == "Test Task"

        # List tasks (should work)
        tasks = list_tasks(workspace_path=tmpdir)
        assert len(tasks) == 1
```

### 1.5 Phase 1 Acceptance Criteria

- [ ] `entities` table created with 11 fields
- [ ] `task_entity_links` table created with 6 fields
- [ ] 6 indexes created (3 entity + 3 link)
- [ ] `entity_type` CHECK constraint enforces `('file', 'other')`
- [ ] UNIQUE constraint on `(entity_type, identifier)`
- [ ] Foreign keys enforce referential integrity
- [ ] All 54 existing tests pass (zero regressions)
- [ ] 4 new schema migration tests pass
- [ ] mypy validation passes

### 1.6 Phase 1 Timeline

| Task | Duration | Output |
|------|----------|--------|
| Add entities table DDL | 2 hours | Schema in database.py |
| Add links table DDL | 1 hour | Schema in database.py |
| Add 6 indexes | 1 hour | Index DDL statements |
| Write migration tests | 3 hours | test_schema_migration.py |
| Run regression tests | 1 hour | Confirm 54 tests pass |
| **TOTAL** | **8 hours** | **~80 LOC** |

---

## Phase 2: Pydantic Models (Days 2-3)

### Objectives

- Add `Entity`, `EntityCreate`, `EntityUpdate` models
- Implement field validation (type, length, JSON)
- Mirror existing task model patterns
- Add helper methods for metadata parsing

### Files Modified

- `src/task_mcp/models.py` (~200 LOC added)

### 2.1 Entity Model Definition

**Location:** `src/task_mcp/models.py` (add after `ProjectInfoWithStats` class, line ~535)

```python
# === NEW: Entity System Models ===

# Constants
VALID_ENTITY_TYPES = ("file", "other")

class Entity(BaseModel):
    """
    Entity model representing domain concepts linked to tasks.

    Entities can represent files, vendors, APIs, or any domain concept
    that tasks reference. The MVP supports two types:
    - file: File paths in the codebase
    - other: Generic catch-all for domain-specific entities

    Examples:
        # File entity
        Entity(
            entity_type="file",
            name="Login Controller",
            identifier="/src/auth/login.py",
            metadata='{"language": "python", "line_count": 250}',
            tags="auth backend"
        )

        # Vendor entity (using "other" type)
        Entity(
            entity_type="other",
            name="ABC Insurance Vendor",
            identifier="ABC-INS",
            metadata='{"vendor_code": "ABC", "format": "xlsx", "phase": "active"}',
            tags="vendor insurance commission"
        )
    """

    model_config = ConfigDict(
        strict=False,
        validate_assignment=True,
        extra='forbid',
    )

    # Core fields
    id: Optional[int] = Field(None, description="Entity ID (auto-generated)")
    entity_type: str = Field(
        ...,
        description="Entity type: 'file' or 'other'"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Human-readable entity name"
    )
    identifier: Optional[str] = Field(
        None,
        max_length=1000,
        description="Unique identifier (file path, vendor code, etc.)"
    )
    description: Optional[str] = Field(
        None,
        description="Optional description (max 10,000 chars)"
    )

    # Metadata and organization
    metadata: Optional[str] = Field(
        None,
        description="Generic JSON metadata (freeform structure)"
    )
    tags: Optional[str] = Field(
        None,
        description="Space-separated tags (normalized to lowercase)"
    )

    # Audit fields
    created_by: Optional[str] = Field(
        None,
        description="Conversation/session ID that created this entity"
    )
    created_at: Optional[datetime] = Field(
        None,
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Last update timestamp"
    )
    deleted_at: Optional[datetime] = Field(
        None,
        description="Soft delete timestamp"
    )

    # Field Validators

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity_type is one of the allowed values."""
        if v not in VALID_ENTITY_TYPES:
            raise ValueError(
                f"entity_type must be one of {VALID_ENTITY_TYPES}, got '{v}'"
            )
        return v

    @field_validator('description')
    @classmethod
    def validate_description_length(cls, v: Optional[str]) -> Optional[str]:
        """Enforce maximum description length of 10,000 characters."""
        if v is not None and len(v) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters "
                f"(got {len(v)} characters)"
            )
        return v

    @field_validator('tags')
    @classmethod
    def validate_and_normalize_tags(cls, v: Optional[str]) -> Optional[str]:
        """Normalize tags to lowercase with single spaces."""
        if v is None:
            return None
        return normalize_tags(v)

    @field_validator('metadata')
    @classmethod
    def validate_metadata_json(cls, v: Optional[str]) -> Optional[str]:
        """Validate metadata is valid JSON syntax."""
        if v is None or v == "":
            return None
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"metadata must be valid JSON: {e}") from e

    # Helper Methods

    def get_metadata_dict(self) -> dict[str, Any]:
        """
        Parse metadata JSON string into dictionary.

        Returns:
            Dictionary of metadata, or empty dict if no metadata

        Examples:
            >>> entity.metadata = '{"language": "python", "loc": 250}'
            >>> entity.get_metadata_dict()
            {"language": "python", "loc": 250}
        """
        if not self.metadata:
            return {}
        try:
            result: dict[str, Any] = json.loads(self.metadata)
            return result
        except json.JSONDecodeError:
            return {}


class EntityCreate(BaseModel):
    """
    Model for creating new entities.

    Subset of Entity fields that can be provided during creation.
    Other fields (id, timestamps) are auto-generated.
    """

    model_config = ConfigDict(
        strict=False,
        extra='forbid',
    )

    entity_type: str
    name: str = Field(min_length=1, max_length=500)
    identifier: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = None
    metadata: Optional[str] = None
    tags: Optional[str] = None
    created_by: Optional[str] = None

    # Reuse validators from Entity model
    _validate_entity_type = field_validator('entity_type')(
        Entity.validate_entity_type.__func__  # type: ignore[attr-defined]
    )
    _validate_description = field_validator('description')(
        Entity.validate_description_length.__func__  # type: ignore[attr-defined]
    )
    _validate_tags = field_validator('tags')(
        Entity.validate_and_normalize_tags.__func__  # type: ignore[attr-defined]
    )
    _validate_metadata = field_validator('metadata')(
        Entity.validate_metadata_json.__func__  # type: ignore[attr-defined]
    )


class EntityUpdate(BaseModel):
    """
    Model for updating existing entities.

    All fields are optional - only provided fields will be updated.
    """

    model_config = ConfigDict(
        strict=False,
        extra='forbid',
    )

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    identifier: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = None
    metadata: Optional[str] = None
    tags: Optional[str] = None

    # Reuse validators from Entity model
    _validate_description = field_validator('description')(
        Entity.validate_description_length.__func__  # type: ignore[attr-defined]
    )
    _validate_tags = field_validator('tags')(
        Entity.validate_and_normalize_tags.__func__  # type: ignore[attr-defined]
    )
    _validate_metadata = field_validator('metadata')(
        Entity.validate_metadata_json.__func__  # type: ignore[attr-defined]
    )
```

### 2.2 Model Validation Rules

**Validation Summary:**

| Field | Validation Rule | Error Message |
|-------|----------------|---------------|
| `entity_type` | Must be `'file'` or `'other'` | "entity_type must be one of ('file', 'other')" |
| `name` | 1-500 characters | "name must be between 1-500 chars" |
| `identifier` | 0-1000 characters | "identifier max 1000 chars" |
| `description` | 0-10,000 characters | "Description max 10,000 chars" |
| `metadata` | Valid JSON syntax | "metadata must be valid JSON: {error}" |
| `tags` | Normalized to lowercase | (auto-normalized, no error) |

### 2.3 Metadata JSON Patterns

**MVP Approach:** Generic JSON with documentation (no typed schemas)

**Common Patterns (Documented in Tool Docstrings):**

```python
# File entity metadata
metadata = {
    "language": "python",
    "line_count": 250,
    "owner": "alice",
    "last_modified": "2025-10-27"
}

# Vendor entity metadata (commission processing)
metadata = {
    "vendor_code": "ABC",
    "phase": "active",  # active, testing, deprecated
    "brands": ["brand_a", "brand_b"],
    "formats": ["xlsx", "pdf"],
    "contact_email": "vendor@example.com"
}

# Other entity metadata (freeform)
metadata = {
    "type": "api_endpoint",
    "url": "https://api.example.com/v1/users",
    "authentication": "bearer_token"
}
```

### 2.4 Model Testing

**Test File:** `tests/test_models_entity.py` (NEW)

```python
"""Test entity Pydantic models."""

import json
import pytest
from task_mcp.models import Entity, EntityCreate, EntityUpdate, VALID_ENTITY_TYPES

def test_entity_valid_file():
    """Test creating valid file entity."""
    entity = Entity(
        id=1,
        entity_type="file",
        name="Login Controller",
        identifier="/src/auth/login.py",
        tags="auth backend"
    )
    assert entity.entity_type == "file"
    assert entity.name == "Login Controller"
    assert entity.tags == "auth backend"

def test_entity_valid_other():
    """Test creating valid 'other' entity."""
    entity = Entity(
        id=2,
        entity_type="other",
        name="ABC Vendor",
        identifier="ABC-INS",
        metadata='{"vendor_code": "ABC"}'
    )
    assert entity.entity_type == "other"
    assert entity.get_metadata_dict() == {"vendor_code": "ABC"}

def test_entity_invalid_type():
    """Test entity_type validation rejects invalid types."""
    with pytest.raises(ValueError, match="entity_type must be one of"):
        Entity(
            entity_type="invalid_type",
            name="Test",
        )

def test_entity_description_too_long():
    """Test description length validation."""
    with pytest.raises(ValueError, match="Description cannot exceed 10,000"):
        Entity(
            entity_type="file",
            name="Test",
            description="x" * 10_001
        )

def test_entity_metadata_invalid_json():
    """Test metadata JSON validation."""
    with pytest.raises(ValueError, match="metadata must be valid JSON"):
        Entity(
            entity_type="file",
            name="Test",
            metadata="{invalid json"
        )

def test_entity_tags_normalized():
    """Test tags are normalized to lowercase."""
    entity = Entity(
        entity_type="file",
        name="Test",
        tags="  Python   Django  REST  "
    )
    assert entity.tags == "python django rest"

def test_entity_get_metadata_dict():
    """Test metadata dictionary helper."""
    entity = Entity(
        entity_type="file",
        name="Test",
        metadata='{"language": "python", "loc": 250}'
    )
    metadata = entity.get_metadata_dict()
    assert metadata == {"language": "python", "loc": 250}

def test_entity_create_valid():
    """Test EntityCreate model."""
    data = EntityCreate(
        entity_type="file",
        name="Test File",
        identifier="/test.py"
    )
    assert data.entity_type == "file"
    assert data.name == "Test File"

def test_entity_update_partial():
    """Test EntityUpdate allows partial updates."""
    data = EntityUpdate(
        name="Updated Name"
        # All other fields None (not updated)
    )
    assert data.name == "Updated Name"
    assert data.description is None
```

### 2.5 Phase 2 Acceptance Criteria

- [ ] `Entity` model with 11 fields and 4 validators
- [ ] `EntityCreate` model with required field validation
- [ ] `EntityUpdate` model with optional field validation
- [ ] `get_metadata_dict()` helper method
- [ ] 10+ model validation tests passing
- [ ] mypy --strict compliance (100% type safety)
- [ ] Zero regressions (54 existing tests pass)

### 2.6 Phase 2 Timeline

| Task | Duration | Output |
|------|----------|--------|
| Add Entity model | 2 hours | ~100 LOC |
| Add EntityCreate/Update | 1 hour | ~50 LOC |
| Add field validators | 2 hours | 4 validators |
| Write model tests | 3 hours | test_models_entity.py |
| mypy validation | 1 hour | Type safety confirmed |
| **TOTAL** | **9 hours** | **~200 LOC** |

---

## Phase 3: MCP Tools (Days 3-7)

### Objectives

- Implement 7 core MCP tools
- Follow exact patterns from task tools
- Enable file tracking + vendor use cases
- Validate bidirectional queries

### Files Modified

- `src/task_mcp/server.py` (~450 LOC added)

### 3.1 Tool Overview

| Tool | Purpose | Lines | Complexity |
|------|---------|-------|------------|
| `create_entity` | Create new entity | ~70 | Medium |
| `update_entity` | Update entity fields | ~80 | Medium |
| `get_entity` | Get single entity by ID | ~35 | Low |
| `list_entities` | List/filter entities | ~50 | Medium |
| `delete_entity` | Soft delete entity | ~45 | Medium |
| `link_entity_to_task` | Create task-entity link | ~60 | Medium |
| `get_task_entities` | Get entities for task | ~45 | Medium |
| **TOTAL** | | **~385 LOC** | |

### 3.2 Tool 1: create_entity

**Location:** `src/task_mcp/server.py` (add after `cleanup_deleted_tasks`, line ~889)

```python
# === NEW: Entity System Tools ===

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
    Create a new entity.

    Entities represent domain concepts that tasks can reference:
    - file: Files in the codebase
    - other: Generic entities (vendors, APIs, components, etc.)

    Args:
        entity_type: Type of entity ('file' or 'other')
        name: Human-readable name (required, 1-500 chars)
        ctx: FastMCP context (auto-injected)
        workspace_path: Optional workspace path (auto-detected)
        identifier: Unique identifier (file path, vendor code, etc.)
        description: Optional description (max 10k chars)
        metadata: Generic JSON metadata dict
        tags: Space-separated tags
        created_by: Conversation ID (auto-captured if not provided)

    Returns:
        Created entity object with all fields

    Examples:
        # File entity
        create_entity(
            entity_type="file",
            name="Login Controller",
            identifier="/src/auth/login.py",
            metadata={"language": "python", "line_count": 250},
            tags="auth backend"
        )

        # Vendor entity (commission processing)
        create_entity(
            entity_type="other",
            name="ABC Insurance Vendor",
            identifier="ABC-INS",
            metadata={
                "vendor_code": "ABC",
                "phase": "active",
                "brands": ["brand_a", "brand_b"],
                "formats": ["xlsx", "pdf"]
            },
            tags="vendor insurance commission"
        )

    Raises:
        ValueError: If validation fails or duplicate identifier
    """
    import json
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .models import EntityCreate
    from .utils import resolve_workspace, validate_description_length

    # Auto-register project
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Auto-capture session ID
    if created_by is None and ctx is not None:
        created_by = ctx.session_id

    # Validate description length
    if description:
        validate_description_length(description)

    # Convert metadata dict to JSON string
    metadata_str = json.dumps(metadata) if metadata else None

    # Validate with Pydantic model
    entity_data = EntityCreate(
        entity_type=entity_type,
        name=name,
        identifier=identifier,
        description=description,
        metadata=metadata_str,
        tags=tags,
        created_by=created_by,
    )

    # Get database connection
    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    try:
        # Insert entity
        cursor.execute(
            """
            INSERT INTO entities (
                entity_type, name, identifier, description, metadata,
                tags, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entity_data.entity_type,
                entity_data.name,
                entity_data.identifier,
                entity_data.description,
                entity_data.metadata,
                entity_data.tags,
                entity_data.created_by,
                now,
                now,
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

### 3.3 Tool 2: update_entity

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
    Update an existing entity.

    Args:
        entity_id: Entity ID to update (required)
        workspace_path: Optional workspace path (auto-detected)
        name: Updated name
        identifier: Updated identifier
        description: Updated description (max 10k chars)
        metadata: Updated metadata dict
        tags: Updated space-separated tags

    Returns:
        Updated entity object

    Raises:
        ValueError: If entity not found or validation fails

    Examples:
        # Update file metadata
        update_entity(
            entity_id=1,
            metadata={"language": "python", "line_count": 275}
        )

        # Update vendor phase
        update_entity(
            entity_id=2,
            metadata={"vendor_code": "ABC", "phase": "deprecated"}
        )
    """
    import json
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .models import EntityUpdate
    from .utils import resolve_workspace, validate_description_length

    # Auto-register project
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Validate description length
    if description is not None:
        validate_description_length(description)

    # Convert metadata dict to JSON string
    metadata_str = json.dumps(metadata) if metadata is not None else None

    # Validate with Pydantic model
    update_data = EntityUpdate(
        name=name,
        identifier=identifier,
        description=description,
        metadata=metadata_str,
        tags=tags,
    )

    # Get database connection
    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Check entity exists
        cursor.execute(
            "SELECT * FROM entities WHERE id = ? AND deleted_at IS NULL",
            (entity_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Entity {entity_id} not found or has been deleted")

        # Build UPDATE statement
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

        # Always update updated_at
        update_fields.append("updated_at = ?")
        update_params.append(datetime.now().isoformat())

        # Execute update
        if update_fields:
            update_params.append(entity_id)
            query = f"UPDATE entities SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_params)
            conn.commit()

        # Fetch updated entity
        cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()

        return dict(row)
    finally:
        conn.close()
```

### 3.4 Tool 3: get_entity

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
        workspace_path: Optional workspace path (auto-detected)

    Returns:
        Entity object with all fields

    Raises:
        ValueError: If entity not found or soft-deleted

    Examples:
        entity = get_entity(entity_id=1)
        print(entity['name'])  # "Login Controller"
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM entities WHERE id = ? AND deleted_at IS NULL",
            (entity_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Entity {entity_id} not found or has been deleted")

        return dict(row)
    finally:
        conn.close()
```

### 3.5 Tool 4: list_entities

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
        List of entity objects matching filters

    Examples:
        # List all file entities
        files = list_entities(entity_type="file")

        # List vendor entities
        vendors = list_entities(entity_type="other", tags="vendor")
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project
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
            query += " AND tags LIKE ?"
            params.append(f"%{tags}%")

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()
```

### 3.6 Tool 5: delete_entity

```python
@mcp.tool()
def delete_entity(
    entity_id: int,
    workspace_path: str | None = None,
    cascade: bool = False,
) -> dict[str, Any]:
    """
    Soft delete an entity.

    Args:
        entity_id: Entity ID to delete
        workspace_path: Optional workspace path (auto-detected)
        cascade: If True, also soft-delete all task links

    Returns:
        Success confirmation with deleted counts

    Raises:
        ValueError: If entity not found or already deleted

    Examples:
        # Delete entity and its links
        result = delete_entity(entity_id=1, cascade=True)
        print(result['deleted_links'])  # 3
    """
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Check entity exists
        cursor.execute(
            "SELECT id FROM entities WHERE id = ? AND deleted_at IS NULL",
            (entity_id,)
        )
        if not cursor.fetchone():
            raise ValueError(f"Entity {entity_id} not found or already deleted")

        now = datetime.now().isoformat()

        # Delete the entity
        cursor.execute(
            "UPDATE entities SET deleted_at = ? WHERE id = ?",
            (now, entity_id)
        )

        deleted_links = 0

        # Cascade delete links if requested
        if cascade:
            cursor.execute(
                """UPDATE task_entity_links
                   SET deleted_at = ?
                   WHERE entity_id = ? AND deleted_at IS NULL""",
                (now, entity_id)
            )
            deleted_links = cursor.rowcount

        conn.commit()

        return {
            "success": True,
            "entity_id": entity_id,
            "deleted_links": deleted_links,
            "cascade": cascade,
        }
    finally:
        conn.close()
```

### 3.7 Tool 6: link_entity_to_task

```python
@mcp.tool()
def link_entity_to_task(
    task_id: int,
    entity_id: int,
    ctx: Context | None = None,
    workspace_path: str | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """
    Create a link between task and entity.

    This establishes a "references" relationship, indicating the task
    is working with or modifying the entity.

    Args:
        task_id: Task ID to link
        entity_id: Entity ID to link
        ctx: FastMCP context (auto-injected)
        workspace_path: Optional workspace path (auto-detected)
        created_by: Conversation ID (auto-captured if not provided)

    Returns:
        Created link object

    Raises:
        ValueError: If task/entity not found or link already exists

    Examples:
        # Link file entity to task
        link = link_entity_to_task(task_id=42, entity_id=1)

        # Link vendor entity to commission processing task
        link = link_entity_to_task(task_id=99, entity_id=2)
    """
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Auto-capture session ID
    if created_by is None and ctx is not None:
        created_by = ctx.session_id

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Verify task exists
        cursor.execute(
            "SELECT id FROM tasks WHERE id = ? AND deleted_at IS NULL",
            (task_id,)
        )
        if not cursor.fetchone():
            raise ValueError(f"Task {task_id} not found")

        # Verify entity exists
        cursor.execute(
            "SELECT id FROM entities WHERE id = ? AND deleted_at IS NULL",
            (entity_id,)
        )
        if not cursor.fetchone():
            raise ValueError(f"Entity {entity_id} not found")

        now = datetime.now().isoformat()

        # Create link (UNIQUE constraint prevents duplicates)
        cursor.execute(
            """
            INSERT INTO task_entity_links (
                task_id, entity_id, created_by, created_at
            ) VALUES (?, ?, ?, ?)
            """,
            (task_id, entity_id, created_by, now)
        )

        link_id = cursor.lastrowid
        conn.commit()

        # Fetch created link
        cursor.execute(
            "SELECT * FROM task_entity_links WHERE id = ?",
            (link_id,)
        )
        row = cursor.fetchone()

        return dict(row)
    finally:
        conn.close()
```

### 3.8 Tool 7: get_task_entities

```python
@mcp.tool()
def get_task_entities(
    task_id: int,
    workspace_path: str | None = None,
    entity_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get all entities linked to a task.

    Returns entities with link metadata (created_at, created_by).

    Args:
        task_id: Task ID to query
        workspace_path: Optional workspace path (auto-detected)
        entity_type: Optional filter by entity type

    Returns:
        List of entity objects linked to the task

    Raises:
        ValueError: If task not found

    Examples:
        # Get all entities for task
        entities = get_task_entities(task_id=42)

        # Get only file entities
        files = get_task_entities(task_id=42, entity_type="file")
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Verify task exists
        cursor.execute(
            "SELECT id FROM tasks WHERE id = ? AND deleted_at IS NULL",
            (task_id,)
        )
        if not cursor.fetchone():
            raise ValueError(f"Task {task_id} not found")

        # Query entities via junction table
        query = """
            SELECT e.*, l.created_at as link_created_at, l.created_by as link_created_by
            FROM entities e
            JOIN task_entity_links l ON e.id = l.entity_id
            WHERE l.task_id = ?
              AND e.deleted_at IS NULL
              AND l.deleted_at IS NULL
        """
        params: list[int | str] = [task_id]

        if entity_type:
            query += " AND e.entity_type = ?"
            params.append(entity_type)

        query += " ORDER BY l.created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()
```

### 3.9 Phase 3 Acceptance Criteria

- [ ] All 7 tools implemented with docstrings
- [ ] create_entity supports file + vendor use cases
- [ ] update_entity allows partial updates
- [ ] get_entity retrieves single entity by ID
- [ ] list_entities filters by type and tags
- [ ] delete_entity soft-deletes with cascade option
- [ ] link_entity_to_task creates bidirectional link
- [ ] get_task_entities returns entities for task
- [ ] All tools follow task tool patterns
- [ ] Auto-capture conversation ID from context
- [ ] Auto-register project on every call

### 3.10 Phase 3 Timeline

| Task | Duration | Output |
|------|----------|--------|
| Implement create_entity | 4 hours | ~70 LOC |
| Implement update_entity | 4 hours | ~80 LOC |
| Implement get_entity | 2 hours | ~35 LOC |
| Implement list_entities | 3 hours | ~50 LOC |
| Implement delete_entity | 3 hours | ~45 LOC |
| Implement link_entity_to_task | 4 hours | ~60 LOC |
| Implement get_task_entities | 3 hours | ~45 LOC |
| Integration testing | 4 hours | Manual verification |
| **TOTAL** | **27 hours** | **~385 LOC** |

---

## Phase 4: Testing (Days 7-10)

### Objectives

- Achieve 70%+ test coverage for entity system
- Validate file tracking workflow
- Validate vendor use case workflow
- Ensure zero regressions

### Files Modified

- `tests/test_entity_crud.py` (NEW, ~200 LOC)
- `tests/test_entity_links.py` (NEW, ~150 LOC)
- `tests/test_entity_workflows.py` (NEW, ~150 LOC)

### 4.1 Test Suite Structure

| Test File | Purpose | Test Count | LOC |
|-----------|---------|------------|-----|
| `test_schema_migration.py` | Schema creation | 4 | ~100 |
| `test_models_entity.py` | Model validation | 10 | ~150 |
| `test_entity_crud.py` | CRUD operations | 15 | ~200 |
| `test_entity_links.py` | Link operations | 10 | ~150 |
| `test_entity_workflows.py` | End-to-end workflows | 8 | ~150 |
| **TOTAL** | | **47** | **~750 LOC** |

### 4.2 CRUD Tests

**File:** `tests/test_entity_crud.py`

```python
"""Test entity CRUD operations."""

import json
import pytest
import tempfile
from task_mcp.server import (
    create_entity,
    update_entity,
    get_entity,
    list_entities,
    delete_entity,
)

@pytest.fixture
def workspace():
    """Provide temporary workspace for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_create_file_entity(workspace):
    """Test creating file entity."""
    entity = create_entity(
        entity_type="file",
        name="Login Controller",
        workspace_path=workspace,
        identifier="/src/auth/login.py",
        metadata={"language": "python", "line_count": 250},
        tags="auth backend"
    )

    assert entity['id'] is not None
    assert entity['entity_type'] == "file"
    assert entity['name'] == "Login Controller"
    assert entity['identifier'] == "/src/auth/login.py"

    # Verify metadata JSON
    metadata = json.loads(entity['metadata'])
    assert metadata['language'] == "python"
    assert metadata['line_count'] == 250

    # Verify tags normalized
    assert entity['tags'] == "auth backend"

def test_create_vendor_entity(workspace):
    """Test creating vendor entity (commission use case)."""
    entity = create_entity(
        entity_type="other",
        name="ABC Insurance Vendor",
        workspace_path=workspace,
        identifier="ABC-INS",
        metadata={
            "vendor_code": "ABC",
            "phase": "active",
            "brands": ["brand_a", "brand_b"],
            "formats": ["xlsx", "pdf"]
        },
        tags="vendor insurance commission"
    )

    assert entity['entity_type'] == "other"
    assert entity['name'] == "ABC Insurance Vendor"

    metadata = json.loads(entity['metadata'])
    assert metadata['vendor_code'] == "ABC"
    assert metadata['phase'] == "active"
    assert len(metadata['brands']) == 2

def test_create_entity_duplicate_identifier(workspace):
    """Test UNIQUE constraint on (entity_type, identifier)."""
    create_entity(
        entity_type="file",
        name="Original",
        workspace_path=workspace,
        identifier="/duplicate.py"
    )

    # Should raise unique constraint error
    with pytest.raises(Exception):  # sqlite3.IntegrityError
        create_entity(
            entity_type="file",
            name="Duplicate",
            workspace_path=workspace,
            identifier="/duplicate.py"
        )

def test_update_entity_metadata(workspace):
    """Test updating entity metadata."""
    entity = create_entity(
        entity_type="file",
        name="Test File",
        workspace_path=workspace,
        metadata={"version": "1.0"}
    )

    updated = update_entity(
        entity_id=entity['id'],
        workspace_path=workspace,
        metadata={"version": "2.0", "author": "alice"}
    )

    metadata = json.loads(updated['metadata'])
    assert metadata['version'] == "2.0"
    assert metadata['author'] == "alice"

def test_get_entity(workspace):
    """Test retrieving single entity."""
    created = create_entity(
        entity_type="file",
        name="Test",
        workspace_path=workspace
    )

    entity = get_entity(
        entity_id=created['id'],
        workspace_path=workspace
    )

    assert entity['id'] == created['id']
    assert entity['name'] == "Test"

def test_get_entity_not_found(workspace):
    """Test get_entity raises error for missing entity."""
    with pytest.raises(ValueError, match="not found"):
        get_entity(entity_id=99999, workspace_path=workspace)

def test_list_entities_filter_by_type(workspace):
    """Test filtering entities by type."""
    create_entity(
        entity_type="file",
        name="File 1",
        workspace_path=workspace
    )
    create_entity(
        entity_type="other",
        name="Vendor 1",
        workspace_path=workspace
    )

    files = list_entities(
        workspace_path=workspace,
        entity_type="file"
    )

    assert len(files) == 1
    assert files[0]['entity_type'] == "file"

def test_list_entities_filter_by_tags(workspace):
    """Test filtering entities by tags."""
    create_entity(
        entity_type="other",
        name="Vendor 1",
        workspace_path=workspace,
        tags="vendor insurance"
    )
    create_entity(
        entity_type="other",
        name="Vendor 2",
        workspace_path=workspace,
        tags="vendor healthcare"
    )

    vendors = list_entities(
        workspace_path=workspace,
        tags="vendor"
    )

    assert len(vendors) == 2

def test_delete_entity(workspace):
    """Test soft delete entity."""
    entity = create_entity(
        entity_type="file",
        name="To Delete",
        workspace_path=workspace
    )

    result = delete_entity(
        entity_id=entity['id'],
        workspace_path=workspace
    )

    assert result['success'] is True

    # Verify soft-deleted (not returned by list)
    entities = list_entities(workspace_path=workspace)
    assert len(entities) == 0

    # Verify raises error on get
    with pytest.raises(ValueError, match="deleted"):
        get_entity(entity_id=entity['id'], workspace_path=workspace)

def test_delete_entity_cascade_links(workspace):
    """Test cascade delete of links."""
    from task_mcp.server import create_task, link_entity_to_task

    task = create_task(title="Test Task", workspace_path=workspace)
    entity = create_entity(
        entity_type="file",
        name="Test",
        workspace_path=workspace
    )

    link_entity_to_task(
        task_id=task['id'],
        entity_id=entity['id'],
        workspace_path=workspace
    )

    result = delete_entity(
        entity_id=entity['id'],
        workspace_path=workspace,
        cascade=True
    )

    assert result['deleted_links'] == 1
```

### 4.3 Link Tests

**File:** `tests/test_entity_links.py`

```python
"""Test entity linking operations."""

import pytest
import tempfile
from task_mcp.server import (
    create_task,
    create_entity,
    link_entity_to_task,
    get_task_entities,
)

@pytest.fixture
def workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_link_entity_to_task(workspace):
    """Test creating task-entity link."""
    task = create_task(
        title="Implement Login",
        workspace_path=workspace
    )
    entity = create_entity(
        entity_type="file",
        name="Login Controller",
        workspace_path=workspace,
        identifier="/src/auth/login.py"
    )

    link = link_entity_to_task(
        task_id=task['id'],
        entity_id=entity['id'],
        workspace_path=workspace
    )

    assert link['task_id'] == task['id']
    assert link['entity_id'] == entity['id']
    assert link['created_at'] is not None

def test_link_duplicate_prevented(workspace):
    """Test UNIQUE constraint prevents duplicate links."""
    task = create_task(title="Test", workspace_path=workspace)
    entity = create_entity(
        entity_type="file",
        name="Test",
        workspace_path=workspace
    )

    link_entity_to_task(
        task_id=task['id'],
        entity_id=entity['id'],
        workspace_path=workspace
    )

    # Duplicate link should fail
    with pytest.raises(Exception):  # sqlite3.IntegrityError
        link_entity_to_task(
            task_id=task['id'],
            entity_id=entity['id'],
            workspace_path=workspace
        )

def test_get_task_entities(workspace):
    """Test retrieving entities for task."""
    task = create_task(title="Test Task", workspace_path=workspace)

    file1 = create_entity(
        entity_type="file",
        name="File 1",
        workspace_path=workspace
    )
    file2 = create_entity(
        entity_type="file",
        name="File 2",
        workspace_path=workspace
    )

    link_entity_to_task(task['id'], file1['id'], workspace_path=workspace)
    link_entity_to_task(task['id'], file2['id'], workspace_path=workspace)

    entities = get_task_entities(
        task_id=task['id'],
        workspace_path=workspace
    )

    assert len(entities) == 2
    names = {e['name'] for e in entities}
    assert names == {"File 1", "File 2"}

def test_get_task_entities_filter_by_type(workspace):
    """Test filtering task entities by type."""
    task = create_task(title="Test", workspace_path=workspace)

    file_entity = create_entity(
        entity_type="file",
        name="File",
        workspace_path=workspace
    )
    other_entity = create_entity(
        entity_type="other",
        name="Other",
        workspace_path=workspace
    )

    link_entity_to_task(task['id'], file_entity['id'], workspace_path=workspace)
    link_entity_to_task(task['id'], other_entity['id'], workspace_path=workspace)

    files = get_task_entities(
        task_id=task['id'],
        workspace_path=workspace,
        entity_type="file"
    )

    assert len(files) == 1
    assert files[0]['entity_type'] == "file"

def test_bidirectional_query(workspace):
    """Test querying tasks from entity perspective."""
    # Note: This requires get_entity_tasks tool (deferred to v0.4.0)
    # For MVP, validate via manual query
    from task_mcp.database import get_connection

    task1 = create_task(title="Task 1", workspace_path=workspace)
    task2 = create_task(title="Task 2", workspace_path=workspace)
    entity = create_entity(
        entity_type="file",
        name="Shared File",
        workspace_path=workspace
    )

    link_entity_to_task(task1['id'], entity['id'], workspace_path=workspace)
    link_entity_to_task(task2['id'], entity['id'], workspace_path=workspace)

    # Manual query (reverse lookup tool deferred)
    conn = get_connection(workspace_path=workspace)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*
        FROM tasks t
        JOIN task_entity_links l ON t.id = l.task_id
        WHERE l.entity_id = ? AND t.deleted_at IS NULL
    """, (entity['id'],))

    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()

    assert len(tasks) == 2
```

### 4.4 Workflow Tests

**File:** `tests/test_entity_workflows.py`

```python
"""Test end-to-end entity workflows."""

import pytest
import tempfile
from task_mcp.server import (
    create_task,
    create_entity,
    link_entity_to_task,
    get_task_entities,
    update_entity,
)

@pytest.fixture
def workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_file_tracking_workflow(workspace):
    """
    Test complete file tracking workflow:
    1. Create task for feature
    2. Create file entities
    3. Link files to task
    4. Query files for task
    """
    # Step 1: Create task
    task = create_task(
        title="Implement user authentication",
        workspace_path=workspace,
        description="Add login/logout functionality"
    )

    # Step 2: Create file entities
    login_controller = create_entity(
        entity_type="file",
        name="Login Controller",
        workspace_path=workspace,
        identifier="/src/controllers/auth/login.py",
        metadata={"language": "python", "line_count": 150},
        tags="auth backend controller"
    )

    logout_controller = create_entity(
        entity_type="file",
        name="Logout Controller",
        workspace_path=workspace,
        identifier="/src/controllers/auth/logout.py",
        metadata={"language": "python", "line_count": 75},
        tags="auth backend controller"
    )

    login_template = create_entity(
        entity_type="file",
        name="Login Template",
        workspace_path=workspace,
        identifier="/templates/auth/login.html",
        metadata={"language": "html", "framework": "jinja2"},
        tags="auth frontend template"
    )

    # Step 3: Link files to task
    link_entity_to_task(task['id'], login_controller['id'], workspace_path=workspace)
    link_entity_to_task(task['id'], logout_controller['id'], workspace_path=workspace)
    link_entity_to_task(task['id'], login_template['id'], workspace_path=workspace)

    # Step 4: Query files for task
    all_files = get_task_entities(
        task_id=task['id'],
        workspace_path=workspace,
        entity_type="file"
    )

    assert len(all_files) == 3

    # Verify can filter by tags (via list_entities)
    from task_mcp.server import list_entities
    backend_files = list_entities(
        workspace_path=workspace,
        entity_type="file",
        tags="backend"
    )
    assert len(backend_files) == 2

def test_vendor_commission_workflow(workspace):
    """
    Test vendor tracking workflow for commission processing:
    1. Create vendor entities with metadata
    2. Create task for vendor integration
    3. Link vendors to task
    4. Update vendor phase
    """
    # Step 1: Create vendor entities
    abc_vendor = create_entity(
        entity_type="other",
        name="ABC Insurance",
        workspace_path=workspace,
        identifier="ABC-INS",
        description="Major insurance carrier, Excel format",
        metadata={
            "vendor_code": "ABC",
            "phase": "active",
            "brands": ["brand_a", "brand_b", "brand_c"],
            "formats": ["xlsx"],
            "contact": "vendor@abc-insurance.com"
        },
        tags="vendor insurance commission active"
    )

    xyz_vendor = create_entity(
        entity_type="other",
        name="XYZ Health",
        workspace_path=workspace,
        identifier="XYZ-HEALTH",
        description="Healthcare provider, PDF format",
        metadata={
            "vendor_code": "XYZ",
            "phase": "testing",
            "brands": ["brand_x"],
            "formats": ["pdf"],
            "contact": "vendor@xyz-health.com"
        },
        tags="vendor healthcare commission testing"
    )

    # Step 2: Create task for vendor integration
    task = create_task(
        title="Process Q4 commission reports",
        workspace_path=workspace,
        description="Extract and validate commission data from vendors"
    )

    # Step 3: Link vendors to task
    link_entity_to_task(task['id'], abc_vendor['id'], workspace_path=workspace)
    link_entity_to_task(task['id'], xyz_vendor['id'], workspace_path=workspace)

    # Step 4: Query vendors for task
    vendors = get_task_entities(
        task_id=task['id'],
        workspace_path=workspace,
        entity_type="other"
    )

    assert len(vendors) == 2

    # Step 5: Update vendor phase (XYZ from testing → active)
    import json
    xyz_metadata = json.loads(xyz_vendor['metadata'])
    xyz_metadata['phase'] = "active"

    updated_vendor = update_entity(
        entity_id=xyz_vendor['id'],
        workspace_path=workspace,
        metadata=xyz_metadata,
        tags="vendor healthcare commission active"  # Update tag
    )

    updated_metadata = json.loads(updated_vendor['metadata'])
    assert updated_metadata['phase'] == "active"
    assert "active" in updated_vendor['tags']

def test_mixed_entity_types_workflow(workspace):
    """Test task with both file and vendor entities."""
    task = create_task(
        title="Build vendor report extractor",
        workspace_path=workspace
    )

    # File entities
    extractor_file = create_entity(
        entity_type="file",
        name="Vendor Extractor",
        workspace_path=workspace,
        identifier="/src/extractors/vendor_base.py"
    )

    # Vendor entity
    vendor = create_entity(
        entity_type="other",
        name="ABC Vendor",
        workspace_path=workspace,
        identifier="ABC-INS",
        metadata={"vendor_code": "ABC", "format": "xlsx"}
    )

    # Link both
    link_entity_to_task(task['id'], extractor_file['id'], workspace_path=workspace)
    link_entity_to_task(task['id'], vendor['id'], workspace_path=workspace)

    # Query all entities
    all_entities = get_task_entities(task_id=task['id'], workspace_path=workspace)
    assert len(all_entities) == 2

    # Query by type
    files = get_task_entities(
        task_id=task['id'],
        workspace_path=workspace,
        entity_type="file"
    )
    assert len(files) == 1

    vendors = get_task_entities(
        task_id=task['id'],
        workspace_path=workspace,
        entity_type="other"
    )
    assert len(vendors) == 1
```

### 4.5 Phase 4 Acceptance Criteria

- [ ] 47+ entity system tests passing
- [ ] All 54 existing tests passing (zero regressions)
- [ ] File tracking workflow validated
- [ ] Vendor commission workflow validated
- [ ] CRUD operations tested
- [ ] Link operations tested
- [ ] Bidirectional queries validated
- [ ] Soft delete behavior tested
- [ ] Unique constraints tested
- [ ] 70%+ code coverage for entity system

### 4.6 Phase 4 Timeline

| Task | Duration | Output |
|------|----------|--------|
| Write CRUD tests | 6 hours | test_entity_crud.py |
| Write link tests | 4 hours | test_entity_links.py |
| Write workflow tests | 6 hours | test_entity_workflows.py |
| Run full test suite | 2 hours | Coverage report |
| Fix failing tests | 6 hours | All tests green |
| **TOTAL** | **24 hours** | **~750 LOC tests** |

---

## Phase 5: Documentation (Day 10)

### Objectives

- Update README with entity system usage
- Update CLAUDE.md with architecture
- Add vendor use case examples
- Create migration guide

### Files Modified

- `README.md` (add Entity System section, ~100 LOC)
- `CLAUDE.md` (add Entity System section, ~150 LOC)
- `docs/examples/vendor-tracking.md` (NEW, ~200 LOC)

### 5.1 README Updates

**Location:** `README.md` (add after "Advanced Queries" section)

```markdown
## Entity System

Track domain concepts (files, vendors, APIs, etc.) and link them to tasks.

### Entity Types

- **file**: Files in your codebase
- **other**: Generic entities (vendors, APIs, components, etc.)

### Creating Entities

**File Entity:**
```python
# Track a file being modified
file_entity = create_entity(
    entity_type="file",
    name="Login Controller",
    identifier="/src/auth/login.py",
    metadata={"language": "python", "line_count": 250},
    tags="auth backend"
)
```

**Vendor Entity (Commission Processing):**
```python
# Track a vendor with custom metadata
vendor = create_entity(
    entity_type="other",
    name="ABC Insurance",
    identifier="ABC-INS",
    metadata={
        "vendor_code": "ABC",
        "phase": "active",
        "brands": ["brand_a", "brand_b"],
        "formats": ["xlsx", "pdf"]
    },
    tags="vendor insurance commission"
)
```

### Linking Entities to Tasks

```python
# Link file to task
link_entity_to_task(task_id=42, entity_id=file_entity['id'])

# Get all entities for task
entities = get_task_entities(task_id=42)

# Filter by type
files = get_task_entities(task_id=42, entity_type="file")
```

### Use Cases

1. **File Tracking**: Track which files are modified by each task
2. **Vendor Management**: Track vendors with metadata (phase, formats, brands)
3. **Component Mapping**: Track architectural components as entities
4. **API Endpoints**: Track API endpoints being developed

### Available Tools

- `create_entity` - Create new entity
- `update_entity` - Update entity metadata
- `get_entity` - Get single entity by ID
- `list_entities` - List/filter entities
- `delete_entity` - Soft delete entity
- `link_entity_to_task` - Link entity to task
- `get_task_entities` - Get entities for task
```

### 5.2 CLAUDE.md Updates

**Location:** `CLAUDE.md` (add new section after "Common Pitfalls")

```markdown
## Entity System Architecture

### Overview

The entity system enables tracking domain concepts (files, vendors, APIs) and linking them to tasks. This provides rich context beyond generic task descriptions.

### Database Schema

```
entities (per project database)
├── id INTEGER PRIMARY KEY
├── entity_type TEXT CHECK IN ('file', 'other')
├── name TEXT NOT NULL
├── identifier TEXT (UNIQUE with entity_type)
├── description TEXT
├── metadata TEXT (JSON blob)
├── tags TEXT
├── created_by TEXT
├── created_at TIMESTAMP
├── updated_at TIMESTAMP
└── deleted_at TIMESTAMP

task_entity_links (junction table)
├── id INTEGER PRIMARY KEY
├── task_id INTEGER FK → tasks(id)
├── entity_id INTEGER FK → entities(id)
├── created_by TEXT
├── created_at TIMESTAMP
└── deleted_at TIMESTAMP
```

### Entity Types

**MVP v1 (v0.3.0):**
- `file`: File paths in codebase
- `other`: Generic catch-all for domain-specific entities

**Future (v0.4.0+):**
- May add `pr`, `issue`, `component`, `vendor`, etc. based on usage patterns

### Metadata Patterns

**Generic JSON (MVP):**
```python
# File metadata
{"language": "python", "line_count": 250}

# Vendor metadata (commission processing)
{
    "vendor_code": "ABC",
    "phase": "active",
    "brands": ["brand_a"],
    "formats": ["xlsx", "pdf"]
}
```

**No Typed Schemas in MVP:**
- Agents document expected metadata in tool docstrings
- Future versions may add optional typed validation

### Implementation Patterns

**Creating Entities:**
```python
entity = create_entity(
    entity_type="file",
    name="Login Controller",
    identifier="/src/auth/login.py",
    metadata={"language": "python"},
    tags="auth backend"
)
```

**Linking to Tasks:**
```python
link_entity_to_task(task_id=42, entity_id=entity['id'])
```

**Querying:**
```python
# Task → Entities (forward)
entities = get_task_entities(task_id=42, entity_type="file")

# Entity → Tasks (reverse, manual query in MVP)
# Dedicated tool deferred to v0.4.0
```

### Critical Rules

1. **entity_type Constraint**: Only `'file'` and `'other'` allowed in MVP
2. **UNIQUE(entity_type, identifier)**: Prevents duplicate entities
3. **Soft Delete**: Always set `deleted_at`, never hard delete
4. **Metadata Validation**: JSON syntax only (no typed schemas in MVP)
5. **Bidirectional Links**: Junction table enables fast queries both directions

### Common Pitfalls

1. **Don't use unsupported entity types**: Only `'file'` and `'other'` in MVP
2. **Don't forget metadata is JSON string**: Must be valid JSON syntax
3. **Don't skip identifier for files**: Use absolute file paths
4. **Don't hard-delete entities**: Always use soft delete
5. **Don't create duplicate identifiers**: UNIQUE constraint will fail
```

### 5.3 Vendor Use Case Documentation

**File:** `docs/examples/vendor-tracking.md` (NEW)

```markdown
# Vendor Tracking Use Case

This example demonstrates using the entity system to track vendors in a commission processing application.

## Scenario

You're building a commission processing system that:
- Extracts data from multiple insurance vendors
- Each vendor has different file formats (Excel, PDF, CSV)
- Vendors go through phases: testing → active → deprecated
- Need to track which vendors are processed by which tasks

## Step 1: Create Vendor Entities

```python
# Active vendor with Excel format
abc_vendor = create_entity(
    entity_type="other",
    name="ABC Insurance",
    identifier="ABC-INS",
    description="Major insurance carrier, Excel-based reports",
    metadata={
        "vendor_code": "ABC",
        "phase": "active",
        "brands": ["brand_a", "brand_b", "brand_c"],
        "formats": ["xlsx"],
        "contact_email": "vendor@abc-insurance.com",
        "last_updated": "2025-10-15"
    },
    tags="vendor insurance commission active excel"
)

# Testing vendor with PDF format
xyz_vendor = create_entity(
    entity_type="other",
    name="XYZ Health Partners",
    identifier="XYZ-HEALTH",
    description="Healthcare provider, PDF-based reports",
    metadata={
        "vendor_code": "XYZ",
        "phase": "testing",
        "brands": ["brand_x"],
        "formats": ["pdf"],
        "contact_email": "vendor@xyz-health.com",
        "notes": "Still validating extraction accuracy"
    },
    tags="vendor healthcare commission testing pdf"
)

# Deprecated vendor
old_vendor = create_entity(
    entity_type="other",
    name="Legacy Corp",
    identifier="LEGACY",
    description="Deprecated vendor, no longer processing",
    metadata={
        "vendor_code": "LEGACY",
        "phase": "deprecated",
        "deprecated_date": "2025-09-01",
        "replacement": "ABC-INS"
    },
    tags="vendor commission deprecated"
)
```

## Step 2: Create Processing Tasks

```python
# Task for Q4 processing
q4_task = create_task(
    title="Process Q4 2025 Commission Reports",
    description="Extract and validate commission data for Q4",
    status="in_progress",
    priority="high",
    tags="commission q4-2025"
)

# Link active vendors to task
link_entity_to_task(task_id=q4_task['id'], entity_id=abc_vendor['id'])
link_entity_to_task(task_id=q4_task['id'], entity_id=xyz_vendor['id'])

# Task for vendor onboarding
onboarding_task = create_task(
    title="Onboard XYZ Health vendor",
    description="Build extractor for XYZ PDF format",
    status="todo",
    priority="medium",
    tags="vendor onboarding"
)

link_entity_to_task(task_id=onboarding_task['id'], entity_id=xyz_vendor['id'])
```

## Step 3: Query Vendors by Phase

```python
# Get all active vendors
active_vendors = list_entities(
    entity_type="other",
    tags="active"
)

print(f"Active vendors: {len(active_vendors)}")
for vendor in active_vendors:
    metadata = json.loads(vendor['metadata'])
    print(f"- {vendor['name']}: {metadata['formats']}")

# Output:
# Active vendors: 1
# - ABC Insurance: ['xlsx']
```

## Step 4: Update Vendor Phase

```python
# Promote XYZ from testing → active
import json

xyz_metadata = json.loads(xyz_vendor['metadata'])
xyz_metadata['phase'] = "active"
xyz_metadata['activated_date'] = "2025-10-27"
del xyz_metadata['notes']  # Remove testing notes

updated_vendor = update_entity(
    entity_id=xyz_vendor['id'],
    metadata=xyz_metadata,
    tags="vendor healthcare commission active pdf"  # Update tags
)

print(f"Updated {updated_vendor['name']} to active phase")
```

## Step 5: Generate Vendor Report

```python
# Get all vendors for reporting
all_vendors = list_entities(entity_type="other", tags="vendor")

for vendor in all_vendors:
    metadata = json.loads(vendor['metadata'])
    phase = metadata.get('phase', 'unknown')

    print(f"\nVendor: {vendor['name']}")
    print(f"  Code: {vendor['identifier']}")
    print(f"  Phase: {phase}")
    print(f"  Formats: {', '.join(metadata.get('formats', []))}")

    if phase == "active":
        print(f"  Brands: {len(metadata.get('brands', []))}")

# Output:
# Vendor: ABC Insurance
#   Code: ABC-INS
#   Phase: active
#   Formats: xlsx
#   Brands: 3
#
# Vendor: XYZ Health Partners
#   Code: XYZ-HEALTH
#   Phase: active
#   Formats: pdf
#   Brands: 1
#
# Vendor: Legacy Corp
#   Code: LEGACY
#   Phase: deprecated
#   Formats:
```

## Best Practices

### Metadata Schema Convention

While metadata is freeform JSON, establish conventions for your domain:

```python
# Vendor metadata schema (documented, not enforced)
{
    "vendor_code": str,        # Required: Unique vendor code
    "phase": str,              # Required: testing|active|deprecated
    "brands": list[str],       # Optional: Associated brands
    "formats": list[str],      # Required: xlsx|pdf|csv|image
    "contact_email": str,      # Optional: Vendor contact
    "activated_date": str,     # Optional: ISO date
    "deprecated_date": str,    # Optional: ISO date
    "notes": str,              # Optional: Freeform notes
    "replacement": str         # Optional: Replacement vendor code
}
```

### Tagging Strategy

Use tags for filtering:
- `vendor` - All vendor entities
- `active` / `testing` / `deprecated` - Phase tags
- `insurance` / `healthcare` - Industry tags
- Format tags: `excel`, `pdf`, `csv`

### Identifier Convention

Use consistent identifier format:
- Pattern: `{VENDOR_CODE}-{INDUSTRY}`
- Examples: `ABC-INS`, `XYZ-HEALTH`, `ACME-AUTO`

## Integration with File Tracking

Combine vendor entities with file entities:

```python
# Create extractor file entity
extractor = create_entity(
    entity_type="file",
    name="ABC Vendor Extractor",
    identifier="/src/extractors/abc_insurance_extractor.py",
    metadata={"language": "python", "vendor": "ABC-INS"},
    tags="extractor vendor abc"
)

# Link both vendor and file to task
task = create_task(
    title="Fix ABC extractor brand parsing",
    description="Update brand extraction logic for ABC vendor"
)

link_entity_to_task(task_id=task['id'], entity_id=abc_vendor['id'])
link_entity_to_task(task_id=task['id'], entity_id=extractor['id'])

# Query shows both vendor and file context
entities = get_task_entities(task_id=task['id'])
# Returns: [abc_vendor, extractor]
```

## Future Enhancements (v0.4.0+)

If vendor tracking proves valuable, future versions may add:
- Typed `vendor` entity type (promoted from `other`)
- Metadata validation schema
- Reverse lookup: `get_entity_tasks(entity_id=vendor_id)`
- Bulk operations: `bulk_link_entities(task_id, [entity_id1, entity_id2])`
```

### 5.4 Phase 5 Acceptance Criteria

- [ ] README updated with entity system section
- [ ] CLAUDE.md updated with architecture details
- [ ] Vendor use case documented with examples
- [ ] Migration guide created (if needed)
- [ ] All documentation examples tested
- [ ] Code examples are copy-paste ready

### 5.5 Phase 5 Timeline

| Task | Duration | Output |
|------|----------|--------|
| Update README | 2 hours | Entity System section |
| Update CLAUDE.md | 3 hours | Architecture section |
| Write vendor guide | 4 hours | vendor-tracking.md |
| Test all examples | 2 hours | Verified examples |
| Review/polish docs | 1 hour | Final docs |
| **TOTAL** | **12 hours** | **~450 LOC docs** |

---

## Vendor Use Case Implementation

### Complete Vendor Workflow Example

This section provides a complete, production-ready example of vendor tracking.

```python
"""
Vendor Commission Processing Workflow

This example shows how to use the entity system for commission processing:
1. Define vendor entities with metadata
2. Track vendor lifecycle (testing → active → deprecated)
3. Link vendors to processing tasks
4. Query vendors by phase and format
"""

import json
from task_mcp.server import (
    create_entity,
    update_entity,
    list_entities,
    create_task,
    link_entity_to_task,
    get_task_entities,
)

# === STEP 1: Initialize Vendor Entities ===

def create_vendor(
    name: str,
    code: str,
    phase: str,
    formats: list[str],
    brands: list[str],
    **kwargs
) -> dict:
    """
    Helper to create vendor entity with standard metadata.

    Args:
        name: Vendor display name
        code: Unique vendor code
        phase: testing|active|deprecated
        formats: List of file formats (xlsx, pdf, csv, etc.)
        brands: List of brand identifiers
        **kwargs: Additional metadata fields

    Returns:
        Created entity dict
    """
    metadata = {
        "vendor_code": code,
        "phase": phase,
        "formats": formats,
        "brands": brands,
        **kwargs
    }

    tags = f"vendor commission {phase} {' '.join(formats)}"

    return create_entity(
        entity_type="other",
        name=name,
        identifier=f"{code}-VENDOR",
        description=f"{name} - {phase} phase, {', '.join(formats)} format(s)",
        metadata=metadata,
        tags=tags
    )

# Create vendors
abc_vendor = create_vendor(
    name="ABC Insurance Corporation",
    code="ABC",
    phase="active",
    formats=["xlsx"],
    brands=["brand_a", "brand_b", "brand_c"],
    contact_email="vendor@abc-insurance.com",
    notes="Primary insurance vendor, stable format"
)

xyz_vendor = create_vendor(
    name="XYZ Health Partners",
    code="XYZ",
    phase="testing",
    formats=["pdf"],
    brands=["brand_x"],
    contact_email="vendor@xyz-health.com",
    notes="New vendor, extraction validation in progress"
)

legacy_vendor = create_vendor(
    name="Legacy Insurance Co",
    code="LEGACY",
    phase="deprecated",
    formats=["csv"],
    brands=[],
    deprecated_date="2025-09-01",
    replacement_vendor="ABC",
    notes="Replaced by ABC Insurance"
)

print(f"Created {len([abc_vendor, xyz_vendor, legacy_vendor])} vendor entities")

# === STEP 2: Create Processing Tasks ===

# Q4 commission processing task
q4_task = create_task(
    title="Process Q4 2025 Commission Reports",
    description="Extract, validate, and reconcile commission data for Q4",
    status="in_progress",
    priority="high",
    tags="commission q4-2025 quarterly"
)

# Link active vendors to Q4 task
link_entity_to_task(task_id=q4_task['id'], entity_id=abc_vendor['id'])
link_entity_to_task(task_id=q4_task['id'], entity_id=xyz_vendor['id'])

# Vendor onboarding task
onboarding_task = create_task(
    title="Complete XYZ Health vendor onboarding",
    description="Build PDF extractor, validate data accuracy, promote to active",
    status="in_progress",
    priority="medium",
    tags="vendor onboarding xyz"
)

link_entity_to_task(task_id=onboarding_task['id'], entity_id=xyz_vendor['id'])

# === STEP 3: Query Vendors by Phase ===

def get_vendors_by_phase(phase: str) -> list[dict]:
    """Get all vendors in specified phase."""
    vendors = list_entities(entity_type="other", tags=phase)
    return [v for v in vendors if json.loads(v['metadata']).get('phase') == phase]

active_vendors = get_vendors_by_phase("active")
testing_vendors = get_vendors_by_phase("testing")
deprecated_vendors = get_vendors_by_phase("deprecated")

print(f"\nVendor Status:")
print(f"  Active: {len(active_vendors)}")
print(f"  Testing: {len(testing_vendors)}")
print(f"  Deprecated: {len(deprecated_vendors)}")

# === STEP 4: Promote Vendor (Testing → Active) ===

def promote_vendor_to_active(vendor_id: int):
    """
    Promote vendor from testing to active phase.

    Updates:
    - phase: testing → active
    - activated_date: Set to current date
    - tags: Update to include 'active'
    - notes: Remove testing notes
    """
    vendor = get_entity(entity_id=vendor_id)
    metadata = json.loads(vendor['metadata'])

    # Update metadata
    metadata['phase'] = "active"
    metadata['activated_date'] = "2025-10-27"
    metadata.pop('notes', None)  # Remove testing notes

    # Update tags (replace 'testing' with 'active')
    new_tags = vendor['tags'].replace('testing', 'active')

    updated = update_entity(
        entity_id=vendor_id,
        metadata=metadata,
        tags=new_tags
    )

    print(f"✓ Promoted {vendor['name']} to active phase")
    return updated

# Promote XYZ after testing complete
promoted_vendor = promote_vendor_to_active(xyz_vendor['id'])

# === STEP 5: Generate Vendor Report ===

def generate_vendor_report():
    """Generate comprehensive vendor status report."""
    all_vendors = list_entities(entity_type="other", tags="vendor")

    print("\n" + "="*60)
    print("VENDOR STATUS REPORT")
    print("="*60)

    for vendor in all_vendors:
        metadata = json.loads(vendor['metadata'])

        print(f"\n{vendor['name']}")
        print(f"  Code: {vendor['identifier']}")
        print(f"  Phase: {metadata['phase'].upper()}")
        print(f"  Formats: {', '.join(metadata.get('formats', []))}")

        if metadata['phase'] == "active":
            print(f"  Brands: {len(metadata.get('brands', []))}")
            print(f"  Contact: {metadata.get('contact_email', 'N/A')}")

        elif metadata['phase'] == "deprecated":
            print(f"  Deprecated: {metadata.get('deprecated_date', 'N/A')}")
            print(f"  Replacement: {metadata.get('replacement_vendor', 'N/A')}")

        elif metadata['phase'] == "testing":
            print(f"  Notes: {metadata.get('notes', 'N/A')}")

generate_vendor_report()

# === STEP 6: Query Task-Vendor Relationships ===

def get_vendors_for_task(task_id: int):
    """Get all vendor entities linked to a task."""
    entities = get_task_entities(task_id=task_id, entity_type="other")

    vendors = []
    for entity in entities:
        metadata = json.loads(entity['metadata'])
        if 'vendor_code' in metadata:
            vendors.append(entity)

    return vendors

q4_vendors = get_vendors_for_task(q4_task['id'])
print(f"\nQ4 Task linked to {len(q4_vendors)} vendors:")
for v in q4_vendors:
    metadata = json.loads(v['metadata'])
    print(f"  - {v['name']} ({metadata['phase']})")

# === STEP 7: Filter Vendors by Format ===

def get_vendors_by_format(format_type: str) -> list[dict]:
    """Get all vendors supporting specified format."""
    all_vendors = list_entities(entity_type="other", tags="vendor")

    matching = []
    for vendor in all_vendors:
        metadata = json.loads(vendor['metadata'])
        if format_type in metadata.get('formats', []):
            matching.append(vendor)

    return matching

excel_vendors = get_vendors_by_format("xlsx")
pdf_vendors = get_vendors_by_format("pdf")

print(f"\nVendors by Format:")
print(f"  Excel (.xlsx): {len(excel_vendors)}")
print(f"  PDF (.pdf): {len(pdf_vendors)}")
```

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Schema migration issues** | HIGH | LOW | Use `CREATE TABLE IF NOT EXISTS`, test on fresh DB |
| **Performance degradation** | MEDIUM | LOW | Add all 6 indexes, test with 1000+ entities |
| **Unique constraint conflicts** | LOW | MEDIUM | Document identifier conventions, provide clear errors |
| **Type safety violations** | MEDIUM | LOW | Use mypy --strict, comprehensive type annotations |
| **Metadata JSON errors** | LOW | MEDIUM | Validate JSON syntax in Pydantic models |

### Schedule Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Underestimated complexity** | MEDIUM | MEDIUM | 20% buffer built into timeline (10 days → 12 days) |
| **Test failures** | HIGH | LOW | Write tests incrementally, fix as you go |
| **Documentation delays** | LOW | MEDIUM | Keep examples simple, defer advanced guides |
| **Integration issues** | MEDIUM | LOW | Follow existing patterns exactly, minimize changes |

### Scope Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Feature creep** | HIGH | MEDIUM | Stick to 7 tools, defer everything else |
| **Vendor use case too complex** | MEDIUM | LOW | Use "other" type, generic metadata (no typed schemas) |
| **Reverse lookup needed** | LOW | HIGH | Document manual query, defer tool to v0.4.0 |
| **Bulk operations needed** | LOW | MEDIUM | Defer to v0.4.0, use loops in MVP |

---

## Appendix: Complete Code Examples

### Complete Database Schema Addition

**File:** `src/task_mcp/database.py`

```python
def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize schema with tasks, entities, and links tables."""

    # === EXISTING: Tasks table creation (lines 79-118) ===
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL CHECK(status IN ('todo', 'in_progress', 'blocked', 'done', 'cancelled')),
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
            parent_task_id INTEGER,
            depends_on TEXT,
            tags TEXT,
            blocker_reason TEXT,
            file_references TEXT,
            created_by TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            completed_at TIMESTAMP,
            deleted_at TIMESTAMP,
            FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
        )
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_parent ON tasks(parent_task_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_deleted ON tasks(deleted_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON tasks(tags)")

    # === NEW: Entities table ===
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL CHECK(entity_type IN ('file', 'other')),
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

    conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_identifier ON entities(identifier)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_deleted ON entities(deleted_at)")

    # === NEW: Task-Entity Links ===
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_entity_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            entity_id INTEGER NOT NULL,
            created_by TEXT,
            created_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
            UNIQUE(task_id, entity_id)
        )
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_link_task ON task_entity_links(task_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_link_entity ON task_entity_links(entity_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_link_deleted ON task_entity_links(deleted_at)")

    conn.commit()
```

### Summary Statistics

**Total Implementation:**

| Category | Files | LOC Added | Test LOC | Total LOC |
|----------|-------|-----------|----------|-----------|
| Schema | 1 | 80 | 100 | 180 |
| Models | 1 | 200 | 150 | 350 |
| Tools | 1 | 385 | 400 | 785 |
| Docs | 3 | 450 | 0 | 450 |
| **TOTAL** | **6** | **1,115** | **650** | **1,765** |

**Development Effort:**

| Phase | Days | Hours | Percentage |
|-------|------|-------|------------|
| Schema | 2 | 8 | 10% |
| Models | 1 | 9 | 11% |
| Tools | 4 | 27 | 34% |
| Testing | 3 | 24 | 30% |
| Documentation | 1 | 12 | 15% |
| **TOTAL** | **10** | **80** | **100%** |

---

## Conclusion

This implementation plan delivers an **entity system MVP in 10 working days** with:

- ✅ **51% code reduction** vs full design (1,765 LOC vs 3,600 LOC)
- ✅ **80% of core value** (file tracking + vendor use cases)
- ✅ **Zero breaking changes** (100% backward compatible)
- ✅ **Extensibility built-in** ("other" type + generic metadata)
- ✅ **Production-ready quality** (70%+ test coverage, mypy compliance)

**Next Steps:**
1. Review plan with stakeholders
2. Approve Phase 1 (database schema)
3. Begin implementation following timeline
4. Deploy v0.3.0 to production
5. Gather usage data to inform v0.4.0 enhancements
