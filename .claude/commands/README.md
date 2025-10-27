# Claude Code Slash Commands

This directory contains slash commands for the Task MCP project.

## What Are Slash Commands?

Slash commands are quick shortcuts that expand into prompts for frequently used workflows.

## Creating a Slash Command

Create a Markdown file in this directory:

```markdown
<!-- Example: .claude/commands/test-mcp.md -->
Run the full MCP server test suite with pytest, including:
- Unit tests for all database operations
- Validation tests for constraints
- Integration tests for tool workflows
- End-to-end tests with workspace detection

After tests complete, analyze any failures and suggest fixes.
```

## Suggested Commands for This Project

### `/test-mcp`
Run complete MCP test suite with failure analysis.

### `/validate-schema`
Verify database schema matches specification, check all constraints and indexes.

### `/review-tools`
Review all MCP tool implementations for consistency, validation, and documentation.

### `/check-dependencies`
Analyze task dependency graph for circular dependencies or orphaned tasks.

### `/benchmark-db`
Run performance benchmarks on database operations (concurrent reads/writes).

### `/update-docs`
Regenerate documentation for all MCP tools and update README.

### `/deploy-check`
Pre-deployment checklist: tests pass, schema valid, tools documented, examples work.

## Usage

Invoke commands with:
```
/test-mcp
/validate-schema
```

## Command Naming Conventions

- Use kebab-case: `test-mcp`, not `testMCP`
- Be descriptive but concise
- Group related commands with prefixes: `db-migrate`, `db-backup`, `db-restore`
