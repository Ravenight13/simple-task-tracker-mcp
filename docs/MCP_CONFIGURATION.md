# MCP Server Configuration Guide

Complete guide for configuring the Task MCP server with Claude Desktop and Claude Code.

## Claude Desktop Configuration

### Location

Configuration file location by platform:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Basic Configuration

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

### With Explicit Workspace

```json
{
  "mcpServers": {
    "task-mcp": {
      "command": "uv",
      "args": ["run", "task-mcp"],
      "env": {
        "TASK_MCP_WORKSPACE": "/Users/username/projects/my-project"
      }
    }
  }
}
```

### Multiple Projects

You can configure multiple instances for different projects:

```json
{
  "mcpServers": {
    "task-mcp-project-a": {
      "command": "uv",
      "args": ["run", "task-mcp"],
      "env": {
        "TASK_MCP_WORKSPACE": "/path/to/project-a"
      }
    },
    "task-mcp-project-b": {
      "command": "uv",
      "args": ["run", "task-mcp"],
      "env": {
        "TASK_MCP_WORKSPACE": "/path/to/project-b"
      }
    }
  }
}
```

## Claude Code Configuration

### Location

Project-specific configuration: `<project>/.claude/config.json`

### Basic Configuration

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

**Note**: Claude Code automatically sets `TASK_MCP_WORKSPACE` to the current project directory, so you don't need to specify it.

### Using System-Installed Package

If you installed task-mcp globally:

```json
{
  "mcpServers": {
    "task-mcp": {
      "command": "task-mcp"
    }
  }
}
```

### Using Python Directly

```json
{
  "mcpServers": {
    "task-mcp": {
      "command": "python",
      "args": ["-m", "task_mcp.server"]
    }
  }
}
```

## Environment Variables

### TASK_MCP_WORKSPACE

Specifies the workspace path for task isolation.

**Priority order:**
1. Explicit `workspace_path` parameter in tool calls
2. `TASK_MCP_WORKSPACE` environment variable
3. Current working directory (fallback)

**Example:**
```bash
export TASK_MCP_WORKSPACE=/path/to/project
```

### HOME

Used to locate the `.task-mcp/` directory.

Default storage locations:
- Project databases: `$HOME/.task-mcp/databases/`
- Master database: `$HOME/.task-mcp/master.db`

## Verification

### Test Configuration

After configuring, test the connection:

1. **Restart Claude Desktop/Code**
2. **Check server list**: MCP servers should appear in the tools menu
3. **Test a tool call**:
   ```
   Create a test task using create_task
   ```

### Debug Mode

Enable debug logging:

```json
{
  "mcpServers": {
    "task-mcp": {
      "command": "uv",
      "args": ["run", "task-mcp"],
      "env": {
        "DEBUG": "true"
      }
    }
  }
}
```

### Manual Testing

Test the server manually:

```bash
# Run server
uv run task-mcp

# The server should start and register 13 tools
```

## Troubleshooting

### Server Not Appearing

1. Check JSON syntax (use a JSON validator)
2. Verify file location is correct
3. Restart Claude Desktop/Code completely
4. Check logs (if available)

### Permission Errors

Ensure the command is executable:

```bash
which uv
# Should return path to uv

uv run task-mcp --help
# Should show help or start server
```

### Workspace Not Detected

Check workspace resolution:

```python
from task_mcp.utils import resolve_workspace
import os

print(f"Workspace: {resolve_workspace()}")
print(f"ENV: {os.getenv('TASK_MCP_WORKSPACE', 'Not set')}")
print(f"CWD: {os.getcwd()}")
```

### Database Issues

Check database location:

```bash
ls -la ~/.task-mcp/
ls -la ~/.task-mcp/databases/
```

Reset if needed:
```bash
rm -rf ~/.task-mcp/
```

## Advanced Configuration

### Custom Database Location

Modify source code in `src/task_mcp/utils.py`:

```python
def get_project_db_path(workspace_path: str | None = None) -> Path:
    # Change base_dir to custom location
    base_dir = Path.home() / ".task-mcp" / "databases"
```

### Security Considerations

- Database files contain task data in plain text
- No encryption by default
- Stored in user's home directory (~/.task-mcp/)
- Consider file permissions if sharing the system

Recommended permissions:
```bash
chmod 700 ~/.task-mcp
chmod 600 ~/.task-mcp/databases/*.db
```

## Examples

### Example 1: Claude Desktop with Single Project

```json
{
  "mcpServers": {
    "task-mcp": {
      "command": "/Users/username/.local/bin/uv",
      "args": ["run", "task-mcp"],
      "env": {
        "TASK_MCP_WORKSPACE": "/Users/username/projects/my-app"
      }
    }
  }
}
```

### Example 2: Claude Code (Auto-Detection)

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

### Example 3: Development Mode

```json
{
  "mcpServers": {
    "task-mcp-dev": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/task-mcp-repo", "task-mcp"],
      "env": {
        "DEBUG": "true"
      }
    }
  }
}
```
