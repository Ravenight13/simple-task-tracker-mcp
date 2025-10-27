# Task MCP Server - Project Brief

## Overview
Build a lightweight Model Context Protocol (MCP) server for task and subtask tracking during agentic AI project development. The server provides isolated SQLite databases per project workspace, enabling agents to create, track, and manage development tasks with file references, dependencies, and status tracking.

## Core Requirements

### Project Isolation
- **Database per workspace**: Use absolute workspace path as identifier
- **Auto-generation**: Hash workspace path to create safe DB filename (e.g., `project_a1b2c3d4.db`)
- **Storage location**: `~/.task-mcp/databases/`
- **Master database**: `~/.task-mcp/master.db` tracks all known projects for discovery
- **Zero-config**: DB auto-creates on first connection from workspace
- **Concurrent access**: SQLite WAL mode handles multiple readers + single writer automatically
- **Cross-client support**: Claude Code (auto-detects workspace) and Claude Desktop (explicit path) can both access project databases

### Task Management Features
1. Task and subtask hierarchy support
2. Status tracking with state machine: `todo → in_progress → blocked → done → cancelled`
3. File reference tracking (JSON array of file paths)
4. Explicit task dependencies (Task B depends on Task A)
5. Tag-based organization (space-separated tags for search/filter)
6. Priority levels (low/medium/high)
7. Blocker documentation (required when status = blocked)
8. Soft delete with 30-day cleanup
9. Agent context capture (conversation ID, timestamps)

### Data Constraints
- **Description field limit**: 10,000 characters maximum
- **No token overflow**: Prevent returning tasks with 25k+ token descriptions
- **Subtasks don't auto-block parents**: Parent can complete with open subtasks
- **Dependencies are hard blocks**: Task B cannot start until Task A completes

## Technical Stack

### Core Framework
- **FastMCP**: Python MCP server framework
- **Python 3.9+**: Minimum version
- **SQLite3**: Embedded database (comes with Python)

### Key Dependencies
```json
{
  "fastmcp": "latest",
  "sqlite3": "built-in",
  "hashlib": "built-in",
  "pathlib": "built-in",
  "datetime": "built-in",
  "json": "built-in"
}
```

### Project Structure
```
task-mcp/
├── src/
│   ├── task_mcp/
│   │   ├── __init__.py
│   │   ├── server.py          # FastMCP server setup
│   │   ├── database.py        # SQLite operations (project DBs)
│   │   ├── master.py          # Master DB operations (project registry)
│   │   ├── models.py          # Task data models
│   │   └── utils.py           # Path hashing, validation, workspace detection
├── tests/
│   └── test_task_mcp.py
├── README.md
├── pyproject.toml
└── uv.lock
```

## Database Schema

### Tasks Table
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,  -- Max 10k chars
    status TEXT NOT NULL CHECK(status IN ('todo', 'in_progress', 'blocked', 'done', 'cancelled')),
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
    parent_task_id INTEGER,
    depends_on TEXT,  -- JSON array of task IDs
    tags TEXT,  -- Space-separated tags
    blocker_reason TEXT,  -- Required when status='blocked'
    file_references TEXT,  -- JSON array of file paths
    created_by TEXT,  -- Conversation ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    deleted_at TIMESTAMP,  -- Soft delete timestamp
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
);

CREATE INDEX idx_status ON tasks(status);
CREATE INDEX idx_parent ON tasks(parent_task_id);
CREATE INDEX idx_deleted ON tasks(deleted_at);
CREATE INDEX idx_tags ON tasks(tags);
```

### Master Database (master.db)
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,                    -- Hash of workspace path (8 chars)
    workspace_path TEXT UNIQUE NOT NULL,    -- Absolute path to project
    friendly_name TEXT,                     -- Optional user-friendly name
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_last_accessed ON projects(last_accessed);
```

## MCP Tools to Implement

### Core CRUD
1. **create_task**
   - Input: title, workspace_path (optional), description, status, priority, parent_task_id, depends_on, tags, file_references
   - Auto-captures: created_by (conversation_id), created_at
   - Auto-detects: workspace_path if not provided (see Workspace Detection)
   - Validates: description length ≤ 10k chars
   - Returns: Full task object

2. **update_task**
   - Input: task_id, workspace_path (optional), fields to update
   - Auto-updates: updated_at
   - Validates: blocker_reason required if status='blocked'
   - Returns: Updated task object

3. **get_task**
   - Input: task_id, workspace_path (optional)
   - Excludes: Soft-deleted tasks
   - Returns: Full task object with all fields

4. **list_tasks**
   - Input: workspace_path (optional), filters (status, tags, parent_id, priority)
   - Excludes: Soft-deleted tasks
   - Returns: Array of task objects

5. **search_tasks**
   - Input: search_term, workspace_path (optional)
   - Searches: title and description fields (full-text)
   - Excludes: Soft-deleted tasks
   - Returns: Array of matching tasks

6. **delete_task**
   - Input: task_id, workspace_path (optional)
   - Action: Sets deleted_at timestamp (soft delete)
   - Returns: Success confirmation

### Advanced Queries
7. **get_task_tree**
   - Input: task_id, workspace_path (optional)
   - Returns: Task with all descendant subtasks (recursive)

8. **get_blocked_tasks**
   - Input: workspace_path (optional)
   - Returns: All tasks with status='blocked' and their blocker_reasons

9. **get_next_tasks**
   - Input: workspace_path (optional)
   - Returns: Tasks with status='todo', no unresolved dependencies, not blocked

### Maintenance
10. **cleanup_deleted_tasks**
    - Input: workspace_path (optional)
    - Runs automatically or on-demand
    - Permanently deletes tasks where deleted_at > 30 days ago
    - Returns: Count of purged tasks

### Project Management
11. **list_projects**
    - Returns: All known projects from master.db with metadata
    - Includes: id (hash), workspace_path, friendly_name, created_at, last_accessed
    - Sorted by: last_accessed (most recent first)

12. **get_project_info**
    - Input: workspace_path
    - Returns: Project metadata + task summary statistics
    - Statistics: total tasks, tasks by status, tasks by priority, blocked count

13. **set_project_name**
    - Input: workspace_path, friendly_name
    - Updates: friendly_name in master.db
    - Returns: Success confirmation

## Key Implementation Notes

### Workspace Detection
- MCP determines workspace path using priority order:
  1. **Explicit workspace_path** parameter in tool call (for Claude Desktop)
  2. **TASK_MCP_WORKSPACE** environment variable (for Claude Code)
  3. **Current working directory** as fallback
- Hash with SHA256, truncate to 8 chars for filename safety
- Create/connect to `~/.task-mcp/databases/project_{hash}.db`
- Auto-register new projects in master.db on first access
- Update last_accessed timestamp in master.db on every operation

### Validation Rules
1. Description ≤ 10,000 characters
2. status='blocked' requires blocker_reason
3. depends_on must reference valid task IDs
4. parent_task_id must reference valid task
5. tags are normalized (lowercase, single spaces)

### Dependency Checking
- When updating task status to 'in_progress' or 'done', verify all depends_on tasks are complete
- Block the update if dependencies aren't satisfied

### Soft Delete Behavior
- Soft-deleted tasks excluded from all queries by default
- Cleanup job removes tasks where `deleted_at < NOW() - 30 days`
- Subtasks of deleted task should cascade delete

### SQLite Configuration
- **WAL mode**: Enable Write-Ahead Logging for concurrent access
```python
  conn.execute("PRAGMA journal_mode=WAL")
```
- **Busy timeout**: Set reasonable timeout for lock contention
```python
  conn.execute("PRAGMA busy_timeout=5000")  # 5 seconds
```
- **Foreign keys**: Enable for referential integrity
```python
  conn.execute("PRAGMA foreign_keys=ON")
```
- These settings enable multiple readers + single writer without blocking

## Success Criteria
1. Agent can create task with single call, auto-creates DB
2. Task hierarchy works (parent/subtasks)
3. Dependencies correctly block task progression
4. Search finds tasks by title/description/tags
5. Soft delete prevents data loss for 30 days
6. All tools return proper FastMCP responses
7. No 25k+ token task descriptions can be created or returned
8. **Claude Code auto-detects workspace without configuration**
9. **Claude Desktop can discover and access all projects via explicit paths**
10. **Master database tracks all projects for cross-client visibility**
11. **Concurrent reads work seamlessly between Claude Code and Desktop**

## Development Approach
1. Use FastMCP skill/guide for proper MCP implementation
2. Start with database setup and core models
3. Implement CRUD operations first
4. Add search and advanced queries
5. Add cleanup/maintenance tools
6. Write tests for validation rules
7. Document all tools in README

## FastMCP Server Configuration
Server should register with Claude Desktop/Code via standard MCP configuration:
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

## Expected Usage Patterns

### Claude Code (Auto-Detection)
1. Agent starts work in project directory `/path/to/project`
2. Agent sets `TASK_MCP_WORKSPACE=/path/to/project` in environment
3. Agent calls `create_task(title="Build API")` - no workspace_path needed
4. MCP auto-detects workspace, creates/opens `~/.task-mcp/databases/project_abc123.db`
5. Registers project in master.db if first access
6. Agent queries tasks, updates status, creates subtasks - all auto-scoped to workspace

### Claude Desktop (Explicit Path)
1. User wants to check project status from chat interface
2. User asks: "Show me tasks for my API project"
3. Agent calls `list_projects()` to discover available projects
4. Agent finds: `/Users/username/projects/api-server` (hash: abc123)
5. Agent calls `list_tasks(workspace_path="/Users/username/projects/api-server")`
6. Agent can query, update, create tasks by always passing workspace_path
7. Enables visibility and management across all projects from one interface

### Cross-Client Scenario
1. Claude Code working on project, creating and updating tasks
2. Claude Desktop user asks for status update
3. Both read from same `project_abc123.db` via SQLite WAL mode
4. SQLite handles concurrent reads seamlessly
5. If both try to write, SQLite's locking ensures data integrity

---

**Build this clean, fast, and functional. Focus on the core loop first, optimize later.**