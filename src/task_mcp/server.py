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
def create_task(
    title: str,
    workspace_path: str | None = None,
    description: str | None = None,
    status: str = "todo",
    priority: str = "medium",
    parent_task_id: int | None = None,
    depends_on: list[int] | None = None,
    tags: str | None = None,
    file_references: list[str] | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """
    Create a new task with validation.

    Args:
        title: Task title (required)
        workspace_path: Optional workspace path (auto-detected if not provided)
        description: Task description (max 10k chars)
        status: Task status (default: "todo")
        priority: Priority level (default: "medium")
        parent_task_id: Parent task ID for subtasks
        depends_on: List of task IDs this depends on
        tags: Space-separated tags
        file_references: List of file paths
        created_by: Conversation ID

    Returns:
        Created task object with all fields
    """
    # Import at function level
    import json

    from .database import get_connection
    from .models import TaskCreate
    from .utils import validate_description_length

    # Validate description length
    if description:
        validate_description_length(description)

    # Create TaskCreate model to validate inputs
    task_data = TaskCreate(
        title=title,
        description=description,
        status=status,
        priority=priority,
        parent_task_id=parent_task_id,
        depends_on=json.dumps(depends_on) if depends_on else None,
        tags=tags,
        file_references=json.dumps(file_references) if file_references else None,
        created_by=created_by,
    )

    # Get database connection
    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Insert task
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, status, priority, parent_task_id,
                depends_on, tags, blocker_reason, file_references, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                task_data.title,
                task_data.description,
                task_data.status,
                task_data.priority,
                task_data.parent_task_id,
                task_data.depends_on,
                task_data.tags,
                task_data.blocker_reason,
                task_data.file_references,
                task_data.created_by,
            ),
        )

        task_id = cursor.lastrowid
        conn.commit()

        # Fetch created task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        return dict(row)
    finally:
        conn.close()


@mcp.tool()
def get_task(
    task_id: int,
    workspace_path: str | None = None,
) -> dict[str, Any]:
    """
    Get a single task by ID.

    Args:
        task_id: Task ID to retrieve
        workspace_path: Optional workspace path (auto-detected if not provided)

    Returns:
        Task object with all fields

    Raises:
        ValueError: If task not found or soft-deleted
    """
    from .database import get_connection

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Fetch task excluding soft-deleted
        cursor.execute(
            "SELECT * FROM tasks WHERE id = ? AND deleted_at IS NULL",
            (task_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Task {task_id} not found or has been deleted")

        return dict(row)
    finally:
        conn.close()


@mcp.tool()
def update_task(
    task_id: int,
    workspace_path: str | None = None,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    parent_task_id: int | None = None,
    depends_on: list[int] | None = None,
    tags: str | None = None,
    blocker_reason: str | None = None,
    file_references: list[str] | None = None,
) -> dict[str, Any]:
    """
    Update an existing task with validation.

    Args:
        task_id: Task ID to update (required)
        workspace_path: Optional workspace path (auto-detected if not provided)
        title: Updated task title
        description: Updated task description (max 10k chars)
        status: Updated task status
        priority: Updated priority level
        parent_task_id: Updated parent task ID
        depends_on: Updated list of task IDs this depends on
        tags: Updated space-separated tags
        blocker_reason: Updated blocker reason (required when status='blocked')
        file_references: Updated list of file paths

    Returns:
        Updated task object with all fields

    Raises:
        ValueError: If task not found, validation fails, or invalid status transition
    """
    # Import at function level
    import json
    from datetime import datetime

    from .database import get_connection
    from .models import TaskUpdate, validate_status_transition
    from .utils import validate_description_length

    # Validate description length
    if description is not None:
        validate_description_length(description)

    # Get database connection
    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Fetch current task to validate transitions
        cursor.execute(
            "SELECT * FROM tasks WHERE id = ? AND deleted_at IS NULL",
            (task_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Task {task_id} not found or has been deleted")

        current_task = dict(row)

        # Validate status transition if status is being changed
        if (
            status is not None
            and status != current_task["status"]
            and not validate_status_transition(current_task["status"], status)
        ):
            raise ValueError(
                f"Invalid status transition from '{current_task['status']}' to '{status}'"
            )

        # Create TaskUpdate model to validate inputs
        update_data = TaskUpdate(
            title=title,
            description=description,
            status=status,
            priority=priority,
            parent_task_id=parent_task_id,
            depends_on=json.dumps(depends_on) if depends_on is not None else None,
            tags=tags,
            blocker_reason=blocker_reason,
            file_references=json.dumps(file_references) if file_references is not None else None,
        )

        # Check blocker_reason requirement
        final_status = status if status is not None else current_task["status"]
        final_blocker_reason = blocker_reason if blocker_reason is not None else current_task.get("blocker_reason")

        if final_status == "blocked" and (not final_blocker_reason or not final_blocker_reason.strip()):
            raise ValueError("blocker_reason is required when status is 'blocked'")

        # Check dependencies before allowing status transitions
        if status == "done":
            depends_on_str = update_data.depends_on if update_data.depends_on is not None else current_task.get("depends_on")
            if depends_on_str:
                try:
                    dep_ids: list[int] = json.loads(depends_on_str)
                    # Check if all dependencies are done
                    for dep_id in dep_ids:
                        cursor.execute(
                            "SELECT status FROM tasks WHERE id = ? AND deleted_at IS NULL",
                            (dep_id,),
                        )
                        dep_row = cursor.fetchone()
                        if dep_row and dep_row["status"] != "done":
                            raise ValueError(
                                f"Cannot mark task as done: dependency {dep_id} is not done (status: {dep_row['status']})"
                            )
                except json.JSONDecodeError:
                    pass  # Invalid JSON, ignore dependency check

        # Build UPDATE statement dynamically
        update_fields = []
        update_params: list[str | int | None] = []

        if update_data.title is not None:
            update_fields.append("title = ?")
            update_params.append(update_data.title)

        if update_data.description is not None:
            update_fields.append("description = ?")
            update_params.append(update_data.description)

        if update_data.status is not None:
            update_fields.append("status = ?")
            update_params.append(update_data.status)

        if update_data.priority is not None:
            update_fields.append("priority = ?")
            update_params.append(update_data.priority)

        if update_data.parent_task_id is not None:
            update_fields.append("parent_task_id = ?")
            update_params.append(update_data.parent_task_id)

        if update_data.depends_on is not None:
            update_fields.append("depends_on = ?")
            update_params.append(update_data.depends_on)

        if update_data.tags is not None:
            update_fields.append("tags = ?")
            update_params.append(update_data.tags)

        if update_data.blocker_reason is not None:
            update_fields.append("blocker_reason = ?")
            update_params.append(update_data.blocker_reason)

        if update_data.file_references is not None:
            update_fields.append("file_references = ?")
            update_params.append(update_data.file_references)

        # Always update updated_at
        update_fields.append("updated_at = ?")
        update_params.append(datetime.now().isoformat())

        # Set completed_at when status changes to 'done'
        if update_data.status == "done":
            update_fields.append("completed_at = ?")
            update_params.append(datetime.now().isoformat())

        # Execute update if there are fields to update
        if update_fields:
            update_params.append(task_id)
            query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_params)
            conn.commit()

        # Fetch updated task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        return dict(row)
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
def get_project_info(
    workspace_path: str,
) -> dict[str, Any]:
    """
    Get project metadata and task statistics.

    Args:
        workspace_path: Project workspace path

    Returns:
        Project info with task counts by status and priority
    """
    from .database import get_connection
    from .master import get_master_connection
    from .utils import hash_workspace_path

    # Get project metadata
    project_id = hash_workspace_path(workspace_path)

    master_conn = get_master_connection()
    master_cursor = master_conn.cursor()

    try:
        master_cursor.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        )
        project_row = master_cursor.fetchone()

        if not project_row:
            raise ValueError(f"Project not found: {workspace_path}")

        project_info = dict(project_row)
    finally:
        master_conn.close()

    # Get task statistics
    task_conn = get_connection(workspace_path)
    task_cursor = task_conn.cursor()

    try:
        # Total tasks
        task_cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE deleted_at IS NULL")
        project_info['total_tasks'] = task_cursor.fetchone()['count']

        # By status
        task_cursor.execute("""
            SELECT status, COUNT(*) as count FROM tasks
            WHERE deleted_at IS NULL
            GROUP BY status
        """)
        project_info['by_status'] = {row['status']: row['count'] for row in task_cursor.fetchall()}

        # By priority
        task_cursor.execute("""
            SELECT priority, COUNT(*) as count FROM tasks
            WHERE deleted_at IS NULL
            GROUP BY priority
        """)
        project_info['by_priority'] = {row['priority']: row['count'] for row in task_cursor.fetchall()}

        # Blocked count
        task_cursor.execute("""
            SELECT COUNT(*) as count FROM tasks
            WHERE status = 'blocked' AND deleted_at IS NULL
        """)
        project_info['blocked_count'] = task_cursor.fetchone()['count']

        return project_info
    finally:
        task_conn.close()


@mcp.tool()
def set_project_name(
    workspace_path: str,
    friendly_name: str,
) -> dict[str, Any]:
    """
    Set friendly name for a project.

    Args:
        workspace_path: Project workspace path
        friendly_name: Human-readable project name

    Returns:
        Success confirmation
    """
    from .master import get_master_connection, register_project

    # Ensure project is registered
    project_id = register_project(workspace_path)

    # Update friendly name
    conn = get_master_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE projects
            SET friendly_name = ?
            WHERE id = ?
        """, (friendly_name, project_id))

        conn.commit()

        return {
            "success": True,
            "project_id": project_id,
            "workspace_path": workspace_path,
            "friendly_name": friendly_name,
        }
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


@mcp.tool()
def delete_task(
    task_id: int,
    workspace_path: str | None = None,
    cascade: bool = False,
) -> dict[str, Any]:
    """
    Soft delete a task by setting deleted_at timestamp.

    Args:
        task_id: Task ID to delete
        workspace_path: Optional workspace path
        cascade: If True, also soft-delete all subtasks

    Returns:
        Success confirmation with deleted task count
    """
    from datetime import datetime

    from .database import get_connection

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Check if task exists
        cursor.execute(
            "SELECT id FROM tasks WHERE id = ? AND deleted_at IS NULL",
            (task_id,),
        )
        if not cursor.fetchone():
            raise ValueError(f"Task {task_id} not found or already deleted")

        now = datetime.now().isoformat()
        deleted_count = 0

        # Delete the task
        cursor.execute(
            "UPDATE tasks SET deleted_at = ? WHERE id = ?",
            (now, task_id),
        )
        deleted_count += cursor.rowcount

        # Cascade delete subtasks if requested
        if cascade:
            cursor.execute(
                "UPDATE tasks SET deleted_at = ? WHERE parent_task_id = ? AND deleted_at IS NULL",
                (now, task_id),
            )
            deleted_count += cursor.rowcount

        conn.commit()

        return {
            "success": True,
            "task_id": task_id,
            "deleted_count": deleted_count,
            "cascade": cascade,
        }
    finally:
        conn.close()


@mcp.tool()
def get_blocked_tasks(
    workspace_path: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get all tasks with status='blocked' and their blocker reasons.

    Args:
        workspace_path: Optional workspace path

    Returns:
        List of blocked tasks with blocker_reason field
    """
    from .database import get_connection

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM tasks
            WHERE status = 'blocked' AND deleted_at IS NULL
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


@mcp.tool()
def get_next_tasks(
    workspace_path: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get tasks ready to work on (status='todo', no unresolved dependencies).

    Args:
        workspace_path: Optional workspace path

    Returns:
        List of actionable tasks
    """
    import json

    from .database import get_connection

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Get all todo tasks
        cursor.execute("""
            SELECT * FROM tasks
            WHERE status = 'todo' AND deleted_at IS NULL
            ORDER BY priority DESC, created_at ASC
        """)
        tasks = [dict(row) for row in cursor.fetchall()]

        # Filter out tasks with unresolved dependencies
        actionable = []
        for task in tasks:
            if not task["depends_on"]:
                actionable.append(task)
                continue

            # Check if all dependencies are done
            dep_ids = json.loads(task["depends_on"])
            placeholders = ",".join("?" * len(dep_ids))
            cursor.execute(
                f"""
                SELECT COUNT(*) as count FROM tasks
                WHERE id IN ({placeholders})
                AND status = 'done'
            """,
                dep_ids,
            )

            done_count = cursor.fetchone()["count"]
            if done_count == len(dep_ids):
                actionable.append(task)

        return actionable
    finally:
        conn.close()


@mcp.tool()
def cleanup_deleted_tasks(
    workspace_path: str | None = None,
    days: int = 30,
) -> dict[str, Any]:
    """
    Permanently delete tasks soft-deleted more than N days ago.

    Args:
        workspace_path: Optional workspace path
        days: Number of days to retain (default: 30)

    Returns:
        Count of purged tasks
    """
    from datetime import datetime, timedelta

    from .database import get_connection

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            DELETE FROM tasks
            WHERE deleted_at IS NOT NULL
            AND deleted_at < ?
        """, (cutoff_date,))

        purged_count = cursor.rowcount
        conn.commit()

        return {
            "success": True,
            "purged_count": purged_count,
            "cutoff_days": days,
            "cutoff_date": cutoff_date,
        }
    finally:
        conn.close()


def main() -> None:
    """Main entry point for the Task MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
