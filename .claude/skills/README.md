# Claude Code Skills

This directory contains custom skills for the Task MCP project.

## What Are Skills?

Skills extend Claude's capabilities with specialized knowledge, workflows, or tool integrations. They are loaded into the main conversation context.

## Creating a Skill

Create a Markdown file in this directory:

```markdown
<!-- Example: .claude/skills/fastmcp-patterns.md -->
# FastMCP Implementation Patterns

This skill provides expertise in building FastMCP tools following best practices.

## Tool Structure

Every MCP tool should follow this pattern:

1. Input validation (description limits, required fields)
2. Workspace resolution (explicit → env → cwd)
3. Database connection with proper configuration
4. Business logic with error handling
5. Return structured response

## Common Patterns

### Workspace Resolution
\`\`\`python
def resolve_workspace(workspace_path: str | None = None) -> str:
    if workspace_path:
        return workspace_path
    if env_workspace := os.getenv("TASK_MCP_WORKSPACE"):
        return env_workspace
    return os.getcwd()
\`\`\`

### Database Connection
\`\`\`python
def get_connection(workspace_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn
\`\`\`

## Validation Rules

- Description ≤ 10,000 characters
- Blocker status requires blocker_reason
- Dependencies must exist and not be deleted
- Status transitions must respect state machine
```

## Suggested Skills for This Project

### `fastmcp-patterns.md`
FastMCP best practices, tool structure patterns, and validation templates.

### `sqlite-wal.md`
SQLite WAL mode configuration, concurrent access patterns, and performance tuning.

### `task-state-machine.md`
Task status state machine rules, transition validation, and dependency checking.

### `testing-workflows.md`
MCP tool testing strategies, fixture patterns, and end-to-end test scenarios.

## Usage

Skills are invoked via:
```
/skill <skill-name>
```

Or Claude Code auto-loads them based on context.
