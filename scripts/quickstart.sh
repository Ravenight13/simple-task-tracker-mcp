#!/bin/bash
# Quick start script for Task MCP server

set -e

echo "=== Task MCP Server Quick Start ==="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ uv is installed"

# Install dependencies
echo ""
echo "Installing dependencies..."
uv sync --dev

# Run validation
echo ""
echo "Running validation..."
uv run python scripts/validate_config.py

# Run tests
echo ""
echo "Running tests..."
uv run pytest -v

# Show configuration instructions
echo ""
echo "=== Configuration Instructions ==="
echo ""
echo "For Claude Desktop, add to claude_desktop_config.json:"
echo ""
echo '{
  "mcpServers": {
    "task-mcp": {
      "command": "uv",
      "args": ["run", "task-mcp"],
      "env": {
        "TASK_MCP_WORKSPACE": "'$(pwd)'"
      }
    }
  }
}'
echo ""
echo "For Claude Code, add to .claude/config.json:"
echo ""
echo '{
  "mcpServers": {
    "task-mcp": {
      "command": "uv",
      "args": ["run", "task-mcp"]
    }
  }
}'
echo ""
echo "✓ Setup complete!"
echo "Restart Claude Desktop/Code to use the Task MCP server."
