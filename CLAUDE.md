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
- Soft delete: `deleted_at` timestamp instead of hard deletion (30-day retention)
- State machine: `todo → in_progress → blocked → done → cancelled`

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
- `database.py`: WAL mode configuration, connection pooling, foreign key enforcement
- `models.py`: 10k char description limit, blocker_reason validation, status transitions
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
- **Description limit**: 10,000 characters maximum (prevent token overflow)
- **Blocked status**: Requires `blocker_reason` field when status='blocked'
- **Dependencies**: Task cannot progress to 'in_progress' or 'done' if depends_on tasks incomplete
- **Subtasks independence**: Parent can complete with open subtasks (not auto-blocked)

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
- **CRUD**: create_task, update_task, get_task, list_tasks, delete_task
- **Search**: search_tasks (full-text on title/description)
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

## Common Pitfalls to Avoid

1. **Don't hard-delete tasks**: Always use soft delete (set `deleted_at`)
2. **Don't forget WAL mode**: Required for concurrent Claude Code + Desktop access
3. **Don't return deleted tasks**: All queries must filter `WHERE deleted_at IS NULL`
4. **Don't allow 25k+ token descriptions**: Validate 10k char limit on input
5. **Don't forget master.db updates**: Every operation must update `last_accessed`
6. **Don't cascade parent blocking**: Subtasks don't automatically block parents
7. **Don't skip dependency validation**: Check all depends_on tasks before status changes

## Project Goals

**Success criteria:**
- Zero-config workspace detection in Claude Code
- Cross-client visibility (Claude Desktop can discover all projects)
- Concurrent read access without blocking
- Complete task lifecycle management with dependencies
- 30-day soft delete safety net
- No token overflow from large descriptions
