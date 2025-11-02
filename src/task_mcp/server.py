"""FastMCP server for task tracking with SQLite backend."""

from functools import wraps
from typing import Any

from fastmcp import Context, FastMCP

# Initialize MCP server
mcp = FastMCP("Task Tracker")


def track_usage(func):
    """Decorator to track MCP tool usage."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from .master import get_project_id, record_tool_usage
        from .utils import resolve_workspace

        tool_name = func.__name__
        workspace_path = kwargs.get('workspace_path')
        success = True

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            # Track usage if workspace_path provided
            if workspace_path:
                try:
                    workspace = resolve_workspace(workspace_path)
                    workspace_id = get_project_id(workspace)
                    record_tool_usage(tool_name, workspace_id, success)
                except Exception:
                    # Silently fail - don't break tool execution
                    pass

    return wrapper


@track_usage
@mcp.tool()
def list_tasks(
    workspace_path: str,
    status: str | None = None,
    priority: str | None = None,
    parent_task_id: int | None = None,
    tags: str | None = None,
) -> list[dict[str, Any]]:
    """
    List tasks with optional filters.

    Args:
        workspace_path: REQUIRED workspace path
        status: Filter by status
        priority: Filter by priority
        parent_task_id: Filter by parent task ID
        tags: Filter by tags (space-separated, partial match)

    Returns:
        List of task objects matching filters
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

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


@track_usage
@mcp.tool()
def create_task(
    title: str,
    workspace_path: str,
    ctx: Context | None = None,
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
        workspace_path: REQUIRED workspace path
        ctx: FastMCP context (auto-injected, optional for direct calls)
        description: Task description (max 10k chars)
        status: Task status (default: "todo")
        priority: Priority level (default: "medium")
        parent_task_id: Parent task ID for subtasks
        depends_on: List of task IDs this depends on
        tags: Space-separated tags
        file_references: List of file paths
        created_by: Conversation ID (auto-captured from session if not provided)

    Returns:
        Created task object with all fields
    """
    # Import at function level
    import json
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .models import TaskCreate
    from .utils import get_workspace_metadata, resolve_workspace, validate_description_length

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Auto-capture session ID if created_by not provided and context available
    if created_by is None and ctx is not None:
        created_by = ctx.session_id

    # Capture workspace metadata for audit trail
    workspace_metadata_dict = get_workspace_metadata(workspace_path)
    workspace_metadata_json = json.dumps(workspace_metadata_dict)

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

    # Generate ISO 8601 timestamp for creation
    now = datetime.now().isoformat()

    try:
        # Insert task with explicit timestamps and workspace metadata
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, status, priority, parent_task_id,
                depends_on, tags, blocker_reason, file_references, created_by,
                created_at, updated_at, workspace_metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                now,  # created_at
                now,  # updated_at
                workspace_metadata_json,  # workspace_metadata
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


@track_usage
@mcp.tool()
def get_task(
    task_id: int,
    workspace_path: str,
) -> dict[str, Any]:
    """
    Get a single task by ID.

    Args:
        task_id: Task ID to retrieve
        workspace_path: REQUIRED workspace path

    Returns:
        Task object with all fields

    Raises:
        ValueError: If task not found or soft-deleted
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

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
    workspace_path: str,
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
        workspace_path: REQUIRED workspace path
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
    from .master import register_project
    from .models import TaskUpdate, validate_status_transition
    from .utils import resolve_workspace, validate_description_length

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

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
    workspace_path: str,
) -> list[dict[str, Any]]:
    """
    Search tasks by title or description (full-text).

    Args:
        search_term: Search term to match in title or description
        workspace_path: REQUIRED workspace path

    Returns:
        List of matching tasks
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

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
    from .master import get_master_connection, register_project
    from .utils import hash_workspace_path, resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Get project metadata
    project_id = hash_workspace_path(workspace)

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


@track_usage
@mcp.tool()
def get_usage_stats(
    workspace_path: str,
    days: int = 30,
    tool_name: str | None = None,
) -> dict[str, Any]:
    """
    Get MCP tool usage statistics for analytics.

    Args:
        workspace_path: REQUIRED workspace path
        days: Number of days to include in stats (default: 30)
        tool_name: Optional filter for specific tool (default: all tools)

    Returns:
        Dict with usage statistics:
        - total_calls: Total number of tool calls
        - success_rate: Percentage of successful calls
        - tools: List of tools with call counts and success rates
        - timeline: Daily call counts
        - date_range: Start and end dates
    """
    from datetime import datetime, timedelta
    from .master import get_master_connection, get_project_id
    from .utils import resolve_workspace

    workspace = resolve_workspace(workspace_path)
    workspace_id = get_project_id(workspace)

    conn = get_master_connection()
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Build query with optional tool_name filter
        where_clause = "WHERE workspace_id = ? AND timestamp >= ?"
        params = [workspace_id, start_date.isoformat()]

        if tool_name:
            where_clause += " AND tool_name = ?"
            params.append(tool_name)

        # Get overall stats
        cursor = conn.execute(f"""
            SELECT
                COUNT(*) as total_calls,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls
            FROM tool_usage
            {where_clause}
        """, params)
        row = cursor.fetchone()
        total_calls = row[0] if row else 0
        successful_calls = row[1] if row else 0
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0

        # Get per-tool stats
        cursor = conn.execute(f"""
            SELECT
                tool_name,
                COUNT(*) as calls,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                CAST(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as success_rate
            FROM tool_usage
            {where_clause}
            GROUP BY tool_name
            ORDER BY calls DESC
        """, params)
        tools = [
            {
                "tool_name": row[0],
                "calls": row[1],
                "successful": row[2],
                "success_rate": round(row[3], 2),
            }
            for row in cursor.fetchall()
        ]

        # Get daily timeline
        cursor = conn.execute(f"""
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as calls
            FROM tool_usage
            {where_clause}
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, params)
        timeline = [
            {"date": row[0], "calls": row[1]}
            for row in cursor.fetchall()
        ]

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "success_rate": round(success_rate, 2),
            "tools": tools,
            "timeline": timeline,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "filter": {
                "workspace_id": workspace_id,
                "tool_name": tool_name,
            },
        }
    finally:
        conn.close()


@mcp.tool()
def get_task_tree(
    task_id: int,
    workspace_path: str,
) -> dict[str, Any]:
    """
    Get task with all descendant subtasks (recursive).

    Args:
        task_id: Root task ID
        workspace_path: REQUIRED workspace path

    Returns:
        Task object with 'subtasks' field containing nested subtasks
    """
    import sqlite3

    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

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
    workspace_path: str,
    cascade: bool = False,
) -> dict[str, Any]:
    """
    Soft delete a task by setting deleted_at timestamp.

    Args:
        task_id: Task ID to delete
        workspace_path: REQUIRED workspace path
        cascade: If True, also soft-delete all subtasks

    Returns:
        Success confirmation with deleted task count
    """
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

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
def cleanup_deleted_tasks(
    workspace_path: str,
    days: int = 30,
) -> dict[str, Any]:
    """
    Permanently delete tasks soft-deleted more than N days ago.

    Args:
        workspace_path: REQUIRED workspace path
        days: Number of days to retain (default: 30)

    Returns:
        Count of purged tasks
    """
    from datetime import datetime, timedelta

    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

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


# ============================================================================
# ENTITY SYSTEM TOOLS (v0.3.0)
# ============================================================================


@mcp.tool()
def get_entity(
    entity_id: int,
    workspace_path: str,
) -> dict[str, Any]:
    """
    Get a single entity by ID.

    Args:
        entity_id: Entity ID to retrieve
        workspace_path: REQUIRED workspace path

    Returns:
        Entity object with all fields

    Raises:
        ValueError: If entity not found or soft-deleted
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Fetch entity excluding soft-deleted
        cursor.execute(
            "SELECT * FROM entities WHERE id = ? AND deleted_at IS NULL",
            (entity_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Entity {entity_id} not found or has been deleted")

        return dict(row)
    finally:
        conn.close()


@mcp.tool()
def create_entity(
    entity_type: str,
    name: str,
    workspace_path: str,
    ctx: Context | None = None,
    identifier: str | None = None,
    description: str | None = None,
    metadata: str | dict[Any, Any] | list[Any] | None = None,
    tags: str | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """
    Create a new entity with validation.

    Args:
        entity_type: 'file' or 'other'
        name: Human-readable name (required)
        workspace_path: REQUIRED workspace path
        ctx: FastMCP context (auto-injected, optional for direct calls)
        identifier: Unique identifier (file path, vendor code, etc.)
        description: Optional description (max 10k chars)
        metadata: Generic JSON metadata (dict, list, or JSON string)
        tags: Space-separated tags
        created_by: Conversation ID (auto-captured from MCP context)

    Returns:
        Created entity dict with all fields

    Raises:
        ValueError: If entity with same (entity_type, identifier) already exists
    """
    # Import at function level
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .models import EntityCreate
    from .utils import resolve_workspace, validate_description_length

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Auto-capture session ID if created_by not provided and context available
    if created_by is None and ctx is not None:
        created_by = ctx.session_id

    # Validate description length
    if description:
        validate_description_length(description)

    # Create EntityCreate model to validate inputs
    # Note: EntityCreate model handles metadata conversion via BeforeValidator
    entity_data = EntityCreate(
        entity_type=entity_type,
        name=name,
        identifier=identifier,
        description=description,
        metadata=metadata,  # type: ignore[arg-type]  # Model validator converts dict/list to JSON string
        tags=tags,
        created_by=created_by,
    )

    # Get database connection
    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    # Generate ISO 8601 timestamp for creation
    now = datetime.now().isoformat()

    try:
        # Check for duplicate (entity_type, identifier) if identifier provided
        if entity_data.identifier is not None:
            cursor.execute(
                """
                SELECT id, name FROM entities
                WHERE entity_type = ? AND identifier = ? AND deleted_at IS NULL
                """,
                (entity_data.entity_type, entity_data.identifier)
            )
            existing = cursor.fetchone()

            if existing:
                raise ValueError(
                    f"Entity already exists: {entity_data.entity_type}='{entity_data.identifier}' "
                    f"(id={existing['id']}, name='{existing['name']}')"
                )

        # Insert entity with explicit timestamps
        cursor.execute(
            """
            INSERT INTO entities (
                entity_type, name, identifier, description,
                metadata, tags, created_by,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entity_data.entity_type,
                entity_data.name,
                entity_data.identifier,
                entity_data.description,
                entity_data.metadata,  # Already JSON string from model
                entity_data.tags,      # Already normalized from model
                entity_data.created_by,
                now,  # created_at
                now,  # updated_at
            ),
        )

        entity_id = cursor.lastrowid
        conn.commit()

        # Fetch created entity
        cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()

        return dict(row)
    finally:
        conn.close()


@mcp.tool()
def link_entity_to_task(
    task_id: int,
    entity_id: int,
    workspace_path: str,
    ctx: Context | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """
    Create a link between a task and an entity.

    Args:
        task_id: Task ID to link
        entity_id: Entity ID to link
        workspace_path: REQUIRED workspace path
        ctx: FastMCP context (auto-injected, optional for direct calls)
        created_by: Conversation ID (auto-captured from session if not provided)

    Returns:
        Link dict with link_id, task_id, entity_id, created_at

    Raises:
        ValueError: If task/entity not found, deleted, or link already exists
    """
    import sqlite3
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Auto-capture session ID if created_by not provided and context available
    if created_by is None and ctx is not None:
        created_by = ctx.session_id

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Validate task exists and is not deleted
        cursor.execute(
            "SELECT id FROM tasks WHERE id = ? AND deleted_at IS NULL",
            (task_id,),
        )
        task_row = cursor.fetchone()
        if not task_row:
            raise ValueError(f"Task {task_id} not found or has been deleted")

        # Validate entity exists and is not deleted
        cursor.execute(
            "SELECT id FROM entities WHERE id = ? AND deleted_at IS NULL",
            (entity_id,),
        )
        entity_row = cursor.fetchone()
        if not entity_row:
            raise ValueError(f"Entity {entity_id} not found or has been deleted")

        # Create link with timestamp
        now = datetime.now().isoformat()
        try:
            cursor.execute(
                """
                INSERT INTO task_entity_links (task_id, entity_id, created_by, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (task_id, entity_id, created_by, now),
            )
            link_id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(
                    f"Link already exists between task {task_id} and entity {entity_id}"
                ) from e
            raise

        return {
            "link_id": link_id,
            "task_id": task_id,
            "entity_id": entity_id,
            "created_by": created_by,
            "created_at": now,
        }
    finally:
        conn.close()


@mcp.tool()
def get_task_entities(
    task_id: int,
    workspace_path: str,
) -> list[dict[str, Any]]:
    """
    Get all entities linked to a task.

    Returns entity details with link metadata.

    Args:
        task_id: Task ID to query
        workspace_path: REQUIRED workspace path

    Returns:
        List of dicts with entity + link fields:
        - All entity fields (id, entity_type, name, identifier, etc.)
        - link_created_at: Timestamp when link was created
        - link_created_by: Conversation ID that created link

    Raises:
        ValueError: If task not found or deleted

    Examples:
        # Get all entities linked to task 42
        entities = get_task_entities(task_id=42)

        # Returns:
        [
            {
                "id": 7,
                "entity_type": "file",
                "name": "Login Controller",
                "identifier": "/src/auth/login.py",
                "description": "User authentication controller",
                "metadata": '{"language": "python", "line_count": 250}',
                "tags": "auth backend",
                "created_by": "conv-123",
                "created_at": "2025-10-29T10:00:00",
                "updated_at": "2025-10-29T10:00:00",
                "deleted_at": None,
                "link_created_at": "2025-10-29T10:05:00",
                "link_created_by": "conv-123"
            }
        ]
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Validate task exists and is not deleted
        cursor.execute(
            "SELECT id FROM tasks WHERE id = ? AND deleted_at IS NULL",
            (task_id,)
        )
        task = cursor.fetchone()

        if not task:
            raise ValueError(
                f"Task {task_id} not found or has been deleted"
            )

        # Query entities with JOIN to get link metadata
        # Returns all entity fields plus link creation info
        cursor.execute("""
            SELECT
                e.*,
                l.created_at AS link_created_at,
                l.created_by AS link_created_by
            FROM entities e
            JOIN task_entity_links l ON e.id = l.entity_id
            WHERE l.task_id = ?
              AND e.deleted_at IS NULL
              AND l.deleted_at IS NULL
            ORDER BY l.created_at DESC
        """, (task_id,))

        entities = cursor.fetchall()

        # Convert Row objects to dicts
        return [dict(entity) for entity in entities]

    finally:
        conn.close()


@mcp.tool()
def get_entity_tasks(
    entity_id: int,
    workspace_path: str,
    status: str | None = None,
    priority: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get all tasks linked to an entity (reverse lookup).

    Returns task details with link metadata.

    Args:
        entity_id: Entity ID to query
        workspace_path: REQUIRED workspace path
        status: Optional task status filter (todo, in_progress, done, etc.)
        priority: Optional task priority filter (low, medium, high)

    Returns:
        List of dicts with task + link fields:
        - All task fields (id, title, description, status, etc.)
        - link_created_at: Timestamp when link was created
        - link_created_by: Conversation ID that created link

    Raises:
        ValueError: If entity not found or deleted

    Examples:
        # Get all tasks linked to entity 42
        tasks = get_entity_tasks(entity_id=42)

        # Get only high-priority tasks for entity
        tasks = get_entity_tasks(entity_id=42, priority="high")

        # Get only in-progress tasks for entity
        tasks = get_entity_tasks(entity_id=42, status="in_progress")

        # Returns:
        [
            {
                "id": 15,
                "title": "Integrate ABC Insurance vendor data pipeline",
                "description": "Implement ETL pipeline for ABC Insurance",
                "status": "in_progress",
                "priority": "high",
                "parent_task_id": None,
                "depends_on": None,
                "tags": "vendor integration",
                "blocker_reason": None,
                "file_references": None,
                "created_by": "conv-123",
                "created_at": "2025-10-29T10:00:00",
                "updated_at": "2025-10-29T11:00:00",
                "completed_at": None,
                "deleted_at": None,
                "link_created_at": "2025-10-29T10:05:00",
                "link_created_by": "conv-123"
            }
        ]
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Validate entity exists and is not deleted
        cursor.execute(
            "SELECT id FROM entities WHERE id = ? AND deleted_at IS NULL",
            (entity_id,)
        )
        entity = cursor.fetchone()

        if not entity:
            raise ValueError(
                f"Entity {entity_id} not found or has been deleted"
            )

        # Build query with optional filters
        query = """
            SELECT
                t.*,
                l.created_at AS link_created_at,
                l.created_by AS link_created_by
            FROM tasks t
            JOIN task_entity_links l ON t.id = l.task_id
            WHERE l.entity_id = ?
              AND t.deleted_at IS NULL
              AND l.deleted_at IS NULL
        """
        params: list[int | str] = [entity_id]

        # Add optional status filter
        if status is not None:
            query += " AND t.status = ?"
            params.append(status)

        # Add optional priority filter
        if priority is not None:
            query += " AND t.priority = ?"
            params.append(priority)

        # Order by link creation (most recent first)
        query += " ORDER BY l.created_at DESC"

        cursor.execute(query, params)
        tasks = cursor.fetchall()

        # Convert Row objects to dicts
        return [dict(task) for task in tasks]

    finally:
        conn.close()


@mcp.tool()
def update_entity(
    entity_id: int,
    workspace_path: str,
    ctx: Context | None = None,
    name: str | None = None,
    identifier: str | None = None,
    description: str | None = None,
    metadata: str | dict[Any, Any] | list[Any] | None = None,
    tags: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing entity with partial updates.

    Only provided fields will be updated. Validates identifier uniqueness
    when changing identifiers to prevent duplicates within entity type.

    Args:
        entity_id: Entity ID to update (required)
        workspace_path: REQUIRED workspace path
        ctx: FastMCP context (auto-injected, optional for direct calls)
        name: Updated name (1-500 chars)
        identifier: Updated identifier (max 1000 chars, must be unique per type)
        description: Updated description (max 10,000 chars)
        metadata: Updated metadata (JSON string, dict, or list)
        tags: Updated space-separated tags (normalized to lowercase)

    Returns:
        Updated entity object with all fields

    Raises:
        ValueError: If entity not found, soft-deleted, or identifier conflicts

    Examples:
        >>> # Update entity name
        >>> update_entity(1, workspace_path="/path", name="New Name")

        >>> # Change identifier (validates uniqueness)
        >>> update_entity(1, workspace_path="/path", identifier="/new/path/file.py")

        >>> # Update metadata
        >>> update_entity(1, workspace_path="/path", metadata={"version": "2.0", "status": "active"})
    """
    # Import at function level
    import json
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .models import EntityUpdate
    from .utils import resolve_workspace, validate_description_length

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Auto-capture session ID for updated_by
    updated_by = ctx.session_id if ctx else None

    # Validate description length if provided
    if description is not None:
        validate_description_length(description)

    # Convert metadata to JSON string if dict/list provided
    metadata_json: str | None = None
    if metadata is not None:
        if isinstance(metadata, str):
            metadata_json = metadata
        elif isinstance(metadata, (dict, list)):
            metadata_json = json.dumps(metadata)
        else:
            raise ValueError("metadata must be a JSON string, dict, or list")

    # Create EntityUpdate model to validate inputs
    update_data = EntityUpdate(
        name=name,
        identifier=identifier,
        description=description,
        metadata=metadata_json,
        tags=tags,
        updated_by=updated_by,
    )

    # Get database connection
    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Fetch current entity to validate changes
        cursor.execute(
            "SELECT * FROM entities WHERE id = ? AND deleted_at IS NULL",
            (entity_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Entity {entity_id} not found or has been deleted")

        current_entity = dict(row)

        # Validate identifier uniqueness if changing
        if identifier is not None and identifier != current_entity["identifier"]:
            cursor.execute(
                """
                SELECT id FROM entities
                WHERE entity_type = ? AND identifier = ? AND id != ? AND deleted_at IS NULL
                """,
                (current_entity["entity_type"], identifier, entity_id),
            )
            existing = cursor.fetchone()

            if existing:
                raise ValueError(
                    f"Entity of type '{current_entity['entity_type']}' already exists "
                    f"with identifier: {identifier}"
                )

        # Build UPDATE statement dynamically for provided fields only
        update_fields = []
        update_params: list[str | int | None] = []

        if update_data.name is not None:
            update_fields.append("name = ?")
            update_params.append(update_data.name)

        if update_data.identifier is not None:
            update_fields.append("identifier = ?")
            update_params.append(update_data.identifier)

        if update_data.description is not None:
            update_fields.append("description = ?")
            update_params.append(update_data.description)

        if update_data.metadata is not None:
            update_fields.append("metadata = ?")
            update_params.append(update_data.metadata)

        if update_data.tags is not None:
            update_fields.append("tags = ?")
            update_params.append(update_data.tags)

        # Always update updated_at timestamp
        update_fields.append("updated_at = ?")
        update_params.append(datetime.now().isoformat())

        # Always update updated_by (audit trail)
        update_fields.append("updated_by = ?")
        update_params.append(updated_by)

        # Execute update if there are fields to update
        if update_fields:
            update_params.append(entity_id)
            query = f"UPDATE entities SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_params)
            conn.commit()

        # Fetch and return updated entity
        cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()

        return dict(row)
    finally:
        conn.close()


@mcp.tool()
def delete_entity(
    entity_id: int,
    workspace_path: str,
) -> dict[str, Any]:
    """
    Soft delete an entity by setting deleted_at timestamp.

    Automatically soft-deletes all associated task-entity links
    to maintain referential integrity. When an entity is deleted,
    all links pointing to it become inactive to prevent orphaned
    references.

    Args:
        entity_id: Entity ID to delete
        workspace_path: REQUIRED workspace path

    Returns:
        Success dict with:
        - success: True
        - entity_id: ID of deleted entity
        - deleted_links: Count of links that were soft-deleted

    Raises:
        ValueError: If entity not found or already deleted

    Example:
        >>> delete_entity(entity_id=42, workspace_path="/path")
        {
            "success": True,
            "entity_id": 42,
            "deleted_links": 3
        }
    """
    from datetime import datetime

    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Check if entity exists and is not already deleted
        cursor.execute(
            "SELECT id FROM entities WHERE id = ? AND deleted_at IS NULL",
            (entity_id,),
        )
        entity = cursor.fetchone()

        if not entity:
            raise ValueError(f"Entity {entity_id} not found or already deleted")

        # Generate ISO 8601 timestamp for deletion
        now = datetime.now().isoformat()

        # Soft delete the entity
        cursor.execute(
            "UPDATE entities SET deleted_at = ? WHERE id = ?",
            (now, entity_id),
        )

        # Cascade soft delete all associated links
        # This maintains referential integrity by marking links as inactive
        cursor.execute(
            """UPDATE task_entity_links
               SET deleted_at = ?
               WHERE entity_id = ? AND deleted_at IS NULL""",
            (now, entity_id),
        )
        deleted_links = cursor.rowcount

        conn.commit()

        return {
            "success": True,
            "entity_id": entity_id,
            "deleted_links": deleted_links,
        }
    finally:
        conn.close()


@mcp.tool()
def list_entities(
    workspace_path: str,
    entity_type: str | None = None,
    tags: str | None = None,
) -> list[dict[str, Any]]:
    """
    List entities with optional filters.

    Args:
        workspace_path: REQUIRED workspace path
        entity_type: Filter by entity type ('file' or 'other')
        tags: Filter by tags (space-separated, partial match)

    Returns:
        List of entity dicts matching filters
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Build query with filters
        query = "SELECT * FROM entities WHERE deleted_at IS NULL"
        params: list[str] = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        if tags:
            # Partial match on tags (OR logic for multiple tags)
            tag_list = tags.split()
            if tag_list:
                tag_conditions = []
                for tag in tag_list:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                query += f" AND ({' OR '.join(tag_conditions)})"

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


@mcp.tool()
def search_entities(
    search_term: str,
    workspace_path: str,
    entity_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search entities by partial match on name or identifier.

    Args:
        search_term: Text to search for (case-insensitive)
        workspace_path: REQUIRED workspace path
        entity_type: Optional filter by entity_type

    Returns:
        List of matching entity dicts, ordered by created_at DESC
    """
    from .database import get_connection
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Build query with search pattern and optional entity_type filter
        query = """
            SELECT * FROM entities
            WHERE deleted_at IS NULL
            AND (name LIKE ? OR identifier LIKE ?)
        """
        params: list[str] = []

        search_pattern = f"%{search_term}%"
        params.append(search_pattern)
        params.append(search_pattern)

        # Add optional entity_type filter
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


@mcp.tool()
def audit_workspace_integrity(
    workspace_path: str,
    include_deleted: bool = False,
    check_git_repo: bool = True,
) -> dict[str, Any]:
    """
    Perform comprehensive workspace integrity audit to detect cross-contamination.

    Scans all tasks and entities in the workspace database for signs of
    cross-workspace contamination, including mismatched file references,
    suspicious tags, git repository inconsistencies, and path references
    in descriptions pointing to other projects.

    Args:
        workspace_path: REQUIRED workspace path
        include_deleted: Include soft-deleted tasks/entities in audit (default: False)
        check_git_repo: Validate git repository consistency (default: True)

    Returns:
        Comprehensive audit report with structure:
        - workspace_path: str - Audited workspace path
        - audit_timestamp: str - ISO 8601 timestamp of audit
        - contamination_found: bool - True if any issues detected
        - issues: dict - Categorized contamination issues:
            - file_reference_mismatches: Tasks with file refs outside workspace
            - suspicious_tags: Tags containing other project names
            - git_repo_mismatches: Tasks from different git repositories
            - entity_identifier_mismatches: File entities pointing outside workspace
            - description_path_references: Absolute paths in descriptions
        - statistics: dict - Summary counts:
            - contaminated_tasks: int - Number of contaminated tasks
            - contaminated_entities: int - Number of contaminated entities
        - recommendations: list[str] - Actionable cleanup recommendations

    Raises:
        ValueError: If workspace path invalid or database inaccessible

    Examples:
        >>> # Run basic audit on current workspace
        >>> audit_workspace_integrity()
        {
            "workspace_path": "/Users/user/projects/task-mcp",
            "audit_timestamp": "2025-11-02T10:30:00",
            "contamination_found": False,
            "issues": {...},
            "statistics": {
                "contaminated_tasks": 0,
                "contaminated_entities": 0
            },
            "recommendations": []
        }

        >>> # Run comprehensive audit including deleted items
        >>> audit_workspace_integrity(include_deleted=True)
        {
            "workspace_path": "/Users/user/projects/task-mcp",
            "contamination_found": True,
            "issues": {
                "file_reference_mismatches": [
                    {
                        "task_id": 42,
                        "title": "Fix authentication bug",
                        "file_references": ["/Users/user/other-project/auth.py"],
                        "reason": "File reference outside workspace"
                    }
                ],
                ...
            },
            "statistics": {
                "contaminated_tasks": 3,
                "contaminated_entities": 1
            },
            "recommendations": [
                "Review and update file references in task #42",
                "Consider soft-deleting tasks from other projects"
            ]
        }

    Use Cases:
        - Periodic workspace health checks
        - Post-migration validation
        - Debugging cross-project contamination issues
        - Pre-cleanup analysis before bulk operations
    """
    from .audit import perform_workspace_audit
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Delegate to audit module
    return perform_workspace_audit(
        workspace_path=workspace,
        include_deleted=include_deleted,
        check_git_repo=check_git_repo,
    )


def main() -> None:
    """Main entry point for the Task MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
