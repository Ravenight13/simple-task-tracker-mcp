"""
Task Viewer REST API - FastAPI Backend.

Provides a read-only web interface to task-mcp MCP server for viewing
tasks, projects, and statistics through standard HTTP REST endpoints.

This is Phase 1: Read-only viewer (no create/update/delete operations).
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()

from mcp_client import mcp_service
from models import (
    ErrorResponse,
    HealthCheckResponse,
    ProjectInfoResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectStatsResponse,
    TaskListResponse,
    TaskResponse,
    TaskSearchResponse,
)
from workspace_resolver import workspace_resolver

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# API Key Authentication
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key from X-API-Key header.

    Args:
        x_api_key: API key from request header

    Returns:
        API key if valid

    Raises:
        HTTPException: 401 if key is missing or invalid
    """
    expected_key = os.getenv("API_KEY", "dev-key-local-only")

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header.",
        )

    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return x_api_key


# Application Lifespan Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle (startup and shutdown)."""
    # Startup
    logger.info("Starting Task Viewer API...")

    try:
        # Initialize MCP client
        await mcp_service.initialize()
        logger.info("MCP client initialized")

        # Initialize workspace resolver
        await workspace_resolver.initialize(mcp_service)
        logger.info(
            f"Workspace resolver initialized with {workspace_resolver.get_project_count()} projects"
        )

        yield

    finally:
        # Shutdown
        logger.info("Shutting down Task Viewer API...")
        await mcp_service.close()
        logger.info("MCP client closed")


# Create FastAPI app
app = FastAPI(
    title="Task Viewer API",
    description="Read-only REST API for task-mcp web frontend",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
origins = [
    "http://localhost:8001",  # Same origin
    "http://127.0.0.1:8001",
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],  # GET-only API
    allow_headers=["Content-Type", "X-API-Key"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=3600,
)


# Exception Handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle ValueError (invalid input, not found)."""
    error_msg = str(exc)
    if "not found" in error_msg.lower():
        status_code = 404
    else:
        status_code = 400

    return JSONResponse(
        status_code=status_code,
        content={
            "error": "Bad Request" if status_code == 400 else "Not Found",
            "message": error_msg,
            "status_code": status_code,
        },
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc: RuntimeError):
    """Handle RuntimeError (MCP connection failures)."""
    logger.error(f"Runtime error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "status_code": 500,
        },
    )


# Health Check Endpoint (No Authentication)
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint with MCP connection status.

    No authentication required.
    """
    try:
        mcp_healthy = mcp_service._initialized
        projects_loaded = workspace_resolver.get_project_count()

        return HealthCheckResponse(
            status="healthy" if mcp_healthy else "degraded",
            version="1.0.0",
            mcp_connected=mcp_healthy,
            projects_loaded=projects_loaded,
            timestamp=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return HealthCheckResponse(
            status="unhealthy",
            version="1.0.0",
            mcp_connected=False,
            projects_loaded=0,
            timestamp=datetime.now(),
            error=str(e),
        )


# Project Endpoints
@app.get("/api/projects", response_model=ProjectListResponse, dependencies=[])
async def list_projects(x_api_key: str = Header(None)):
    """
    List all projects from master database.

    Requires API key authentication via X-API-Key header.
    """
    # Verify API key
    await verify_api_key(x_api_key)

    projects = workspace_resolver.list_projects()
    return ProjectListResponse(
        projects=[ProjectResponse(**p) for p in projects], total=len(projects)
    )


@app.get("/api/projects/{project_id}/info", response_model=ProjectInfoResponse)
async def get_project_info(project_id: str, x_api_key: str = Header(None)):
    """
    Get detailed project information including task statistics.

    Args:
        project_id: Project hash ID (e.g., "1e7be4ae")

    Requires API key authentication.
    """
    # Verify API key
    await verify_api_key(x_api_key)

    # Get project data
    project_data = workspace_resolver.get_project_by_id(project_id)
    if not project_data:
        raise ValueError(f"Project with ID '{project_id}' not found")

    # Get workspace path
    workspace_path = workspace_resolver.resolve(project_id=project_id)

    # Call task-mcp to get project stats
    try:
        stats_result = await mcp_service.call_tool(
            "get_project_info", {"workspace_path": workspace_path}
        )

        # Extract stats from result
        stats = ProjectStatsResponse(
            total_tasks=stats_result.get("total_tasks", 0),
            by_status=stats_result.get("by_status", {}),
            by_priority=stats_result.get("by_priority", {}),
        )

        return ProjectInfoResponse(
            project=ProjectResponse(**project_data), stats=stats
        )

    except Exception as e:
        logger.error(f"Failed to get project stats: {e}", exc_info=True)
        # Return project without stats on error
        return ProjectInfoResponse(
            project=ProjectResponse(**project_data),
            stats=ProjectStatsResponse(
                total_tasks=0, by_status={}, by_priority={}
            ),
        )


# Task Endpoints
# IMPORTANT: Specific routes (search, next, blocked) must come BEFORE /{task_id}
# to avoid path matching issues

@app.get("/api/tasks/search", response_model=TaskSearchResponse)
async def search_tasks(
    q: str,
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search tasks by title or description (full-text search).

    Query Parameters:
        - q: Search query (required)
        - project_id: Filter by project
        - limit: Max results (default: 20, max: 100)

    Requires API key authentication.
    """
    # Verify API key
    await verify_api_key(x_api_key)

    if not q:
        raise ValueError("Search query 'q' is required")

    # Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)

    # Call task-mcp
    tasks_data = await mcp_service.call_tool(
        "search_tasks", {"search_term": q, "workspace_path": resolved_workspace}
    )

    # Apply limit
    limited_tasks = tasks_data[:limit]

    return TaskSearchResponse(
        tasks=[TaskResponse(**t) for t in limited_tasks],
        total=len(tasks_data),
        query=q,
        limit=limit,
    )


@app.get("/api/tasks/next", response_model=TaskListResponse)
async def get_next_tasks(
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get actionable tasks (status='todo', no unresolved dependencies).

    Query Parameters:
        - project_id: Filter by project
        - limit: Max results (default: 10, max: 50)

    Requires API key authentication.
    """
    # Verify API key
    await verify_api_key(x_api_key)

    # Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)

    # Call task-mcp
    tasks_data = await mcp_service.call_tool(
        "get_next_tasks", {"workspace_path": resolved_workspace}
    )

    # Apply limit
    limited_tasks = tasks_data[:limit]

    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in limited_tasks],
        total=len(tasks_data),
        limit=limit,
        offset=0,
    )


@app.get("/api/tasks/blocked", response_model=TaskListResponse)
async def get_blocked_tasks(
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
):
    """
    Get all blocked tasks with blocker reasons.

    Query Parameters:
        - project_id: Filter by project

    Requires API key authentication.
    """
    # Verify API key
    await verify_api_key(x_api_key)

    # Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)

    # Call task-mcp
    tasks_data = await mcp_service.call_tool(
        "get_blocked_tasks", {"workspace_path": resolved_workspace}
    )

    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in tasks_data],
        total=len(tasks_data),
        limit=len(tasks_data),
        offset=0,
    )


@app.get("/api/tasks", response_model=TaskListResponse)
async def list_tasks(
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    parent_task_id: Optional[int] = None,
    tags: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List tasks with optional filtering.

    Query Parameters:
        - project_id: Filter by project hash ID
        - status: Filter by status (todo, in_progress, done, blocked)
        - priority: Filter by priority (low, medium, high)
        - parent_task_id: Filter by parent task
        - tags: Filter by tags (space-separated)
        - limit: Max results per page (default: 50, max: 100)
        - offset: Pagination offset (default: 0)

    Requires API key authentication.
    """
    # Verify API key
    await verify_api_key(x_api_key)

    # Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)

    # Build arguments for MCP call
    args: dict[str, Any] = {"workspace_path": resolved_workspace}
    if status:
        args["status"] = status
    if priority:
        args["priority"] = priority
    if parent_task_id is not None:
        args["parent_task_id"] = parent_task_id
    if tags:
        args["tags"] = tags

    # Call task-mcp
    tasks_data = await mcp_service.call_tool("list_tasks", args)

    # Add blocker detection logic
    # Build a map of which tasks are blocked by which tasks
    blocker_map = {}  # task_id -> [list of task_ids it blocks]

    for task in tasks_data:
        task_id = task.get("id")
        depends_on = task.get("depends_on")

        # Parse depends_on (could be JSON string or list)
        if depends_on:
            try:
                if isinstance(depends_on, str):
                    dep_list = json.loads(depends_on)
                else:
                    dep_list = depends_on

                # For each dependency, mark it as a blocker
                for dep_id in dep_list:
                    if dep_id not in blocker_map:
                        blocker_map[dep_id] = []
                    blocker_map[dep_id].append(task_id)
            except (json.JSONDecodeError, TypeError):
                pass

    # Enhance tasks with blocker metadata
    for task in tasks_data:
        task_id = task.get("id")
        if task_id in blocker_map:
            task["is_blocker"] = True
            task["blocks_task_ids"] = blocker_map[task_id]
        else:
            task["is_blocker"] = False
            task["blocks_task_ids"] = []

    # Apply pagination
    total = len(tasks_data)
    paginated_tasks = tasks_data[offset : offset + limit]

    # Build filter info
    filters = {}
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority

    # Build meta counts
    meta = {
        "status_counts": {},
        "priority_counts": {},
    }

    # Count by status
    for task in tasks_data:
        task_status = task.get("status", "unknown")
        meta["status_counts"][task_status] = (
            meta["status_counts"].get(task_status, 0) + 1
        )

        task_priority = task.get("priority", "unknown")
        meta["priority_counts"][task_priority] = (
            meta["priority_counts"].get(task_priority, 0) + 1
        )

    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in paginated_tasks],
        total=total,
        limit=limit,
        offset=offset,
        filters=filters if filters else None,
        meta=meta,
    )


@app.get("/api/tasks/{task_id}/tree", response_model=TaskResponse)
async def get_task_tree(
    task_id: int,
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
):
    """
    Get a task with all descendant subtasks (recursive tree).

    Args:
        task_id: Root task ID
        project_id: Optional project hint for workspace resolution

    Returns:
        Task object with 'subtasks' field containing nested subtasks

    Requires API key authentication.
    """
    # Verify API key
    await verify_api_key(x_api_key)

    # Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)

    # Call task-mcp
    task_tree = await mcp_service.call_tool(
        "get_task_tree", {"task_id": task_id, "workspace_path": resolved_workspace}
    )

    if not task_tree:
        raise ValueError(f"Task with ID {task_id} not found or deleted")

    return TaskResponse(**task_tree)


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
):
    """
    Get a single task by ID.

    Args:
        task_id: Task ID
        project_id: Optional project hint for workspace resolution

    Requires API key authentication.
    """
    # Verify API key
    await verify_api_key(x_api_key)

    # Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)

    # Call task-mcp
    task_data = await mcp_service.call_tool(
        "get_task", {"task_id": task_id, "workspace_path": resolved_workspace}
    )

    if not task_data:
        raise ValueError(f"Task with ID {task_id} not found or deleted")

    return TaskResponse(**task_data)


# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the task viewer frontend HTML."""
    return FileResponse("static/index.html")


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8001")),
        reload=True,
        log_level="info",
    )
