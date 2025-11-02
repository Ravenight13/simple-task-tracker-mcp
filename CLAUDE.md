# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Task MCP Server is a lightweight Model Context Protocol (MCP) server for task and subtask tracking during agentic AI project development. It provides isolated SQLite databases per project workspace, enabling agents to create, track, and manage development tasks with file references, dependencies, and status tracking.

## Architecture

### Database Design

**Multi-Database Strategy:**
- Each project workspace gets its own isolated SQLite database
- Workspace path is hashed (SHA256, truncated to 8 chars) to generate safe filenames
- All project databases stored in `~/.task-mcp/databases/project_{hash}.db`
- Master database at `~/.task-mcp/master.db` tracks all known projects for cross-client discovery
- SQLite WAL mode enables concurrent reads between Claude Code and Claude Desktop

**Schema Structure:**
- `tasks` table: Full task hierarchy with parent/child relationships via `parent_task_id`
- `depends_on` field: JSON array of task IDs for explicit dependencies
- `file_references` field: JSON array of file paths for context
- `entities` table: Typed entities (file, other) with JSON metadata for flexible domain modeling
- `task_entity_links` table: Many-to-many relationships between tasks and entities
- Soft delete: `deleted_at` timestamp instead of hard deletion (30-day retention)
- State machine: `todo → in_progress → blocked → done → cancelled → to_be_deleted`

### Module Organization

```
src/task_mcp/
├── server.py      # FastMCP server setup and tool registration
├── database.py    # SQLite operations for project databases (CRUD, queries)
├── master.py      # Master DB operations (project registry, discovery)
├── models.py      # Task data models and validation (Pydantic)
└── utils.py       # Workspace detection, path hashing, validation helpers
```

**Key Responsibilities:**
- `utils.py`: Workspace detection priority: explicit param → TASK_MCP_WORKSPACE env → cwd
- `database.py`: WAL mode configuration, connection pooling, foreign key enforcement, entity operations
- `models.py`: 10k char description limit, blocker_reason validation, status transitions, entity models
- `master.py`: Auto-register projects on first access, update last_accessed timestamps

### Workspace Detection Flow

1. **Claude Code (auto-detection)**: Sets `TASK_MCP_WORKSPACE` environment variable, tools omit `workspace_path` parameter
2. **Claude Desktop (explicit)**: Always passes `workspace_path` parameter in tool calls
3. **Fallback**: Use current working directory if neither above is available
4. Hash workspace path → lookup/create project DB → register in master.db if new

## Development Commands

### Setup
```bash
# Install dependencies using uv
uv sync

# Run the MCP server (for testing)
uv run task-mcp
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_task_mcp.py

# Run with verbose output
uv run pytest -v

# Run specific test function
uv run pytest tests/test_task_mcp.py::test_create_task
```

### Configuration
MCP server registers via standard configuration:
```json
{
  "mcpServers": {
    "task-mcp": {
      "command": "uv",
      "args": ["run", "task-mcp"]
    }
  }
}
```

## Critical Implementation Rules

### Data Constraints
- **Description limit**: 10,000 characters maximum (prevent token overflow) - applies to both tasks and entities
- **Blocked status**: Requires `blocker_reason` field when status='blocked'
- **Dependencies**: Task cannot progress to 'in_progress' or 'done' if depends_on tasks incomplete
- **Subtasks independence**: Parent can complete with open subtasks (not auto-blocked)
- **Entity uniqueness**: (entity_type, identifier) must be unique for active entities (WHERE deleted_at IS NULL)
- **Entity metadata**: Must be valid JSON string or dict; no schema validation (generic storage)

### SQLite Configuration (MUST SET)
```python
conn.execute("PRAGMA journal_mode=WAL")      # Enable concurrent reads
conn.execute("PRAGMA busy_timeout=5000")     # 5-second lock timeout
conn.execute("PRAGMA foreign_keys=ON")       # Enforce referential integrity
```

### Validation Sequence
1. Check description length ≤ 10k chars before insert/update
2. Verify `blocker_reason` exists when setting status='blocked'
3. Validate `depends_on` task IDs exist and are not deleted
4. Verify `parent_task_id` exists and is not deleted
5. Normalize tags (lowercase, single spaces)

### Dependency Checking Logic
Before allowing status transition to 'in_progress' or 'done':
```python
# Pseudocode
depends_on_ids = json.loads(task.depends_on or "[]")
for dep_id in depends_on_ids:
    dep_task = get_task(dep_id)
    if dep_task.status != 'done':
        raise ValidationError(f"Cannot progress: Task {dep_id} not complete")
```

## MCP Tools Implementation

### Core Pattern
All tools follow this pattern:
1. Resolve workspace_path (explicit param → env var → cwd)
2. Hash workspace path to get project DB filename
3. Connect to/create project database
4. Register project in master.db if first access
5. Update last_accessed in master.db
6. Execute operation
7. Return FastMCP-formatted response

### Tool Categories
- **Task CRUD**: create_task, update_task, get_task, list_tasks, delete_task
- **Entity CRUD**: create_entity, update_entity, get_entity, list_entities, delete_entity
- **Entity Linking**: link_entity_to_task, get_task_entities, get_entity_tasks
- **Search**: search_tasks (full-text on title/description), search_entities (full-text on name/identifier)
- **Advanced Queries**: get_task_tree (recursive subtasks), get_blocked_tasks, get_next_tasks
- **Maintenance**: cleanup_deleted_tasks (purge >30 days old)
- **Project Management**: list_projects, get_project_info, set_project_name

### Auto-Capture Fields
- `created_by`: Conversation ID from MCP context
- `created_at`, `updated_at`: Automatic timestamps
- `completed_at`: Set when status changes to 'done'

## FastMCP Integration

Use FastMCP decorators for tool registration:
```python
from fastmcp import FastMCP

mcp = FastMCP("task-mcp")

@mcp.tool()
def create_task(
    title: str,
    workspace_path: str | None = None,
    description: str | None = None,
    # ... other params
) -> dict:
    """Create a new task with validation."""
    pass
```

## Testing Strategy

### Critical Test Cases
1. Workspace detection with explicit path, env var, and cwd fallback
2. Description length validation (reject >10k chars)
3. Dependency blocking (cannot complete task with incomplete dependencies)
4. Soft delete behavior (excluded from queries, purged after 30 days)
5. Concurrent access (multiple reads via WAL mode)
6. Status transitions with blocker_reason validation
7. Project auto-registration in master.db
8. Subtask cascade delete when parent is deleted

### Test Database Isolation
Use temporary directories for test databases to avoid conflicts:
```python
import tempfile
with tempfile.TemporaryDirectory() as tmpdir:
    # Point database operations to tmpdir
    pass
```

## Task Grouping and Organization

### Project Tags Pattern

Task MCP uses a **tag-based grouping system** to organize related tasks into projects or feature groups. This approach leverages the existing tag infrastructure without requiring database changes.

**Tag Format:**
- Use prefix `project:` followed by project/feature name
- Example: `project:workspace-metadata`, `project:entity-viewer`, `project:auth-refactor`
- Tags are normalized to lowercase with single spaces
- Multiple project tags can coexist on the same task

**Benefits:**
- No database schema changes required
- Works immediately with existing UI tag filters
- Backward compatible (tasks without project tags unaffected)
- Flexible grouping (tasks can belong to multiple projects)
- Fast to implement and use

**Usage Examples:**

```python
# Create tasks with project grouping
create_task(
    title="Implement user authentication",
    tags="backend security project:auth-refactor"
)

create_task(
    title="Add login UI",
    tags="frontend ui project:auth-refactor"
)

# Filter tasks by project
tasks = list_tasks(tags="project:auth-refactor")

# Update existing task to add to project
update_task(
    task_id=42,
    tags="api backend project:workspace-metadata"
)
```

**Task-Viewer Integration:**
- Filter by project tag using the tag dropdown
- Project tags appear alongside other tags
- Tag count shows number of tasks in each project
- Supports multiple tag filters (combine project + status tags)

**Best Practices:**
1. Use descriptive project names (e.g., `project:entity-viewer` not `project:ev`)
2. Apply project tags when creating related tasks
3. Use consistent naming conventions within a workspace
4. Combine project tags with functional tags (e.g., `project:auth backend testing`)
5. Document active projects in workspace README or docs

**Example: Workspace Metadata Feature (Tasks #70-76)**
```bash
# All tasks tagged with: project:workspace-metadata
Task #70: Create audit.py module → tags: "audit strategy2 project:workspace-metadata"
Task #71: Integrate audit tool → tags: "audit mcp-tool project:workspace-metadata"
Task #72: Create test suite → tags: "testing audit project:workspace-metadata"
Task #73: Database migration → tags: "database migration project:workspace-metadata"
Task #74: Workspace utilities → tags: "utilities project:workspace-metadata"
Task #75: Update create_task → tags: "mcp-tools project:workspace-metadata"
Task #76: Validate workspace → tags: "mcp-tools validation project:workspace-metadata"

# Filter to see all related tasks
list_tasks(tags="project:workspace-metadata")  # Returns 7 tasks
```

## Entity System

### Overview
The Entity System enables tracking and linking arbitrary entities (files, vendors, etc.) to tasks for rich context management.

**Key Features:**
- 2 entity types: `file` (code files) and `other` (vendors, people, etc.)
- 7 MCP tools for CRUD + linking operations
- Generic JSON metadata for flexible data storage
- Many-to-many relationships with tasks via junction table
- Soft delete pattern for data safety

### Database Schema

**entities table (11 fields):**
- `id` (INTEGER PRIMARY KEY)
- `entity_type` (TEXT: 'file' or 'other')
- `name` (TEXT: Display name, required)
- `identifier` (TEXT: Unique ID like file path, nullable)
- `description` (TEXT: Max 10k chars, nullable)
- `metadata` (TEXT: JSON string for flexible data, nullable)
- `tags` (TEXT: Space-separated, normalized to lowercase)
- `created_by` (TEXT: Conversation ID, auto-captured)
- `created_at` (TEXT: ISO 8601 timestamp)
- `updated_at` (TEXT: ISO 8601 timestamp)
- `deleted_at` (TEXT: Soft delete timestamp, nullable)

**task_entity_links table (6 fields):**
- `id` (INTEGER PRIMARY KEY)
- `task_id` (INTEGER: Foreign key to tasks)
- `entity_id` (INTEGER: Foreign key to entities)
- `created_by` (TEXT: Conversation ID)
- `created_at` (TEXT: ISO 8601 timestamp)
- `deleted_at` (TEXT: Soft delete timestamp)

**Indexes (6 total):**
- Partial UNIQUE on (entity_type, identifier) WHERE deleted_at IS NULL
- entity_type for filtering
- deleted_at for soft delete queries
- task_id for task→entity lookups
- entity_id for entity→task lookups
- (task_id, entity_id) UNIQUE for link integrity

### MCP Tools

**create_entity:** Create new entity with validation
- Validates entity_type ('file' or 'other')
- Checks duplicate identifier (scoped to entity_type)
- Auto-captures conversation ID from context
- Returns full entity dict with generated ID

**update_entity:** Update existing entity (partial updates)
- Only updates provided fields
- Checks duplicate identifier on change
- Updates updated_at timestamp automatically
- Returns full updated entity dict

**get_entity:** Retrieve single entity by ID
- Returns error if not found or soft-deleted
- Includes all entity fields

**list_entities:** List entities with filtering
- Filter by entity_type (optional)
- Filter by tags (partial match, space-separated)
- Excludes soft-deleted entities
- Orders by created_at DESC

**delete_entity:** Soft delete entity
- Sets deleted_at timestamp
- Cascades to all task_entity_links automatically
- Returns deleted_links count
- Allows re-creation with same identifier after deletion

**link_entity_to_task:** Create task-entity link
- Creates many-to-many relationship
- Prevents duplicate links (UNIQUE constraint)
- Auto-captures conversation ID
- Returns link dict with timestamps

**get_task_entities:** Get all entities for a task
- Returns entities with link metadata
- Includes link_created_at and link_created_by
- Excludes soft-deleted entities/tasks
- Orders by link_created_at DESC

**get_entity_tasks:** Get all tasks for an entity (reverse query)
- Returns tasks with link metadata
- Includes link_created_at and link_created_by
- Optional status filter (todo, in_progress, done, etc.)
- Optional priority filter (low, medium, high)
- Excludes soft-deleted tasks/entities
- Orders by link_created_at DESC

### Vendor Use Case

Standard metadata schema for vendor entities:
```json
{
  "vendor_code": "ABC-INS",
  "phase": "active",
  "formats": ["xlsx", "pdf"],
  "brands": ["Brand A", "Brand B"]
}
```

**Tag conventions:**
- `vendor` - Mark as vendor entity
- `insurance` / `telecom` / etc. - Industry tags
- `active` / `testing` - Phase tags

**Query patterns:**
```python
# Create vendor
vendor = create_entity(
    entity_type="other",
    name="ABC Insurance",
    identifier="ABC-INS",
    metadata={"phase": "active", "formats": ["xlsx", "pdf"]},
    tags="vendor insurance active"
)

# List all vendors
vendors = list_entities(entity_type="other", tags="vendor")

# Link vendor to task
link_entity_to_task(task_id=42, entity_id=vendor["id"])

# Get vendors for task
task_vendors = get_task_entities(task_id=42)

# Get all tasks for a vendor (reverse query)
vendor_tasks = get_entity_tasks(entity_id=vendor["id"])

# Get only high-priority tasks for a vendor
high_priority_tasks = get_entity_tasks(
    entity_id=vendor["id"],
    priority="high"
)

# Get only in-progress tasks for a vendor
in_progress_tasks = get_entity_tasks(
    entity_id=vendor["id"],
    status="in_progress"
)
```

### File Entity Use Case

Track code files involved in tasks:
```python
# Create file entity
file_entity = create_entity(
    entity_type="file",
    name="Authentication Controller",
    identifier="/src/api/auth.py",
    metadata={"language": "python", "line_count": 250},
    tags="backend api authentication"
)

# Link file to refactoring task
link_entity_to_task(task_id=123, entity_id=file_entity["id"])

# Get all files for task
files = get_task_entities(task_id=123)
```

### Critical Implementation Rules

**Duplicate Detection:**
- Uniqueness: (entity_type, identifier) WHERE deleted_at IS NULL
- Different entity types CAN share identifiers
- NULL identifiers do not conflict (multiple entities without identifiers allowed)
- Soft-deleted entities don't block re-creation with same identifier

**Cascade Deletion:**
- Entity deletion ALWAYS cascades to all task-entity links
- No optional cascade parameter (always cascade for data integrity)
- Soft delete pattern used (deleted_at timestamp)

**Metadata Handling:**
- Accepts dict, list, or JSON string
- Converts to JSON string for storage
- Returns as JSON string (client must parse)
- No schema validation (generic JSON storage)

## Common Pitfalls to Avoid

1. **Don't hard-delete tasks or entities**: Always use soft delete (set `deleted_at`)
2. **Don't forget WAL mode**: Required for concurrent Claude Code + Desktop access
3. **Don't return deleted tasks/entities**: All queries must filter `WHERE deleted_at IS NULL`
4. **Don't allow 25k+ token descriptions**: Validate 10k char limit on input (tasks and entities)
5. **Don't forget master.db updates**: Every operation must update `last_accessed`
6. **Don't cascade parent blocking**: Subtasks don't automatically block parents
7. **Don't skip dependency validation**: Check all depends_on tasks before status changes
8. **Don't forget entity uniqueness**: Check (entity_type, identifier) uniqueness for active entities
9. **Don't skip cascade on entity delete**: Entity deletion must cascade to all task_entity_links
10. **Don't validate metadata schemas**: Entity metadata is generic JSON (no schema enforcement)

## Project Goals

**Success criteria:**
- Zero-config workspace detection in Claude Code
- Cross-client visibility (Claude Desktop can discover all projects)
- Concurrent read access without blocking
- Complete task lifecycle management with dependencies
- Rich entity tracking with bidirectional task-entity linking
- Flexible metadata storage for domain-specific entities
- 30-day soft delete safety net
- No token overflow from large descriptions
