# Claude Code Agents

This directory contains specialized agent definitions for the Task MCP project.

## What Are Agents?

Agents are autonomous subagents that Claude Code can invoke to handle complex, multi-step tasks. They run independently and return results when complete.

## Creating an Agent

Create a YAML file in this directory:

```yaml
# Example: .claude/agents/database-specialist.yaml
name: database-specialist
description: SQLite database expert for Task MCP
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
prompt: |
  You are a SQLite database specialist for the Task MCP project.

  Your expertise includes:
  - Schema design and migrations
  - WAL mode configuration
  - Query optimization
  - Concurrent access patterns

  When working with Task MCP databases:
  - Always enable WAL mode, foreign keys, and busy timeout
  - Validate all constraints before schema changes
  - Test migrations with sample data
  - Document breaking changes
```

## Suggested Agents for This Project

### `mcp-tool-builder.yaml`
Expert in building FastMCP tools with proper validation, error handling, and documentation.

### `sqlite-specialist.yaml`
Database design and optimization specialist for SQLite with WAL mode and concurrent access.

### `test-automation.yaml`
Testing specialist for MCP tool validation, integration tests, and end-to-end workflows.

### `dependency-validator.yaml`
Expert in validating task dependencies and ensuring state machine integrity.

## Usage

Agents are invoked programmatically via the Task tool:
```
Task tool with subagent_type="database-specialist"
```

Claude Code will automatically discover agents in this directory.
