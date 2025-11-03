#!/usr/bin/env python3
"""
Cleanup script for removing test projects from master database.

This script identifies and removes test projects created in temporary directories
(like /private/var/folders/) from the master.db database. It can optionally
delete the associated project database files.

Usage:
    python scripts/cleanup_test_projects.py [--dry-run] [--delete-files]

Options:
    --dry-run: Show what would be deleted without actually deleting
    --delete-files: Also delete the project database files (default: keep files)
"""

import argparse
import sqlite3
from pathlib import Path
from datetime import datetime


def get_master_db_path() -> Path:
    """Get path to master database."""
    return Path.home() / ".task-mcp" / "master.db"


def get_project_db_path(project_id: str) -> Path:
    """Get path to project database file."""
    return Path.home() / ".task-mcp" / "databases" / f"project_{project_id}.db"


def identify_test_projects(conn: sqlite3.Connection) -> list[dict]:
    """
    Identify test projects that should be cleaned up.

    Test projects are identified by:
    - Workspace path in /private/var/folders/ or /tmp/
    - Friendly name is "My Friendly Project" or null

    Returns:
        List of project dicts with id, workspace_path, friendly_name
    """
    cursor = conn.execute("""
        SELECT id, workspace_path, friendly_name, created_at, last_accessed
        FROM projects
        WHERE workspace_path LIKE '/private/var/folders/%'
           OR workspace_path LIKE '/tmp/%'
           OR workspace_path LIKE '%/tmp%/%'
        ORDER BY last_accessed DESC
    """)

    projects = []
    for row in cursor:
        projects.append({
            'id': row[0],
            'workspace_path': row[1],
            'friendly_name': row[2],
            'created_at': row[3],
            'last_accessed': row[4]
        })

    return projects


def delete_projects(conn: sqlite3.Connection, project_ids: list[str], delete_files: bool = False) -> tuple[int, int]:
    """
    Delete projects from master database.

    Args:
        conn: Database connection
        project_ids: List of project IDs to delete
        delete_files: If True, also delete project database files

    Returns:
        Tuple of (projects_deleted, files_deleted)
    """
    projects_deleted = 0
    files_deleted = 0

    for project_id in project_ids:
        # Delete from master database
        # First delete tool_usage records (foreign key constraint)
        conn.execute("DELETE FROM tool_usage WHERE workspace_id = ?", (project_id,))

        # Then delete project record
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        projects_deleted += 1

        # Optionally delete project database file
        if delete_files:
            project_db = get_project_db_path(project_id)
            if project_db.exists():
                project_db.unlink()
                files_deleted += 1
                # Also delete WAL and SHM files if they exist
                wal_file = project_db.with_suffix('.db-wal')
                shm_file = project_db.with_suffix('.db-shm')
                if wal_file.exists():
                    wal_file.unlink()
                if shm_file.exists():
                    shm_file.unlink()

    conn.commit()
    return projects_deleted, files_deleted


def main():
    """Main cleanup routine."""
    parser = argparse.ArgumentParser(
        description="Clean up test projects from task-mcp master database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--delete-files",
        action="store_true",
        help="Also delete project database files (default: keep files)"
    )
    args = parser.parse_args()

    # Get master database path
    master_db = get_master_db_path()
    if not master_db.exists():
        print(f"❌ Master database not found at {master_db}")
        return 1

    print(f"🔍 Scanning master database: {master_db}\n")

    # Connect to master database
    conn = sqlite3.connect(str(master_db))
    conn.row_factory = sqlite3.Row

    try:
        # Identify test projects
        test_projects = identify_test_projects(conn)

        if not test_projects:
            print("✅ No test projects found to clean up!")
            return 0

        # Display test projects
        print(f"📋 Found {len(test_projects)} test project(s):\n")

        for i, project in enumerate(test_projects, 1):
            print(f"{i}. ID: {project['id']}")
            print(f"   Path: {project['workspace_path']}")
            print(f"   Name: {project['friendly_name'] or '(unnamed)'}")
            print(f"   Created: {project['created_at']}")
            print(f"   Last accessed: {project['last_accessed']}")

            # Check if database file exists
            project_db = get_project_db_path(project['id'])
            db_exists = "✅" if project_db.exists() else "❌"
            print(f"   Database: {db_exists} {project_db}")
            print()

        # Dry run mode
        if args.dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made")
            print(f"\nWould delete {len(test_projects)} project(s) from master database")
            if args.delete_files:
                file_count = sum(1 for p in test_projects if get_project_db_path(p['id']).exists())
                print(f"Would delete {file_count} project database file(s)")
            return 0

        # Confirm deletion
        print("\n⚠️  WARNING: This will permanently delete these projects!")
        if args.delete_files:
            print("⚠️  Project database files will also be deleted!")

        response = input("\nProceed with deletion? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("❌ Deletion cancelled")
            return 0

        # Perform deletion
        print("\n🗑️  Deleting projects...")
        project_ids = [p['id'] for p in test_projects]
        projects_deleted, files_deleted = delete_projects(conn, project_ids, args.delete_files)

        print(f"\n✅ Deleted {projects_deleted} project(s) from master database")
        if args.delete_files:
            print(f"✅ Deleted {files_deleted} project database file(s)")

        print("\n🎉 Cleanup complete!")
        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    exit(main())
