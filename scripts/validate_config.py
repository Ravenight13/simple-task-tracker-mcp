#!/usr/bin/env python3
"""Validate Task MCP server configuration and environment."""

import json
import os
import sys
from pathlib import Path
import subprocess


def check_python_version() -> bool:
    """Check Python version >= 3.9."""
    version = sys.version_info
    if version < (3, 9):
        print(f"❌ Python {version.major}.{version.minor} is too old (need >= 3.9)")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_uv_installed() -> bool:
    """Check if uv is installed."""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ uv installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    print("❌ uv not installed")
    print("   Install: curl -LsSf https://astral.sh/uv/install.sh | sh")
    return False


def check_task_mcp_installed() -> bool:
    """Check if task-mcp package is installed."""
    try:
        result = subprocess.run(
            ['uv', 'run', 'python', '-c', 'import task_mcp; print(task_mcp.__version__)'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ task-mcp installed: {result.stdout.strip()}")
            return True
    except Exception:
        pass

    print("❌ task-mcp not installed")
    print("   Run: uv sync")
    return False


def check_config_file(config_path: Path) -> bool:
    """Check if config file exists and is valid JSON."""
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False

    print(f"✓ Config file exists: {config_path}")

    try:
        with open(config_path) as f:
            config = json.load(f)

        if 'mcpServers' not in config:
            print("❌ Config missing 'mcpServers' key")
            return False

        if 'task-mcp' not in config['mcpServers']:
            print("⚠ Config does not include 'task-mcp' server")
            return False

        server_config = config['mcpServers']['task-mcp']
        print(f"✓ task-mcp server configured")
        print(f"  Command: {server_config.get('command')}")
        print(f"  Args: {server_config.get('args')}")

        if 'env' in server_config and 'TASK_MCP_WORKSPACE' in server_config['env']:
            workspace = server_config['env']['TASK_MCP_WORKSPACE']
            print(f"  Workspace: {workspace}")
            if not Path(workspace).exists():
                print(f"  ⚠ Workspace directory does not exist: {workspace}")

        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config: {e}")
        return False


def check_workspace_detection() -> bool:
    """Check workspace detection."""
    try:
        result = subprocess.run(
            ['uv', 'run', 'python', '-c',
             'from task_mcp.utils import resolve_workspace; print(resolve_workspace())'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            workspace = result.stdout.strip()
            print(f"✓ Workspace detection works: {workspace}")
            return True
    except Exception as e:
        print(f"❌ Workspace detection failed: {e}")

    return False


def check_database_directory() -> bool:
    """Check if database directory exists and is writable."""
    db_dir = Path.home() / ".task-mcp"

    if not db_dir.exists():
        print(f"⚠ Database directory does not exist: {db_dir}")
        print("  (Will be created on first use)")
        return True

    if not db_dir.is_dir():
        print(f"❌ {db_dir} exists but is not a directory")
        return False

    # Check write permissions
    if not os.access(db_dir, os.W_OK):
        print(f"❌ Database directory not writable: {db_dir}")
        return False

    print(f"✓ Database directory: {db_dir}")

    # Count databases
    databases_dir = db_dir / "databases"
    if databases_dir.exists():
        db_count = len(list(databases_dir.glob("*.db")))
        print(f"  {db_count} project database(s)")

    master_db = db_dir / "master.db"
    if master_db.exists():
        print(f"  Master database exists")

    return True


def check_quality_gates() -> bool:
    """Check if quality gate tools are available."""
    tools = ['ruff', 'mypy', 'pytest']
    all_ok = True

    for tool in tools:
        try:
            result = subprocess.run(['uv', 'run', tool, '--version'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ {tool} available")
            else:
                print(f"⚠ {tool} not available")
                all_ok = False
        except Exception:
            print(f"⚠ {tool} not available")
            all_ok = False

    return all_ok


def main() -> int:
    """Run all validation checks."""
    print("=== Task MCP Server Configuration Validation ===\n")

    checks: list[tuple[str, callable]] = [
        ("Python Version", check_python_version),
        ("uv Package Manager", check_uv_installed),
        ("task-mcp Package", check_task_mcp_installed),
        ("Workspace Detection", check_workspace_detection),
        ("Database Directory", check_database_directory),
        ("Quality Gate Tools", check_quality_gates),
    ]

    results: list[bool] = []
    for name, check_func in checks:
        print(f"\n{name}:")
        results.append(check_func())

    # Check config files
    print("\nConfiguration Files:")
    config_locations = [
        Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",  # macOS
        Path.home() / ".config/Claude/claude_desktop_config.json",  # Linux
        Path(os.getenv('APPDATA', '')) / "Claude/claude_desktop_config.json",  # Windows
        Path.cwd() / ".claude/config.json",  # Claude Code
    ]

    config_found = False
    for config_path in config_locations:
        if config_path.exists():
            config_found = True
            results.append(check_config_file(config_path))

    if not config_found:
        print("⚠ No configuration files found")
        print("  Create configuration for Claude Desktop or Claude Code")

    # Summary
    print("\n" + "="*50)
    if all(results):
        print("✓ All checks passed!")
        print("Task MCP server is ready to use.")
        return 0
    else:
        print("⚠ Some checks failed")
        print("Please address the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
