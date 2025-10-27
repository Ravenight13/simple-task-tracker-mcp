"""FastMCP server for task tracking with SQLite backend."""

from typing import Any

from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Task Tracker")


@mcp.tool()
def list_tasks(
    workspace_path: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    parent_task_id: int | None = None,
    tags: str | None = None,
) -> list[dict[str, Any]]:
    """
    List tasks with optional filters.

    Args:
        workspace_path: Optional workspace path (auto-detected)
        status: Filter by status
        priority: Filter by priority
        parent_task_id: Filter by parent task ID
        tags: Filter by tags (space-separated, partial match)

    Returns:
        List of task objects matching filters
    """
    from .database import get_connection

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Build query with filters
        query = "SELECT * FROM tasks WHERE deleted_at IS NULL"
        params: list[str | int] = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        if parent_task_id is not None:
            query += " AND parent_task_id = ?"
            params.append(parent_task_id)

        if tags:
            # Partial match on tags
            query += " AND tags LIKE ?"
            params.append(f"%{tags}%")

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


@mcp.tool()
def search_tasks(
    search_term: str,
    workspace_path: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search tasks by title or description (full-text).

    Args:
        search_term: Search term to match in title or description
        workspace_path: Optional workspace path

    Returns:
        List of matching tasks
    """
    from .database import get_connection

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        query = """
            SELECT * FROM tasks
            WHERE deleted_at IS NULL
            AND (
                title LIKE ? OR description LIKE ?
            )
            ORDER BY created_at DESC
        """

        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_pattern, search_pattern))
        rows = cursor.fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


@mcp.tool()
def list_projects() -> list[dict[str, Any]]:
    """
    List all known projects from master database.

    Returns:
        List of projects sorted by last_accessed DESC
    """
    from .master import get_master_connection

    conn = get_master_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, workspace_path, friendly_name, created_at, last_accessed
            FROM projects
            ORDER BY last_accessed DESC
        """)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


@mcp.tool()
def get_task_tree(
    task_id: int,
    workspace_path: str | None = None,
) -> dict[str, Any]:
    """
    Get task with all descendant subtasks (recursive).

    Args:
        task_id: Root task ID
        workspace_path: Optional workspace path

    Returns:
        Task object with 'subtasks' field containing nested subtasks
    """
    import sqlite3
    from .database import get_connection

    def fetch_with_subtasks(conn: sqlite3.Connection, tid: int) -> dict[str, Any] | None:
        cursor = conn.cursor()

        # Get the task
        cursor.execute(
            "SELECT * FROM tasks WHERE id = ? AND deleted_at IS NULL",
            (tid,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        task = dict(row)

        # Get subtasks
        cursor.execute(
            "SELECT id FROM tasks WHERE parent_task_id = ? AND deleted_at IS NULL",
            (tid,),
        )
        subtask_ids = [r["id"] for r in cursor.fetchall()]

        # Recursively fetch subtasks
        task["subtasks"] = [
            fetch_with_subtasks(conn, sid) for sid in subtask_ids
        ]

        return task

    conn = get_connection(workspace_path)
    try:
        result = fetch_with_subtasks(conn, task_id)
        if not result:
            raise ValueError(f"Task {task_id} not found")
        return result
    finally:
        conn.close()


def main() -> None:
    """Main entry point for the Task MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
