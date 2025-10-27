#!/usr/bin/env python3
"""
Demonstration script for Task MCP utils.py functionality.

This script demonstrates:
1. Workspace resolution priority order
2. Path hashing with 8-character output
3. Database path generation
4. Validation utilities
"""

import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from task_mcp.utils import (
    ensure_absolute_path,
    get_master_db_path,
    get_project_db_path,
    hash_workspace_path,
    resolve_workspace,
    validate_description_length,
)


def print_section(title: str) -> None:
    """Print section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def demo_workspace_resolution() -> None:
    """Demonstrate workspace resolution priority order."""
    print_section("1. Workspace Resolution Priority Order")

    # Save original environment
    original_env = os.environ.get("TASK_MCP_WORKSPACE")

    # Test Priority 3: Current working directory (fallback)
    if "TASK_MCP_WORKSPACE" in os.environ:
        del os.environ["TASK_MCP_WORKSPACE"]
    workspace = resolve_workspace()
    print("\nPriority 3 (CWD fallback):")
    print("  Input: None (no param, no env var)")
    print(f"  Result: {workspace}")
    print(f"  Expected: Current directory - {Path.cwd().resolve()}")
    print(f"  Match: {workspace == str(Path.cwd().resolve())}")

    # Test Priority 2: Environment variable
    test_env_path = "/tmp/test-workspace-env"
    os.environ["TASK_MCP_WORKSPACE"] = test_env_path
    workspace = resolve_workspace()
    print("\nPriority 2 (Environment variable):")
    print(f"  TASK_MCP_WORKSPACE={test_env_path}")
    print("  Input: None (no param)")
    print(f"  Result: {workspace}")
    print(f"  Expected: {Path(test_env_path).resolve()}")
    print(f"  Match: {workspace == str(Path(test_env_path).resolve())}")

    # Test Priority 1: Explicit parameter (overrides environment)
    explicit_path = "/tmp/test-workspace-explicit"
    workspace = resolve_workspace(explicit_path)
    print("\nPriority 1 (Explicit parameter - HIGHEST):")
    print(f"  TASK_MCP_WORKSPACE={test_env_path} (still set)")
    print(f"  Input: workspace_path='{explicit_path}'")
    print(f"  Result: {workspace}")
    print(f"  Expected: {Path(explicit_path).resolve()}")
    print(f"  Match: {workspace == str(Path(explicit_path).resolve())}")
    print("\n  Note: Explicit parameter overrides environment variable!")

    # Restore original environment
    if original_env:
        os.environ["TASK_MCP_WORKSPACE"] = original_env
    elif "TASK_MCP_WORKSPACE" in os.environ:
        del os.environ["TASK_MCP_WORKSPACE"]


def demo_path_hashing() -> None:
    """Demonstrate path hashing functionality."""
    print_section("2. Path Hashing (SHA256 truncated to 8 chars)")

    test_paths = [
        "/home/user/project-alpha",
        "/home/user/project-beta",
        "/Users/dev/workspace/app",
        "/var/www/myapp",
        Path.cwd(),  # Current directory
    ]

    print("\nHash generation (8-character safe filenames):")
    print(f"{'Path':<40} | Hash")
    print("-" * 70)

    for path in test_paths:
        path_str = str(path)
        hash_result = hash_workspace_path(path_str)
        print(f"{path_str:<40} | {hash_result}")

    # Demonstrate consistency
    print("\n\nConsistency check (same path = same hash):")
    test_path = "/home/user/consistent-test"
    hash1 = hash_workspace_path(test_path)
    hash2 = hash_workspace_path(test_path)
    hash3 = hash_workspace_path(test_path)
    print(f"  Path: {test_path}")
    print(f"  Hash 1: {hash1}")
    print(f"  Hash 2: {hash2}")
    print(f"  Hash 3: {hash3}")
    print(f"  All identical: {hash1 == hash2 == hash3}")
    print(f"  Length: {len(hash1)} characters")


def demo_database_paths() -> None:
    """Demonstrate database path generation."""
    print_section("3. Database Path Generation")

    # Master database path
    master_path = get_master_db_path()
    print("\nMaster Database:")
    print(f"  Path: {master_path}")
    print("  Location: ~/.task-mcp/master.db")
    print(f"  Exists: {master_path.exists()}")
    print(f"  Parent dir exists: {master_path.parent.exists()}")

    # Project-specific database paths
    print("\n\nProject Databases (format: ~/.task-mcp/databases/project_{hash}.db):")

    test_workspaces = [
        "/home/user/project-alpha",
        "/home/user/project-beta",
        str(Path.cwd()),
    ]

    for workspace in test_workspaces:
        db_path = get_project_db_path(workspace)
        path_hash = hash_workspace_path(workspace)
        print(f"\n  Workspace: {workspace}")
        print(f"  Hash: {path_hash}")
        print(f"  Database: {db_path}")
        print(f"  Parent exists: {db_path.parent.exists()}")
        print(f"  Expected name: project_{path_hash}.db")
        print(f"  Name matches: {db_path.name == f'project_{path_hash}.db'}")


def demo_validation_utilities() -> None:
    """Demonstrate validation utilities."""
    print_section("4. Validation Utilities")

    # Description length validation
    print("\nDescription Length Validation (max 10,000 chars):")

    test_cases = [
        (None, "None (optional field)"),
        ("Short description", "Short text (17 chars)"),
        ("x" * 9999, "9,999 characters (valid)"),
        ("x" * 10000, "10,000 characters (valid, at limit)"),
        ("x" * 10001, "10,001 characters (INVALID - exceeds limit)"),
    ]

    for description, label in test_cases:
        try:
            validate_description_length(description)
            status = "VALID"
            message = "Passed validation"
        except ValueError as e:
            status = "INVALID"
            message = str(e)

        length = len(description) if description else 0
        print(f"\n  {label}:")
        print(f"    Length: {length:,}")
        print(f"    Status: {status}")
        if status == "INVALID":
            print(f"    Error: {message}")

    # Path validation
    print("\n\nPath Validation (ensure_absolute_path):")

    path_tests = [
        ("/absolute/path", "Absolute path"),
        ("relative/path", "Relative path (converts to absolute)"),
        ("./current/dir", "Current directory relative"),
        ("../parent/dir", "Parent directory relative"),
    ]

    for path_input, label in path_tests:
        try:
            result = ensure_absolute_path(path_input)
            print(f"\n  {label}:")
            print(f"    Input: {path_input}")
            print(f"    Output: {result}")
            print(f"    Is absolute: {Path(result).is_absolute()}")
        except ValueError as e:
            print(f"\n  {label}:")
            print(f"    Input: {path_input}")
            print(f"    Error: {e}")

    # Empty path test
    print("\n  Empty path (should fail):")
    try:
        ensure_absolute_path("")
        print("    ERROR: Should have raised ValueError!")
    except ValueError as e:
        print(f"    Correctly rejected: {e}")


def main() -> None:
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  TASK MCP UTILS.PY DEMONSTRATION")
    print("  Complete workspace detection & path hashing utilities")
    print("=" * 70)

    demo_workspace_resolution()
    demo_path_hashing()
    demo_database_paths()
    demo_validation_utilities()

    print_section("Summary")
    print("""
All utilities demonstrated successfully:

1. Workspace Resolution - 3-tier priority system working correctly
   - Priority 1: Explicit parameter (highest)
   - Priority 2: TASK_MCP_WORKSPACE environment variable
   - Priority 3: Current working directory (fallback)

2. Path Hashing - SHA256 truncated to 8 characters
   - Consistent hashing (same path = same hash)
   - Safe filename generation
   - Sufficient uniqueness for typical usage

3. Database Paths - Automatic directory creation
   - Master: ~/.task-mcp/master.db
   - Projects: ~/.task-mcp/databases/project_{hash}.db
   - Directories created automatically with parents=True, exist_ok=True

4. Validation - Robust error handling
   - Description length limit: 10,000 characters
   - Path validation: Converts to absolute, validates non-empty
   - Clear error messages for constraint violations

Type Safety: All functions use Python 3.9+ union syntax (str | None)
Pathlib: All path operations use Path objects for cross-platform support
""")


if __name__ == "__main__":
    main()
