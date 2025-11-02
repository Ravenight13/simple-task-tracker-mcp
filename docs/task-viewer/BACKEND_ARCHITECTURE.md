# Task Viewer Backend Architecture

**Version:** 1.0
**Date:** November 2, 2025
**Author:** Backend Architecture Planning Subagent
**Purpose:** FastAPI backend for task-mcp web frontend

---

## Overview

This document defines the architecture for a FastAPI backend that wraps the task-mcp MCP server, providing REST API endpoints for a web-based task viewer frontend.

### Architecture Diagram

```
┌─────────────────────┐
│   Web Frontend      │
│   (React/Vue)       │
└──────────┬──────────┘
           │ HTTP REST
           ↓
┌─────────────────────┐
│  FastAPI Backend    │
│  (This System)      │
├─────────────────────┤
│ - REST Endpoints    │
│ - Request Validation│
│ - Error Handling    │
│ - CORS Config       │
└──────────┬──────────┘
           │ FastMCP Client
           ↓
┌─────────────────────┐
│   task-mcp Server   │
│   (MCP Tools)       │
├─────────────────────┤
│ - list_tasks        │
│ - create_task       │
│ - update_task       │
│ - get_task          │
│ - search_tasks      │
│ - list_entities     │
│ - etc.              │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   SQLite Database   │
│   (task-mcp.db)     │
└─────────────────────┘
```

---

## Core Architecture

### 1. FastAPI Application Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration management
├── models/
│   ├── __init__.py
│   ├── requests.py        # Pydantic request models
│   └── responses.py       # Pydantic response models
├── api/
│   ├── __init__.py
│   ├── tasks.py           # Task endpoints
│   ├── entities.py        # Entity endpoints
│   └── projects.py        # Project endpoints
├── services/
│   ├── __init__.py
│   └── mcp_client.py      # FastMCP client wrapper
├── middleware/
│   ├── __init__.py
│   ├── cors.py            # CORS configuration
│   └── error_handler.py   # Global error handling
└── utils/
    ├── __init__.py
    └── logging.py         # Logging configuration
```

---

## FastMCP Client Integration

### Direct FastMCP Import Approach

Since this is a **local-only tool** where both the backend API and task-mcp run on the same machine, we use direct FastMCP instance import for optimal performance. This avoids MCP protocol overhead and provides instant function calls.

#### Connection Strategy

**Chosen Approach: Direct FastMCP Import** (Fastest, Local Only)

```python
# Direct import of task-mcp's FastMCP instance
from mcp import Server

# Initialize at application startup
mcp_server = Server()

# Call tools directly - no protocol overhead
result = await mcp_server.call_tool(tool_name, arguments)
```

**Rationale:**
- Both backend and task-mcp run locally on same machine
- No network latency or protocol overhead
- Instant function calls (microseconds vs milliseconds)
- Simpler architecture for local development
- Full type safety and debugging support

### MCP Client Service Layer

Create a service layer that wraps direct MCP calls with workspace resolution:

```python
# services/mcp_client.py
from mcp import Server
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MCPClientService:
    """
    Wrapper service for direct task-mcp server access.

    This service provides direct function calls to task-mcp tools
    without MCP protocol overhead, since both services run locally.
    """

    def __init__(self):
        """Initialize MCP client service with direct server connection."""
        self.mcp = Server()
        self._initialized = False

    async def initialize(self):
        """Initialize persistent connection (called at app startup)."""
        if not self._initialized:
            try:
                # Initialize the MCP server connection
                await self.mcp.__aenter__()
                self._initialized = True
                logger.info("MCP client service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize MCP client: {e}", exc_info=True)
                raise RuntimeError(f"MCP initialization failed: {str(e)}") from e

    async def close(self):
        """Close persistent connection (called at app shutdown)."""
        if self._initialized:
            try:
                await self.mcp.__aexit__(None, None, None)
                self._initialized = False
                logger.info("MCP client service closed")
            except Exception as e:
                logger.error(f"Error closing MCP client: {e}", exc_info=True)

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any] | None = None
    ) -> Any:
        """
        Call an MCP tool directly and return parsed result.

        Args:
            tool_name: Name of the MCP tool (e.g., "mcp__task-mcp__list_tasks")
            arguments: Dictionary of tool arguments

        Returns:
            Parsed response from the tool

        Raises:
            ValueError: If tool call fails or returns invalid data
            RuntimeError: If connection not initialized
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Direct function call - no protocol overhead
            result = await self.mcp.call_tool(tool_name, arguments or {})
            return result

        except ValueError as e:
            # Tool not found or invalid arguments
            logger.warning(f"Tool call failed: {tool_name} - {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to call MCP tool: {str(e)}") from e

    async def list_tools(self) -> list:
        """List all available MCP tools."""
        if not self._initialized:
            await self.initialize()

        try:
            tools = await self.mcp.list_tools()
            return [{"name": t.name, "description": t.description} for t in tools]
        except Exception as e:
            logger.error(f"Error listing tools: {e}", exc_info=True)
            raise RuntimeError(f"Failed to list MCP tools: {str(e)}") from e


# Singleton instance
mcp_service = MCPClientService()
```

### Workspace Resolution Strategy

Task-mcp tools require a `workspace_path` parameter. We resolve this from `project_id` query parameters:

```python
# services/workspace_resolver.py
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class WorkspaceResolver:
    """
    Resolve workspace_path from project_id or explicit path.

    Maps project IDs to filesystem paths for task-mcp database access.
    """

    def __init__(self):
        """Initialize workspace resolver with empty cache."""
        self._project_cache: Dict[str, str] = {}  # project_id -> workspace_path

    async def initialize(self):
        """Load all projects from master DB on startup."""
        try:
            from services.mcp_client import mcp_service

            # Query task-mcp for all known projects
            projects = await mcp_service.call_tool("mcp__task-mcp__list_projects", {})

            # Build cache: use last path component as project_id
            for project in projects:
                workspace_path = project.get("workspace_path", "")
                if workspace_path:
                    # Use directory name as project_id
                    project_id = os.path.basename(workspace_path.rstrip("/"))
                    self._project_cache[project_id] = workspace_path

            logger.info(f"Loaded {len(self._project_cache)} projects into cache")

        except Exception as e:
            logger.error(f"Failed to initialize workspace resolver: {e}", exc_info=True)
            # Non-fatal: can still use default workspace

    def resolve(
        self,
        project_id: Optional[str] = None,
        workspace_path: Optional[str] = None
    ) -> str:
        """
        Resolve workspace_path from project_id or explicit path.

        Priority:
        1. Explicit workspace_path parameter (highest)
        2. Project ID lookup in cache
        3. Default workspace from environment variable
        4. Raise error if none found

        Args:
            project_id: Short project identifier (directory name)
            workspace_path: Full filesystem path to workspace

        Returns:
            Absolute path to workspace directory

        Raises:
            ValueError: If workspace cannot be resolved
        """
        # Priority 1: Explicit workspace_path
        if workspace_path:
            if os.path.isdir(workspace_path):
                return workspace_path
            raise ValueError(f"Workspace path does not exist: {workspace_path}")

        # Priority 2: Project ID lookup
        if project_id:
            if project_id in self._project_cache:
                return self._project_cache[project_id]
            raise ValueError(f"Project '{project_id}' not found. Available projects: {list(self._project_cache.keys())}")

        # Priority 3: Default workspace
        default = os.getenv("DEFAULT_WORKSPACE_PATH")
        if default and os.path.isdir(default):
            return default

        raise ValueError(
            "No workspace_path or project_id provided. "
            "Please specify project_id query parameter or set DEFAULT_WORKSPACE_PATH"
        )

    def list_projects(self) -> list[dict]:
        """
        List all cached projects.

        Returns:
            List of project info dicts with id and workspace_path
        """
        return [
            {"project_id": pid, "workspace_path": path}
            for pid, path in self._project_cache.items()
        ]


# Singleton instance
workspace_resolver = WorkspaceResolver()
```

---

## API Endpoint Design

### REST API Conventions

**Read-Only API Design** (Phase 1: Viewer Only)

This backend provides **GET-only endpoints** for viewing task data. No create/update/delete operations are exposed via the API.

- **GET** - Retrieve resources (idempotent, cacheable)
- **POST/PUT/PATCH/DELETE** - Not implemented (deferred to Phase 2)

**Rationale:**
- Phase 1 focuses on viewing and browsing tasks
- Task creation/editing happens via Claude Desktop MCP interface
- Simpler security model (no write operations)
- Faster to implement and deploy

### Base URL Structure

```
http://localhost:8001/api/
```

- Port **8001** (avoid conflicts with other local services)
- Path prefix `/api/` (no versioning in v1.0)
- All endpoints are GET-only

---

## Endpoint Specifications

**Phase 1: Read-Only Task Viewer Endpoints**

All endpoints use **GET** method only. Entity endpoints are deferred to Phase 2.

### Task Endpoints

#### 1. List Tasks

```http
GET /api/tasks
```

**Query Parameters:**
- `project_id` (optional): Project identifier (directory name)
- `workspace_path` (optional): Explicit workspace path
- `status` (optional): Filter by status (todo, in_progress, done, blocked)
- `priority` (optional): Filter by priority (low, medium, high)
- `parent_task_id` (optional): Filter by parent task
- `tags` (optional): Space-separated tags for filtering
- `limit` (optional): Maximum results (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Example:**
```
GET /api/tasks?project_id=bmcis-knowledge-mcp&status=todo&priority=high
```

**Response:**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Deploy to Railway",
      "description": "Deploy enhanced MCP server...",
      "status": "todo",
      "priority": "high",
      "parent_task_id": null,
      "depends_on": [],
      "tags": "deployment railway",
      "blocker_reason": null,
      "file_references": [],
      "created_by": "conv-123",
      "created_at": "2025-11-02T10:00:00Z",
      "updated_at": "2025-11-02T10:00:00Z",
      "completed_at": null,
      "deleted_at": null
    }
  ],
  "total": 24,
  "limit": 100,
  "offset": 0
}
```

**MCP Tool:** `mcp__task-mcp__list_tasks`

---

#### 2. Get Task by ID

```http
GET /api/tasks/{task_id}
```

**Path Parameters:**
- `task_id` (required): Task ID

**Query Parameters:**
- `project_id` (optional): Project identifier
- `workspace_path` (optional): Explicit workspace path

**Example:**
```
GET /api/tasks/1?project_id=bmcis-knowledge-mcp
```

**Response:**
```json
{
  "id": 1,
  "title": "Deploy to Railway",
  "description": "Deploy enhanced MCP server...",
  "status": "todo",
  "priority": "high",
  "parent_task_id": null,
  "depends_on": [],
  "tags": "deployment railway",
  "blocker_reason": null,
  "file_references": [],
  "created_by": "conv-123",
  "created_at": "2025-11-02T10:00:00Z",
  "updated_at": "2025-11-02T10:00:00Z",
  "completed_at": null,
  "deleted_at": null
}
```

**MCP Tool:** `mcp__task-mcp__get_task`

---

#### 3. Search Tasks

```http
GET /api/tasks/search
```

**Query Parameters:**
- `q` (required): Search query (searches title and description)
- `project_id` (optional): Project identifier
- `workspace_path` (optional): Explicit workspace path

**Example:**
```
GET /api/tasks/search?q=authentication&project_id=bmcis-knowledge-mcp
```

**Response:**
```json
{
  "tasks": [
    {
      "id": 25,
      "title": "Implement user authentication",
      "description": "Add JWT-based authentication to API",
      ...
    }
  ],
  "total": 5,
  "query": "authentication"
}
```

**MCP Tool:** `mcp__task-mcp__search_tasks`

---

#### 4. Get Task Tree

```http
GET /api/tasks/{task_id}/tree
```

**Path Parameters:**
- `task_id` (required): Root task ID

**Query Parameters:**
- `project_id` (optional): Project identifier
- `workspace_path` (optional): Explicit workspace path

**Example:**
```
GET /api/tasks/1/tree?project_id=bmcis-knowledge-mcp
```

**Response:**
```json
{
  "id": 1,
  "title": "Deploy to Railway",
  "subtasks": [
    {
      "id": 2,
      "title": "Configure environment variables",
      "subtasks": []
    },
    {
      "id": 3,
      "title": "Test deployment",
      "subtasks": []
    }
  ],
  "status": "todo",
  "priority": "high",
  ...
}
```

**MCP Tool:** `mcp__task-mcp__get_task_tree`

---

#### 5. Get Blocked Tasks

```http
GET /api/tasks/blocked
```

**Query Parameters:**
- `project_id` (optional): Project identifier
- `workspace_path` (optional): Explicit workspace path

**Example:**
```
GET /api/tasks/blocked?project_id=bmcis-knowledge-mcp
```

**Response:**
```json
{
  "tasks": [
    {
      "id": 24,
      "title": "Cloudflare Access SSO",
      "status": "blocked",
      "blocker_reason": "Waiting for DNS access to bmcis.net",
      "priority": "high",
      ...
    }
  ],
  "total": 1
}
```

**MCP Tool:** `mcp__task-mcp__get_blocked_tasks`

---

#### 6. Get Next Tasks

```http
GET /api/tasks/next
```

**Query Parameters:**
- `project_id` (optional): Project identifier
- `workspace_path` (optional): Explicit workspace path

**Example:**
```
GET /api/tasks/next?project_id=bmcis-knowledge-mcp
```

**Response:**
```json
{
  "tasks": [
    {
      "id": 20,
      "title": "Deploy to Railway",
      "status": "todo",
      "priority": "high",
      ...
    }
  ],
  "total": 3
}
```

**MCP Tool:** `mcp__task-mcp__get_next_tasks`

---

### Project Endpoints

#### 7. List Projects

```http
GET /api/projects
```

**Example:**
```
GET /api/projects
```

**Response:**
```json
{
  "projects": [
    {
      "project_id": "bmcis-knowledge-mcp",
      "workspace_path": "/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp",
      "friendly_name": "BMCIS Knowledge MCP",
      "last_accessed": "2025-11-02T14:00:00Z",
      "task_count": 24
    }
  ],
  "total": 1
}
```

**MCP Tool:** `mcp__task-mcp__list_projects`

---

#### 8. Get Project Info

```http
GET /api/projects/{project_id}
```

**Path Parameters:**
- `project_id` (required): Project identifier (directory name)

**Example:**
```
GET /api/projects/bmcis-knowledge-mcp
```

**Response:**
```json
{
  "project_id": "bmcis-knowledge-mcp",
  "workspace_path": "/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp",
  "friendly_name": "BMCIS Knowledge MCP",
  "task_counts": {
    "total": 24,
    "todo": 17,
    "in_progress": 0,
    "done": 6,
    "blocked": 1
  },
  "priority_counts": {
    "high": 12,
    "medium": 6,
    "low": 6
  },
  "last_accessed": "2025-11-02T14:00:00Z"
}
```

**MCP Tool:** `mcp__task-mcp__get_project_info`

---

### Entity Endpoints

**Status:** Deferred to Phase 2

Entity management (list, get, create, update, delete, search, links) will be added in Phase 2 when write operations are implemented.

**Rationale:**
- Phase 1 focuses on task viewing only
- Entity relationships add complexity
- Not required for initial task viewer MVP
- Can be added incrementally later

---

## Request/Response Models

### Pydantic Models

**Phase 1: Read-Only Models**

No request models needed for GET-only endpoints. All data validation happens via query parameters.

```python
# models/responses.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TaskResponse(BaseModel):
    """Response model for a single task."""
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    parent_task_id: Optional[int]
    depends_on: Optional[List[int]]
    tags: Optional[str]
    blocker_reason: Optional[str]
    file_references: Optional[List[str]]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    deleted_at: Optional[datetime]


class TaskListResponse(BaseModel):
    """Response model for list of tasks."""
    tasks: List[TaskResponse]
    total: int
    limit: int = 100
    offset: int = 0


class TaskTreeResponse(BaseModel):
    """Response model for task with subtasks (recursive)."""
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    parent_task_id: Optional[int]
    depends_on: Optional[List[int]]
    tags: Optional[str]
    blocker_reason: Optional[str]
    file_references: Optional[List[str]]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    deleted_at: Optional[datetime]
    subtasks: List['TaskTreeResponse'] = []  # Recursive subtasks


class ProjectResponse(BaseModel):
    """Response model for project in list."""
    project_id: str
    workspace_path: str
    friendly_name: Optional[str]
    last_accessed: Optional[datetime]
    task_count: int


class ProjectListResponse(BaseModel):
    """Response model for list of projects."""
    projects: List[ProjectResponse]
    total: int


class ProjectInfoResponse(BaseModel):
    """Response model for detailed project info."""
    project_id: str
    workspace_path: str
    friendly_name: Optional[str]
    task_counts: dict
    priority_counts: dict
    last_accessed: Optional[datetime]


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    mcp_connected: bool
    projects_loaded: int
```

---

## Error Handling Strategy

### Error Response Format

All errors follow a consistent JSON format:

```json
{
  "error": "Resource not found",
  "detail": "Task with id 999 does not exist",
  "status_code": 404
}
```

### HTTP Status Codes

- **200 OK** - Successful GET, PATCH
- **201 Created** - Successful POST
- **204 No Content** - Successful DELETE
- **400 Bad Request** - Invalid input, validation error
- **404 Not Found** - Resource not found
- **409 Conflict** - Duplicate resource, constraint violation
- **422 Unprocessable Entity** - Pydantic validation error
- **500 Internal Server Error** - Server error, MCP connection failure

### Global Exception Handler

```python
# middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    errors = exc.errors()
    logger.warning(f"Validation error: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": errors,
            "status_code": 422
        }
    )


async def runtime_exception_handler(request: Request, exc: RuntimeError):
    """Handle MCP connection and runtime errors."""
    logger.error(f"Runtime error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "status_code": 500
        }
    )


async def value_exception_handler(request: Request, exc: ValueError):
    """Handle value errors (invalid input, not found, etc.)."""
    logger.warning(f"Value error: {exc}")

    # Distinguish between not found and bad request
    error_msg = str(exc)
    if "not found" in error_msg.lower():
        status_code = status.HTTP_404_NOT_FOUND
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_msg,
            "detail": None,
            "status_code": status_code
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected error occurred",
            "detail": str(exc) if logger.level <= logging.DEBUG else None,
            "status_code": 500
        }
    )
```

### Registering Exception Handlers

```python
# main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from middleware.error_handler import (
    validation_exception_handler,
    runtime_exception_handler,
    value_exception_handler,
    generic_exception_handler
)

app = FastAPI()

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RuntimeError, runtime_exception_handler)
app.add_exception_handler(ValueError, value_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

---

## CORS Configuration

### Local Development CORS

```python
# middleware/cors.py
from fastapi.middleware.cors import CORSMiddleware

def configure_cors(app):
    """Configure CORS for local development."""

    # Explicit origin list - no wildcards
    origins = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Alternative port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],  # GET-only API
        allow_headers=["Content-Type", "X-API-Key"],  # Explicit headers only
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
```

**Security Notes:**
- No wildcard origins (`*`)
- GET and OPTIONS only (no POST/PUT/PATCH/DELETE)
- Explicit header list (no `*`)
- Credentials support for API key headers

### Production CORS (Future)

```python
# For production deployment
origins = [
    "https://tasks.bmcis.net",  # Production domain
    "https://www.tasks.bmcis.net",
]
```

---

## Authentication

### API Key Authentication (Day 1)

**Approach:** Simple API key in `X-API-Key` header

```python
# middleware/auth.py
from fastapi import Security, HTTPException, Header
from typing import Optional
import os
import secrets
import hashlib

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Verify API key from X-API-Key header.

    Returns:
        API key if valid

    Raises:
        HTTPException: 401 if key is missing or invalid
    """
    expected_key = os.getenv("API_KEY", "dev-key-local-only")

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header."
        )

    if x_api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return x_api_key


def generate_api_key() -> str:
    """Generate cryptographically secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage (don't store plaintext)."""
    return hashlib.sha256(api_key.encode()).hexdigest()
```

### Applying Authentication

```python
# main.py
from fastapi import Depends
from middleware.auth import verify_api_key

# Protected endpoint
@app.get("/api/tasks", dependencies=[Depends(verify_api_key)])
async def list_tasks():
    """List tasks - requires API key."""
    ...

# Public endpoint (no auth)
@app.get("/health")
async def health_check():
    """Health check - no authentication required."""
    return {"status": "healthy"}
```

### API Key Setup

```bash
# Generate API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
echo "API_KEY=your-generated-key-here" >> .env
```

### Frontend Configuration

```typescript
// Frontend API client
const API_KEY = process.env.VITE_API_KEY;

fetch('http://localhost:8001/api/tasks', {
  headers: {
    'X-API-Key': API_KEY
  }
});
```

**Rationale:**
- Simple to implement (10 lines of code)
- No database or session management
- Works for local development
- Sufficient security for local-only tool
- Can upgrade to OAuth2/JWT later if needed

---

## Performance Considerations

### 1. Connection Pooling

The MCP client creates new connections per request. For better performance:

```python
# services/mcp_client.py
class MCPClientService:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connection_pool_size = 5
        self._semaphore = asyncio.Semaphore(self._connection_pool_size)

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] | None = None):
        async with self._semaphore:  # Limit concurrent connections
            # ... existing implementation
```

### 2. Response Caching

For read-heavy operations, implement caching:

```python
from functools import lru_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

# Initialize cache
FastAPICache.init(InMemoryBackend())

# Cache endpoint responses
@router.get("/tasks")
@cache(expire=60)  # Cache for 60 seconds
async def list_tasks(status: Optional[str] = None):
    # ... implementation
```

### 3. Async Operations

All MCP calls are async - ensure proper async/await usage:

```python
# ✅ Good - Parallel execution
async def get_task_with_entities(task_id: int):
    task_future = mcp_service.call_tool("mcp__task-mcp__get_task", {"task_id": task_id})
    entities_future = mcp_service.call_tool("mcp__task-mcp__get_task_entities", {"task_id": task_id})

    task, entities = await asyncio.gather(task_future, entities_future)
    return {"task": task, "entities": entities}

# ❌ Bad - Sequential execution
async def get_task_with_entities_slow(task_id: int):
    task = await mcp_service.call_tool("mcp__task-mcp__get_task", {"task_id": task_id})
    entities = await mcp_service.call_tool("mcp__task-mcp__get_task_entities", {"task_id": task_id})
    return {"task": task, "entities": entities}
```

### 4. Request Timeout

Set timeouts to prevent hanging requests:

```python
import asyncio

async def call_tool_with_timeout(tool_name: str, arguments: dict, timeout: int = 30):
    try:
        return await asyncio.wait_for(
            mcp_service.call_tool(tool_name, arguments),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        raise RuntimeError(f"Tool {tool_name} timed out after {timeout}s")
```

### 5. Pagination

Implement pagination for large result sets:

```python
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int

def paginate(items: List[Any], page: int, page_size: int) -> PaginatedResponse:
    total = len(items)
    pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size

    return PaginatedResponse(
        items=items[start:end],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )
```

### 6. Database Query Optimization

Since task-mcp uses SQLite, avoid N+1 queries:

- Use `get_task_tree` instead of recursive `get_task` calls
- Use `get_task_entities` instead of individual entity lookups
- Batch operations when possible

---

## Logging Strategy

### Structured Logging

```python
# utils/logging.py
import logging
import sys
from typing import Any, Dict
import json

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        return json.dumps(log_data)


def configure_logging(level: str = "INFO", json_logs: bool = False):
    """Configure application logging."""

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Set formatter
    if json_logs:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=[handler]
    )

    # Set third-party loggers to WARNING
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
```

### Request Logging Middleware

```python
from fastapi import Request
import time
import uuid

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Log request
    logger.info(
        f"Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params)
        }
    )

    # Process request
    response = await call_next(request)

    # Log response
    duration = time.time() - start_time
    logger.info(
        f"Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2)
        }
    )

    return response
```

### Logging Levels

- **DEBUG:** MCP tool calls, argument details, response data
- **INFO:** Request/response, API endpoint hits, cache operations
- **WARNING:** Validation errors, not found errors, deprecated usage
- **ERROR:** MCP connection failures, unhandled exceptions, system errors
- **CRITICAL:** Service unavailable, database connection lost

### What to Log

**Always Log:**
- All incoming requests (method, path, query params)
- All MCP tool calls (tool name, arguments)
- All errors and exceptions
- Response times and status codes

**Never Log:**
- Sensitive data (API keys, tokens, passwords)
- Personal information (unless required for debugging)
- Full database records (log IDs only)

---

## Configuration Management

### Environment Variables

```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application configuration."""

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8001  # Port 8001 to avoid conflicts
    RELOAD: bool = True

    # MCP Connection (direct import - no connection string needed)
    MCP_TIMEOUT: int = 30  # seconds

    # Workspace Resolution
    DEFAULT_WORKSPACE_PATH: Optional[str] = None  # Fallback workspace

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"
    JSON_LOGS: bool = False

    # Authentication
    API_KEY: str = "dev-key-local-only"  # Required from day 1

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

### .env File

```bash
# .env.example
# Server Configuration
HOST=127.0.0.1
PORT=8001
RELOAD=true

# Workspace Configuration
DEFAULT_WORKSPACE_PATH=/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO
JSON_LOGS=false

# Authentication (Required)
API_KEY=your-generated-api-key-here

# Generate a secure API key with:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Main Application Entry Point

```python
# main.py
from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from config import settings
from middleware.cors import configure_cors
from middleware.auth import verify_api_key
from middleware.error_handler import (
    validation_exception_handler,
    runtime_exception_handler,
    value_exception_handler,
    generic_exception_handler
)
from api import tasks, projects
from services.mcp_client import mcp_service
from services.workspace_resolver import workspace_resolver
from utils.logging import configure_logging
import logging

# Configure logging
configure_logging(level=settings.LOG_LEVEL, json_logs=settings.JSON_LOGS)
logger = logging.getLogger(__name__)


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
        await workspace_resolver.initialize()
        logger.info(f"Workspace resolver initialized with {len(workspace_resolver._project_cache)} projects")

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
    lifespan=lifespan
)

# Configure CORS
configure_cors(app)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RuntimeError, runtime_exception_handler)
app.add_exception_handler(ValueError, value_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register routers (all protected by API key)
app.include_router(
    tasks.router,
    prefix="/api/tasks",
    tags=["tasks"],
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    projects.router,
    prefix="/api/projects",
    tags=["projects"],
    dependencies=[Depends(verify_api_key)]
)


# Health check endpoint (no authentication)
@app.get("/health")
async def health_check():
    """
    Health check endpoint with MCP connection status.

    No authentication required.
    """
    try:
        # Check if MCP is initialized
        mcp_healthy = mcp_service._initialized

        # Get project count
        projects_loaded = len(workspace_resolver._project_cache)

        return {
            "status": "healthy" if mcp_healthy else "degraded",
            "version": "1.0.0",
            "mcp_connected": mcp_healthy,
            "projects_loaded": projects_loaded
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "version": "1.0.0",
            "mcp_connected": False,
            "projects_loaded": 0,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
```

---

## Testing Strategy

### Unit Tests

Test individual components in isolation:

```python
# tests/test_mcp_service.py
import pytest
from services.mcp_client import MCPClientService
from fastmcp import FastMCP

@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server for testing."""
    mcp = FastMCP("test-server")

    @mcp.tool()
    async def test_tool(value: int) -> dict:
        return {"result": value * 2}

    return mcp

@pytest.mark.asyncio
async def test_mcp_service_call_tool(mock_mcp_server):
    """Test calling an MCP tool."""
    service = MCPClientService(mock_mcp_server)
    result = await service.call_tool("test_tool", {"value": 5})
    assert result == {"result": 10}
```

### Integration Tests

Test API endpoints with FastAPI TestClient:

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_tasks():
    """Test listing tasks."""
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    assert "tasks" in response.json()
    assert "total" in response.json()

def test_create_task():
    """Test creating a task."""
    task_data = {
        "title": "Test task",
        "description": "Test description",
        "status": "todo",
        "priority": "medium"
    }
    response = client.post("/api/v1/tasks", json=task_data)
    assert response.status_code == 201
    assert response.json()["title"] == "Test task"
```

---

## Dependencies

### requirements.txt

```
# FastAPI Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# FastMCP Client
fastmcp>=0.2.0

# Data Validation
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Environment Variables
python-dotenv>=1.0.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0  # For TestClient

# Development
black>=23.0.0
ruff>=0.1.0
```

---

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Generate API key
python -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))" >> .env

# Set default workspace path
echo "DEFAULT_WORKSPACE_PATH=$(pwd)" >> .env

# Run server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### Docker (Future)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Future Enhancements

### Phase 2 Features

1. **WebSocket Support**
   - Real-time task updates
   - Live collaboration features
   - Push notifications

2. **GraphQL API**
   - Alternative to REST
   - Better for complex queries
   - Reduced over-fetching

3. **Batch Operations**
   - Bulk task creation
   - Bulk status updates
   - Batch deletions

4. **File Upload**
   - Attach files to tasks
   - Upload task lists (CSV/JSON)

5. **Export/Import**
   - Export tasks to CSV/JSON
   - Import from external tools
   - Backup/restore functionality

6. **Advanced Filtering**
   - Complex query builder
   - Saved filters
   - Custom views

7. **Analytics Endpoints**
   - Task completion rates
   - Time tracking
   - Productivity metrics

---

## Security Considerations

### Input Validation

- All inputs validated by Pydantic models
- SQL injection prevented (task-mcp uses parameterized queries)
- Path traversal prevented (workspace path validation)

### Rate Limiting (Future)

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@router.get("/tasks")
@limiter.limit("100/minute")
async def list_tasks(request: Request):
    # ... implementation
```

### HTTPS (Production)

- Use reverse proxy (Nginx, Caddy)
- Automatic HTTPS with Let's Encrypt
- Redirect HTTP to HTTPS

---

## Monitoring & Observability

### Health Check

```python
@app.get("/health")
async def health_check():
    """Health check with dependency checks."""
    try:
        # Test MCP connection
        async with mcp_service.get_client() as client:
            await client.ping()

        return {
            "status": "healthy",
            "version": "1.0.0",
            "mcp_connection": "ok"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "version": "1.0.0",
            "mcp_connection": "error",
            "error": str(e)
        }
```

### Metrics Endpoint (Future)

```python
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter("http_requests_total", "Total HTTP requests")
request_duration = Histogram("http_request_duration_seconds", "HTTP request duration")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")
```

---

## Documentation

### Auto-Generated API Docs

FastAPI automatically generates:

- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **OpenAPI JSON:** http://localhost:8000/api/openapi.json

### Custom Documentation

Add detailed docstrings to all endpoints:

```python
@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """
    Get a single task by ID.

    Args:
        task_id: The unique identifier of the task

    Returns:
        Task object with all fields

    Raises:
        404: Task not found
        500: Server error

    Example:
        GET /api/v1/tasks/1

        Response:
        {
            "id": 1,
            "title": "Deploy to Railway",
            "status": "todo",
            ...
        }
    """
    # ... implementation
```

---

## Summary

**Phase 1: Read-Only Task Viewer Backend**

This backend architecture provides:

1. **Direct MCP Integration** - Fast local function calls (no protocol overhead)
2. **Workspace Resolution** - Automatic project_id → workspace_path mapping
3. **Read-Only API** - GET-only endpoints for viewing tasks
4. **API Key Authentication** - Simple security from day 1
5. **Type Safety** - Pydantic models for response validation
6. **Clean Separation** - Service layer, API layer, models
7. **Error Handling** - Consistent error responses
8. **CORS Support** - Explicit origins, GET-only methods
9. **Lifecycle Management** - Proper startup/shutdown hooks
10. **Documentation** - Auto-generated + custom docs

### Key Design Decisions

1. **Local-Only Tool**: Both backend and task-mcp run on same machine
2. **Direct Import**: No MCP protocol overhead for maximum performance
3. **Read-Only Phase 1**: No create/update/delete operations
4. **No Entity Endpoints**: Deferred to Phase 2
5. **Port 8001**: Avoid conflicts with other services
6. **URL Prefix `/api/`**: No versioning in v1.0
7. **API Key Auth**: Simple but sufficient for local development

### Architecture Strengths

- **Fast**: Microsecond latency for MCP calls (direct import)
- **Simple**: Minimal complexity for Phase 1 viewer
- **Secure**: API key authentication, explicit CORS
- **Maintainable**: Clean separation of concerns
- **Extensible**: Easy to add write operations in Phase 2

The architecture follows FastAPI best practices and provides a solid foundation for the task viewer web frontend.

---

## Next Steps

### Phase 1 Implementation (Read-Only Viewer)

1. **Core Application**
   - [ ] Implement `main.py` with lifespan management
   - [ ] Create `config.py` with Settings
   - [ ] Set up `.env` configuration

2. **Services Layer**
   - [ ] Implement `services/mcp_client.py` (direct import)
   - [ ] Implement `services/workspace_resolver.py`
   - [ ] Add startup/shutdown lifecycle hooks

3. **API Endpoints**
   - [ ] Implement `api/tasks.py` (6 GET endpoints)
   - [ ] Implement `api/projects.py` (2 GET endpoints)
   - [ ] Add workspace resolution to all endpoints

4. **Middleware**
   - [ ] Implement `middleware/auth.py` (API key)
   - [ ] Implement `middleware/cors.py` (explicit config)
   - [ ] Implement `middleware/error_handler.py`

5. **Models**
   - [ ] Create `models/responses.py` (Pydantic)
   - [ ] Add response validation

6. **Testing**
   - [ ] Write unit tests for services
   - [ ] Write integration tests for API
   - [ ] Test with frontend

7. **Documentation**
   - [ ] Verify OpenAPI docs at `/api/docs`
   - [ ] Add endpoint docstrings
   - [ ] Create deployment guide

### Phase 2 (Future - Write Operations)

- Add POST/PATCH/DELETE endpoints for tasks
- Add entity management endpoints
- Add batch operations
- Add WebSocket support for real-time updates

---

**Document Version:** 2.0 (Revised)
**Last Updated:** November 2, 2025
**Status:** REVISED - Architecture Updated Based on Review Feedback
**Changes:**
- Fixed MCP client integration (direct import instead of protocol connection)
- Added workspace resolution strategy
- Removed write operation endpoints (Phase 2)
- Removed entity endpoints (Phase 2)
- Changed port to 8001
- Changed URL prefix to `/api/` (no versioning)
- Added API key authentication from day 1
- Fixed CORS to explicit configuration
- Added proper lifecycle management
