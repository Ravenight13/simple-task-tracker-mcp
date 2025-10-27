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


def main() -> None:
    """Main entry point for the Task MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
