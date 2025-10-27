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

(To be continued in Part 2...)