# Claude Code Configuration

This directory contains Claude Code configuration files for agents, skills, and slash commands.

## Directory Structure

```
.claude/
├── agents/       # Specialized subagents for complex tasks
├── skills/       # Custom skills that extend Claude's capabilities
└── commands/     # Slash commands for quick workflows
```

## What Goes Where

### `/agents`
Define specialized subagents that can be invoked via the Task tool. Agents are autonomous workers that handle complex, multi-step tasks. Useful for this project:
- Database migration agents
- Testing specialists
- Code review agents for MCP tool implementations

### `/skills`
Custom skills that provide specialized knowledge or workflows. Skills are loaded into the main conversation context. Useful for this project:
- FastMCP implementation patterns
- SQLite optimization techniques
- MCP tool testing workflows

### `/commands`
Slash commands for frequently used workflows. Commands are quick shortcuts that expand into prompts. Useful for this project:
- `/test-mcp` - Run MCP server tests
- `/validate-schema` - Check database schema integrity
- `/review-tools` - Review all MCP tool implementations

## Documentation

See individual README files in each subdirectory for detailed usage instructions.
