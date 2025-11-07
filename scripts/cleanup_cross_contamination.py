#!/usr/bin/env python3
"""
Cross-Contamination Cleanup Script

Soft-deletes cross-contaminated tasks from commission-processing workspace.

Usage:
    # Dry run (preview what would be deleted)
    python cleanup_cross_contamination.py --dry-run

    # Execute cleanup
    python cleanup_cross_contamination.py --execute

    # Verify cleanup results
    python cleanup_cross_contamination.py --verify
"""

import argparse
import hashlib
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def get_workspace_hash(workspace_path: str) -> str:
    """Generate workspace hash (SHA256, truncated to 8 chars)."""
    return hashlib.sha256(workspace_path.encode()).hexdigest()[:8]


def get_database_path(workspace_path: str) -> Path:
    """Get database path for workspace."""
    workspace_hash = get_workspace_hash(workspace_path)
    db_dir = Path.home() / ".task-mcp" / "databases"
    return db_dir / f"project_{workspace_hash}.db"


def connect_to_database(workspace_path: str) -> sqlite3.Connection:
    """Connect to workspace database."""
    db_path = get_database_path(workspace_path)

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def get_cross_contaminated_task_ids() -> list[int]:
    """Return list of cross-contaminated task IDs to delete."""
    task_ids = []

    # Single tasks
    task_ids.append(16)   # Remove workflow-mcp references
    task_ids.append(42)   # Fix subtasks expansion
    task_ids.append(47)   # Validate semantic architecture

    # Task-MCP integration tasks (26-31)
    task_ids.extend(range(26, 32))  # 26, 27, 28, 29, 30, 31

    # Enhancement backlog tasks (48-67)
    task_ids.extend(range(48, 68))  # 48 through 67

    return sorted(task_ids)


def list_tasks(conn: sqlite3.Connection) -> list[dict]:
    """List all non-deleted tasks."""
    cursor = conn.execute("""
        SELECT id, title, status, priority
        FROM tasks
        WHERE deleted_at IS NULL
        ORDER BY id
    """)
    return [dict(row) for row in cursor.fetchall()]


def get_task(conn: sqlite3.Connection, task_id: int) -> dict | None:
    """Get task by ID."""
    cursor = conn.execute("""
        SELECT id, title, status, priority, deleted_at
        FROM tasks
        WHERE id = ?
    """, (task_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def soft_delete_task(conn: sqlite3.Connection, task_id: int) -> bool:
    """Soft delete a task by setting deleted_at timestamp."""
    now = datetime.utcnow().isoformat()

    try:
        cursor = conn.execute("""
            UPDATE tasks
            SET deleted_at = ?
            WHERE id = ? AND deleted_at IS NULL
        """, (now, task_id))
        conn.commit()

        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"❌ Error deleting task {task_id}: {e}")
        return False


def verify_cleanup(conn: sqlite3.Connection, deleted_ids: list[int]) -> dict:
    """Verify cleanup results."""
    results = {
        "total_tasks": 0,
        "deleted_confirmed": 0,
        "still_visible": [],
        "legitimate_tasks": []
    }

    # Get all non-deleted tasks
    all_tasks = list_tasks(conn)
    results["total_tasks"] = len(all_tasks)

    # Check if deleted tasks are still visible
    for task in all_tasks:
        if task["id"] in deleted_ids:
            results["still_visible"].append(task["id"])
        else:
            results["legitimate_tasks"].append(task["id"])

    # Count successfully deleted
    results["deleted_confirmed"] = len(deleted_ids) - len(results["still_visible"])

    return results


def dry_run(workspace_path: str):
    """Preview what would be deleted without making changes."""
    print("=" * 80)
    print("DRY RUN - No changes will be made")
    print("=" * 80)
    print(f"\nWorkspace: {workspace_path}")
    print(f"Database: {get_database_path(workspace_path)}")

    conn = connect_to_database(workspace_path)

    # Get current state
    all_tasks = list_tasks(conn)
    print(f"\nCurrent tasks visible: {len(all_tasks)}")

    # Get cross-contaminated task IDs
    contaminated_ids = get_cross_contaminated_task_ids()
    print(f"\nCross-contaminated task IDs to delete: {len(contaminated_ids)} tasks")
    print(f"IDs: {contaminated_ids}")

    # Check which tasks exist
    print("\n" + "-" * 80)
    print("Tasks that WILL BE DELETED:")
    print("-" * 80)

    found_count = 0
    not_found_count = 0

    for task_id in contaminated_ids:
        task = get_task(conn, task_id)
        if task and task["deleted_at"] is None:
            print(f"  ✓ Task #{task_id}: {task['title']}")
            found_count += 1
        elif task and task["deleted_at"]:
            print(f"  ⊘ Task #{task_id}: Already deleted")
            not_found_count += 1
        else:
            print(f"  ✗ Task #{task_id}: Not found in database")
            not_found_count += 1

    print(f"\nFound: {found_count} tasks")
    print(f"Not found/already deleted: {not_found_count} tasks")

    # Preview legitimate tasks that will remain
    legitimate_ids = [t["id"] for t in all_tasks if t["id"] not in contaminated_ids]
    print("\n" + "-" * 80)
    print("Tasks that WILL REMAIN (legitimate):")
    print("-" * 80)

    for task in all_tasks:
        if task["id"] in legitimate_ids:
            print(f"  ✓ Task #{task['id']}: {task['title']}")

    print(f"\nExpected tasks after cleanup: {len(legitimate_ids)}")
    print("Expected: 15 legitimate tasks (Framework Modernization + vendor tasks)")

    if len(legitimate_ids) == 15:
        print("✅ Count matches expected")
    else:
        print(f"⚠️  Count mismatch: expected 15, will have {len(legitimate_ids)}")

    conn.close()

    print("\n" + "=" * 80)
    print("To execute cleanup, run: python cleanup_cross_contamination.py --execute")
    print("=" * 80)


def execute_cleanup(workspace_path: str):
    """Execute the cleanup operation."""
    print("=" * 80)
    print("EXECUTING CLEANUP")
    print("=" * 80)
    print(f"\nWorkspace: {workspace_path}")
    print(f"Database: {get_database_path(workspace_path)}")

    conn = connect_to_database(workspace_path)

    # Get cross-contaminated task IDs
    contaminated_ids = get_cross_contaminated_task_ids()
    print(f"\nDeleting {len(contaminated_ids)} cross-contaminated tasks...")

    deleted_count = 0
    skipped_count = 0
    errors = []

    for task_id in contaminated_ids:
        task = get_task(conn, task_id)

        if not task:
            print(f"  ⊘ Task #{task_id}: Not found (skipping)")
            skipped_count += 1
            continue

        if task["deleted_at"]:
            print(f"  ⊘ Task #{task_id}: Already deleted (skipping)")
            skipped_count += 1
            continue

        # Soft delete the task
        success = soft_delete_task(conn, task_id)

        if success:
            print(f"  ✓ Task #{task_id}: Deleted - {task['title']}")
            deleted_count += 1
        else:
            print(f"  ✗ Task #{task_id}: Failed to delete")
            errors.append(task_id)

    print("\n" + "-" * 80)
    print("CLEANUP SUMMARY")
    print("-" * 80)
    print(f"Successfully deleted: {deleted_count} tasks")
    print(f"Skipped (not found/already deleted): {skipped_count} tasks")

    if errors:
        print(f"Errors: {len(errors)} tasks")
        print(f"Failed task IDs: {errors}")
    else:
        print("Errors: 0")

    # Verify results
    print("\n" + "-" * 80)
    print("VERIFICATION")
    print("-" * 80)

    verification = verify_cleanup(conn, contaminated_ids)
    print(f"Total tasks now visible: {verification['total_tasks']}")
    print(f"Successfully deleted: {verification['deleted_confirmed']} tasks")

    if verification["still_visible"]:
        print(f"⚠️  Still visible (should be deleted): {verification['still_visible']}")
    else:
        print("✅ All targeted tasks successfully deleted")

    print(f"\nLegitimate tasks remaining: {len(verification['legitimate_tasks'])}")
    print(f"Legitimate task IDs: {verification['legitimate_tasks']}")

    if len(verification['legitimate_tasks']) == 15:
        print("✅ Task count matches expected (15 legitimate tasks)")
    else:
        print(f"⚠️  Expected 15 tasks, found {len(verification['legitimate_tasks'])}")

    conn.close()

    print("\n" + "=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run verification: python cleanup_cross_contamination.py --verify")
    print("2. Test workspace isolation from Claude Code")
    print("3. Verify task-mcp workspace still has all tasks")


def verify_only(workspace_path: str):
    """Verify cleanup results without making changes."""
    print("=" * 80)
    print("VERIFICATION ONLY")
    print("=" * 80)
    print(f"\nWorkspace: {workspace_path}")

    conn = connect_to_database(workspace_path)

    # Get all tasks
    all_tasks = list_tasks(conn)
    contaminated_ids = get_cross_contaminated_task_ids()

    print(f"\nTotal tasks visible: {len(all_tasks)}")
    print("Expected after cleanup: 15 tasks")

    # Check for contaminated tasks
    still_contaminated = [t for t in all_tasks if t["id"] in contaminated_ids]
    legitimate = [t for t in all_tasks if t["id"] not in contaminated_ids]

    if still_contaminated:
        print(f"\n⚠️  CONTAMINATION DETECTED: {len(still_contaminated)} tasks")
        print("\nCross-contaminated tasks still visible:")
        for task in still_contaminated:
            print(f"  - Task #{task['id']}: {task['title']}")
        print("\n❌ Cleanup needed or incomplete")
    else:
        print("\n✅ No cross-contamination detected")

    print(f"\nLegitimate tasks: {len(legitimate)}")
    if legitimate:
        print("\nLegitimate task list:")
        for task in legitimate:
            print(f"  - Task #{task['id']}: {task['title']} [{task['status']}]")

    if len(legitimate) == 15:
        print("\n✅ Task count correct (15 legitimate tasks)")
    else:
        print(f"\n⚠️  Expected 15 tasks, found {len(legitimate)}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Cross-contamination cleanup script for task-mcp"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without making changes"
    )
    group.add_argument(
        "--execute",
        action="store_true",
        help="Execute the cleanup operation"
    )
    group.add_argument(
        "--verify",
        action="store_true",
        help="Verify cleanup results"
    )

    parser.add_argument(
        "--workspace",
        type=str,
        default="/Users/cliffclarke/Claude_Code/commission-processing-vendor-extractors",
        help="Workspace path (default: commission-processing)"
    )

    args = parser.parse_args()

    # Validate workspace path
    workspace_path = Path(args.workspace).resolve()
    if not workspace_path.exists():
        print(f"❌ Workspace path does not exist: {workspace_path}")
        sys.exit(1)

    workspace_str = str(workspace_path)

    # Execute requested operation
    if args.dry_run:
        dry_run(workspace_str)
    elif args.execute:
        # Confirm before executing
        print("⚠️  This will soft-delete 32 cross-contaminated tasks from:")
        print(f"   {workspace_str}")
        print(f"\nDatabase: {get_database_path(workspace_str)}")

        response = input("\nProceed with cleanup? [y/N]: ")
        if response.lower() not in ["y", "yes"]:
            print("Cleanup cancelled")
            sys.exit(0)

        execute_cleanup(workspace_str)
    elif args.verify:
        verify_only(workspace_str)


if __name__ == "__main__":
    main()
