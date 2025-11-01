# Global Claude Code Config Update - 2025-11-01

## Overview
Updated the global Claude Code configuration file (`~/.claude.json`) to use the uv-based method with `--directory` flag for all task-mcp server configurations across multiple projects.

## Problem
The global config file had 4 project entries with hardcoded paths to the old folder name or .venv locations:
1. `/Users/cliffclarke/Claude_Code/commission-processing-vendor-extractors`
2. `/Users/cliffclarke/Claude_Code/workflow-mcp`
3. `/Users/cliffclarke/Claude_Code/simple-task-tracker-mcp` (old folder name)
4. `/Users/cliffclarke/Claude_Code/task-mcp` (had empty mcpServers)

## Solution Applied

### Before (all 4 projects)
```json
"task-mcp": {
  "command": "/Users/cliffclarke/Claude_Code/task-mcp/.venv/bin/task-mcp"
}
```

### After (all 4 projects)
```json
"task-mcp": {
  "command": "uv",
  "args": [
    "--directory",
    "/Users/cliffclarke/Claude_Code/task-mcp",
    "run",
    "task-mcp"
  ]
}
```

## Files Modified
- `~/.claude.json` - Global Claude Code configuration (4 project entries updated)

## Benefits
1. **Path independence**: Works regardless of folder renames
2. **Consistency**: All projects now use the same configuration method
3. **Maintainability**: Single source of truth for the project location
4. **Reliability**: uv resolves the correct virtual environment automatically

## Projects Updated
1. ✅ commission-processing-vendor-extractors (line 114-121)
2. ✅ workflow-mcp (line 212-219)
3. ✅ simple-task-tracker-mcp (line 268-275)
4. ✅ task-mcp (line 299-306, added new config)

## Verification
All 4 project configurations now use the uv --directory method:
```bash
grep -A 8 '"task-mcp"' ~/.claude.json | grep -E '(command|args|directory)'
```

## Next Steps
1. ✅ Restart Claude Code to reload the global configuration
2. Test MCP connectivity in each of the 4 projects
3. Verify task-mcp tools are accessible in all workspaces
4. Consider updating other MCP servers (codebase-mcp) to use similar method

## Related Changes
- `.claude/config.json` (workspace-specific config) - Updated in same session
- `~/Library/Application Support/Claude/claude_desktop_config.json` - Updated in same session
- See related reports:
  - docs/subagent-reports/mcp-config/desktop/2025-11-01-desktop-config-update.md
  - docs/subagent-reports/mcp-config/claude-code/2025-11-01-claude-code-config-update.md

## Notes
- The global config file is shared across all Claude Code sessions
- Each project can also have its own workspace-specific `.claude/config.json`
- The workspace-specific config takes precedence when both exist
- Claude Code will automatically merge configurations from both sources
