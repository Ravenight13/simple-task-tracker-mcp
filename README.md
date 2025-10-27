# Task MCP Server

A lightweight Model Context Protocol (MCP) server for task and subtask tracking during agentic AI development. Provides isolated SQLite databases per project workspace for Claude Code and Claude Desktop integration.

## Features

### 🎯 Core Capabilities
- **Project Isolation**: Separate SQLite database per workspace (auto-detected)
- **Task Hierarchy**: Parent/child task relationships with unlimited nesting
- **Dependencies**: Explicit task dependencies with validation
- **Status Tracking**: State machine workflow (todo → in_progress → blocked → done → cancelled)
- **Soft Delete**: 30-day retention before permanent deletion
- **Full-Text Search**: Search tasks by title and description
- **Tag Organization**: Space-separated tags with normalization
- **Concurrent Access**: SQLite WAL mode for simultaneous Claude Code + Desktop reads

### 🔒 Data Validation
- Description length limit (10,000 characters)
- Status/Priority enum validation
- Blocker reason requirement when status='blocked'
- Dependency resolution before task completion
- Tag normalization (lowercase, single spaces)

### 📊 Database Architecture
- **Per-project databases**: `~/.task-mcp/databases/project_{hash}.db`
- **Master registry**: `~/.task-mcp/master.db` (cross-client discovery)
- **Workspace detection**: Explicit parameter → TASK_MCP_WORKSPACE env → current directory
- **Path hashing**: SHA256 truncated to 8 characters for safe filenames

## Installation

### Prerequisites
- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Install from Source

```bash
# Clone repository
git clone https://github.com/Ravenight13/simple-task-tracker-mcp.git
cd simple-task-tracker-mcp

# Install dependencies
uv sync --dev

# Verify installation
uv run task-mcp --help
```

### Install as Package

```bash
# Install with uv
uv pip install git+https://github.com/Ravenight13/simple-task-tracker-mcp.git

# Or with pip
pip install git+https://github.com/Ravenight13/simple-task-tracker-mcp.git
```

## Configuration

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "task-mcp": {
      "command": "uv",
      "args": ["run", "task-mcp"],
      "env": {
        "TASK_MCP_WORKSPACE": "/path/to/your/project"
      }
    }
  }
}
```

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

### Claude Code

For Claude Code, the server auto-detects the workspace from the current working directory. Add to `.claude/config.json`:

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

The `TASK_MCP_WORKSPACE` environment variable is automatically set by Claude Code based on the active project.

## Quick Start

### Create a Task

```python
# Via MCP tool
create_task(
    title="Implement authentication API",
    description="Add JWT-based authentication to the REST API",
    status="todo",
    priority="high",
    tags="backend api authentication"
)
```

### List Tasks

```python
# Get all tasks
list_tasks()

# Filter by status
list_tasks(status="in_progress")

# Filter by priority and tags
list_tasks(priority="high", tags="backend")
```

### Search Tasks

```python
# Full-text search
search_tasks("authentication")
```

### Update Task Status

```python
update_task(
    task_id=1,
    status="in_progress"
)
```

### Create Subtasks

```python
# Create parent task
parent = create_task(title="Build Authentication System")

# Create subtasks
create_task(
    title="Design database schema",
    parent_task_id=parent['id']
)

create_task(
    title="Implement JWT generation",
    parent_task_id=parent['id']
)

# Get full task tree
get_task_tree(parent['id'])
```

### Task Dependencies

```python
# Create tasks with dependencies
task1 = create_task(title="Set up database")
task2 = create_task(title="Create API endpoints", depends_on=[task1['id']])

# Get next actionable tasks (no unresolved dependencies)
get_next_tasks()
```

## MCP Tools Reference

### Core CRUD Operations

#### create_task
Create a new task with validation.

**Parameters:**
- `title` (str, required): Task title
- `workspace_path` (str | None): Optional workspace path (auto-detected)
- `description` (str | None): Task description (max 10k chars)
- `status` (str): Task status (default: "todo")
- `priority` (str): Priority level (default: "medium")
- `parent_task_id` (int | None): Parent task ID for subtasks
- `depends_on` (list[int] | None): List of task IDs this depends on
- `tags` (str | None): Space-separated tags
- `file_references` (list[str] | None): List of file paths
- `created_by` (str | None): Conversation ID

**Returns:** Task object with all fields

**Example:**
```python
task = create_task(
    title="Implement user registration",
    description="Create registration endpoint with email validation",
    priority="high",
    tags="backend api user-management",
    file_references=["src/api/auth.py", "tests/test_auth.py"]
)
```

#### get_task
Fetch a single task by ID.

**Parameters:**
- `task_id` (int, required): Task ID
- `workspace_path` (str | None): Optional workspace path

**Returns:** Task object

**Example:**
```python
task = get_task(task_id=1)
print(task['title'], task['status'])
```

#### update_task
Update an existing task with validation.

**Parameters:**
- `task_id` (int, required): Task ID
- `workspace_path` (str | None): Optional workspace path
- `title` (str | None): Updated title
- `description` (str | None): Updated description
- `status` (str | None): Updated status
- `priority` (str | None): Updated priority
- `blocker_reason` (str | None): Required when status='blocked'
- Other fields as needed

**Returns:** Updated task object

**Example:**
```python
# Mark task as blocked
update_task(
    task_id=1,
    status="blocked",
    blocker_reason="Waiting for API key from infrastructure team"
)

# Complete task
update_task(task_id=1, status="done")
```

#### list_tasks
List tasks with optional filters.

**Parameters:**
- `workspace_path` (str | None): Optional workspace path
- `status` (str | None): Filter by status
- `priority` (str | None): Filter by priority
- `parent_task_id` (int | None): Filter by parent task
- `tags` (str | None): Filter by tags (partial match)

**Returns:** List of task objects

**Example:**
```python
# Get all high-priority in-progress tasks
tasks = list_tasks(status="in_progress", priority="high")

# Get all subtasks of a parent
subtasks = list_tasks(parent_task_id=5)

# Get tasks by tag
backend_tasks = list_tasks(tags="backend")
```

#### search_tasks
Full-text search on task title and description.

**Parameters:**
- `search_term` (str, required): Search term
- `workspace_path` (str | None): Optional workspace path

**Returns:** List of matching tasks

**Example:**
```python
results = search_tasks("authentication")
```

#### delete_task
Soft delete a task (sets deleted_at timestamp).

**Parameters:**
- `task_id` (int, required): Task ID
- `workspace_path` (str | None): Optional workspace path
- `cascade` (bool): If True, also delete all subtasks (default: False)

**Returns:** Success confirmation with deleted count

**Example:**
```python
# Delete single task
delete_task(task_id=1)

# Delete task and all subtasks
delete_task(task_id=1, cascade=True)
```

### Advanced Query Tools

#### get_task_tree
Get task with all descendant subtasks (recursive).

**Parameters:**
- `task_id` (int, required): Root task ID
- `workspace_path` (str | None): Optional workspace path

**Returns:** Task object with nested 'subtasks' field

**Example:**
```python
tree = get_task_tree(task_id=1)
print(tree['title'])
for subtask in tree['subtasks']:
    print(f"  - {subtask['title']}")
```

#### get_blocked_tasks
Get all tasks with status='blocked'.

**Parameters:**
- `workspace_path` (str | None): Optional workspace path

**Returns:** List of blocked tasks with blocker_reason

**Example:**
```python
blocked = get_blocked_tasks()
for task in blocked:
    print(f"{task['title']}: {task['blocker_reason']}")
```

#### get_next_tasks
Get actionable tasks (status='todo', no unresolved dependencies).

**Parameters:**
- `workspace_path` (str | None): Optional workspace path

**Returns:** List of actionable tasks sorted by priority DESC, created_at ASC

**Example:**
```python
next_tasks = get_next_tasks()
if next_tasks:
    print(f"Next task to work on: {next_tasks[0]['title']}")
```

### Maintenance Tools

#### cleanup_deleted_tasks
Permanently delete tasks soft-deleted more than N days ago.

**Parameters:**
- `workspace_path` (str | None): Optional workspace path
- `days` (int): Retention days (default: 30)

**Returns:** Count of purged tasks

**Example:**
```python
# Purge tasks deleted >30 days ago
result = cleanup_deleted_tasks()
print(f"Purged {result['purged_count']} tasks")

# Custom retention period
cleanup_deleted_tasks(days=60)
```

### Project Management Tools

#### list_projects
List all known projects from master database.

**Returns:** List of projects sorted by last_accessed DESC

**Example:**
```python
projects = list_projects()
for project in projects:
    print(f"{project['friendly_name']}: {project['workspace_path']}")
```

#### get_project_info
Get project metadata and task statistics.

**Parameters:**
- `workspace_path` (str, required): Project workspace path

**Returns:** Project info with task counts by status and priority

**Example:**
```python
info = get_project_info("/path/to/project")
print(f"Total tasks: {info['total_tasks']}")
print(f"By status: {info['by_status']}")
print(f"Blocked: {info['blocked_count']}")
```

#### set_project_name
Set friendly name for a project.

**Parameters:**
- `workspace_path` (str, required): Project workspace path
- `friendly_name` (str, required): Human-readable project name

**Returns:** Success confirmation

**Example:**
```python
set_project_name("/path/to/project", "My Awesome Project")
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=task_mcp --cov-report=html

# Run specific test file
uv run pytest tests/test_database.py -v

# Run specific test
uv run pytest tests/test_database.py::TestDatabase::test_get_connection_creates_database
```

### Quality Gates

```bash
# Linting
uv run ruff check src/ tests/

# Type checking
uv run mypy src/

# Format code
uv run black src/ tests/
```

### Project Structure

```
task-mcp/
├── src/task_mcp/
│   ├── __init__.py
│   ├── server.py          # FastMCP server + tool registration
│   ├── database.py        # Project database operations
│   ├── master.py          # Master database (project registry)
│   ├── models.py          # Pydantic data models
│   └── utils.py           # Utilities (workspace detection, hashing)
├── tests/
│   ├── test_database.py   # Database integration tests
│   ├── test_models.py     # Model validation tests
│   └── test_mcp_tools.py  # MCP tools integration tests
├── pyproject.toml         # Project configuration
└── README.md
```

### Database Schema

**Tasks Table** (`tasks`):
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('todo', 'in_progress', 'blocked', 'done', 'cancelled')),
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
    parent_task_id INTEGER,
    depends_on TEXT,  -- JSON array of task IDs
    tags TEXT,  -- Space-separated tags
    blocker_reason TEXT,
    file_references TEXT,  -- JSON array of file paths
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    deleted_at TIMESTAMP,
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
);

-- Indexes
CREATE INDEX idx_status ON tasks(status);
CREATE INDEX idx_parent ON tasks(parent_task_id);
CREATE INDEX idx_deleted ON tasks(deleted_at);
CREATE INDEX idx_tags ON tasks(tags);
```

**Projects Table** (`master.db`):
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,  -- 8-char hash
    workspace_path TEXT UNIQUE NOT NULL,
    friendly_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_last_accessed ON projects(last_accessed);
```

## Troubleshooting

### Database Location

Databases are stored at:
- Project databases: `~/.task-mcp/databases/project_{hash}.db`
- Master database: `~/.task-mcp/master.db`

To inspect manually:
```bash
sqlite3 ~/.task-mcp/master.db "SELECT * FROM projects;"
```

### Workspace Detection Issues

Check workspace resolution priority:
1. Explicit `workspace_path` parameter (highest priority)
2. `TASK_MCP_WORKSPACE` environment variable
3. Current working directory (fallback)

Verify workspace detection:
```python
from task_mcp.utils import resolve_workspace
print(resolve_workspace())
```

### Reset Project Database

```bash
# Find project hash
python -c "from task_mcp.utils import hash_workspace_path; print(hash_workspace_path('/path/to/project'))"

# Remove database
rm ~/.task-mcp/databases/project_{hash}.db
```

## License

MIT License - see LICENSE file

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all quality gates pass (ruff, mypy, pytest)
5. Submit a pull request

## Acknowledgments

Built with:
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server framework
- [Pydantic v2](https://docs.pydantic.dev/) - Data validation
- SQLite - Embedded database