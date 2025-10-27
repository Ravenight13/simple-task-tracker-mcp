# SQL Database Schemas

## Project Database Schema (project_{hash}.db)

### Tasks Table

```sql
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    deleted_at TIMESTAMP,
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
);
```

### Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_parent ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_deleted ON tasks(deleted_at);
CREATE INDEX IF NOT EXISTS idx_tags ON tasks(tags);
```

### Field Descriptions

- **id**: Auto-incrementing primary key
- **title**: Task title (required)
- **description**: Task description (max 10,000 chars via app validation)
- **status**: Task status (must be one of: 'todo', 'in_progress', 'blocked', 'done', 'cancelled')
- **priority**: Task priority (default 'medium', must be: 'low', 'medium', 'high')
- **parent_task_id**: Optional parent task for subtask hierarchy
- **depends_on**: JSON array of task IDs for explicit dependencies
- **tags**: Space-separated tags for search/filtering
- **blocker_reason**: Required when status='blocked'
- **file_references**: JSON array of file paths
- **created_by**: Conversation ID from MCP context
- **created_at**: Auto-set timestamp on creation
- **updated_at**: Auto-updated on modification
- **completed_at**: Set when status changes to 'done'
- **deleted_at**: Soft delete timestamp (NULL if not deleted)

---

## Master Database Schema (master.db)

### Projects Table

```sql
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    workspace_path TEXT UNIQUE NOT NULL,
    friendly_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_last_accessed ON projects(last_accessed);
```

### Field Descriptions

- **id**: 8-character hash of workspace path (primary key)
- **workspace_path**: Absolute path to project workspace (unique)
- **friendly_name**: Optional user-friendly project name
- **created_at**: Timestamp when project was first registered
- **last_accessed**: Updated on every operation to track active projects

---

## SQLite Configuration

All database connections are configured with the following critical pragmas:

```python
conn.execute("PRAGMA journal_mode=WAL")      # Enable concurrent reads
conn.execute("PRAGMA foreign_keys=ON")       # Enforce referential integrity
conn.execute("PRAGMA busy_timeout=5000")     # 5-second lock timeout
```

### Why These Settings Matter

1. **WAL Mode (Write-Ahead Logging)**: Enables concurrent reads while a write is in progress. Essential for Claude Code and Claude Desktop to access databases simultaneously.

2. **Foreign Keys**: Ensures parent_task_id references are valid, preventing orphaned subtasks.

3. **Busy Timeout**: Prevents immediate errors when database is locked, retrying for up to 5 seconds.

---

## Database Location

- Project databases: `~/.task-mcp/databases/project_{hash}.db`
- Master database: `~/.task-mcp/master.db`

Where `{hash}` is the first 8 characters of SHA256 hash of absolute workspace path.
