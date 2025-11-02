# Task Viewer REST API Specification

**Version:** 1.0.0
**Backend:** FastAPI wrapping task-mcp MCP tools
**Frontend:** HTML/Tailwind/Alpine.js
**Response Format:** JSON
**Authentication:** API Key (X-API-Key header)

---

## Table of Contents

1. [Overview](#overview)
2. [v1.0 Scope](#v10-scope)
3. [Authentication](#authentication)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Endpoints](#endpoints)
   - [Health Check](#health-check)
   - [Projects](#projects)
   - [Tasks](#tasks)
7. [Data Models](#data-models)
8. [Examples](#examples)

---

## Overview

This REST API provides a web interface to the task-mcp MCP server, enabling browser-based task management through a simple HTTP interface.

**Base URL:** `http://localhost:8001` (development)
**Production URL:** TBD (Railway deployment)

**Design Principles:**
- RESTful resource-based URLs
- Consistent JSON response format
- Proper HTTP status codes
- Pagination for large result sets
- Rich filtering capabilities
- Sub-500ms response time target

---

## v1.0 Scope

**This is a READ-ONLY viewer for v1.0.** The API provides task visibility but does NOT support task creation, editing, or deletion through the web interface.

**Included in v1.0:**
- ✅ View all projects
- ✅ View project statistics
- ✅ List and filter tasks
- ✅ Search tasks (full-text)
- ✅ View task details
- ✅ Find next actionable tasks
- ✅ Find blocked tasks

**Deferred to v1.1+ (Future):**
- ❌ Task creation (POST /api/tasks)
- ❌ Task updates (PATCH /api/tasks/:id)
- ❌ Task deletion (DELETE /api/tasks/:id)
- ❌ Entity management endpoints
- ❌ Project name updates
- ❌ Task tree/hierarchy endpoints

**Rationale:** Users will continue using Claude Desktop for task management. The web viewer provides visibility and filtering, not full CRUD capabilities.

---

## Authentication

All API endpoints (except `/health`) require API key authentication via the `X-API-Key` header.

```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:8001/api/projects
```

**Missing/Invalid API Key Response:**
```json
{
  "error": "Unauthorized",
  "message": "Missing or invalid API key",
  "status_code": 401
}
```

---

## Error Handling

All errors follow a consistent JSON format:

```json
{
  "error": "Error Type",
  "message": "Human-readable error description",
  "status_code": 400,
  "details": {
    "field": "Additional context (optional)"
  }
}
```

**Standard HTTP Status Codes:**
- `200 OK` - Successful request
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Missing/invalid API key
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - MCP server unavailable

---

## Rate Limiting

**Current Limits:**
- 100 requests per minute per API key
- 1000 requests per hour per API key

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699123456
```

**Rate Limit Exceeded Response (429):**
```json
{
  "error": "Rate Limit Exceeded",
  "message": "Too many requests. Please retry after 60 seconds.",
  "status_code": 429,
  "retry_after": 60
}
```

---

## Endpoints

### Health Check

#### GET /health

Health check endpoint (no authentication required).

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "mcp_connected": true,
  "timestamp": "2025-11-02T10:30:00Z"
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "version": "1.0.0",
  "mcp_connected": false,
  "error": "MCP server connection failed",
  "timestamp": "2025-11-02T10:30:00Z"
}
```

**Example:**
```bash
curl http://localhost:8001/health
```

---

### Projects

#### GET /api/projects

List all projects from the master database.

**Query Parameters:** None

**Response (200 OK):**
```json
{
  "projects": [
    {
      "id": "1e7be4ae",
      "workspace_path": "/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp",
      "friendly_name": "BMCIS Knowledge MCP - Production Deployment",
      "created_at": "2025-11-01T18:33:44.130713",
      "last_accessed": "2025-11-02T07:07:06.292393"
    },
    {
      "id": "7f0198f7",
      "workspace_path": "/Users/cliffclarke/Claude_Code/task-mcp",
      "friendly_name": null,
      "created_at": "2025-11-01T11:44:51.725883",
      "last_accessed": "2025-11-02T07:13:28.250050"
    }
  ],
  "total": 2
}
```

**Response (500 Internal Server Error):**
```json
{
  "error": "Internal Server Error",
  "message": "Failed to retrieve projects from MCP server",
  "status_code": 500,
  "details": {
    "mcp_error": "Connection timeout"
  }
}
```

**Example:**
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8001/api/projects
```

---

#### GET /api/projects/{id}/info

Get detailed project information including task statistics.

**Path Parameters:**
- `id` (string, required) - Project hash ID from `/api/projects` (e.g., "1e7be4ae")

**Response (200 OK):**
```json
{
  "project": {
    "id": "1e7be4ae",
    "workspace_path": "/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp",
    "friendly_name": "BMCIS Knowledge MCP - Production Deployment",
    "created_at": "2025-11-01T18:33:44.130713",
    "last_accessed": "2025-11-02T07:07:06.292393"
  },
  "stats": {
    "total_tasks": 23,
    "by_status": {
      "todo": 16,
      "in_progress": 2,
      "done": 5,
      "blocked": 0
    },
    "by_priority": {
      "high": 8,
      "medium": 10,
      "low": 5
    }
  }
}
```

**Response (404 Not Found):**
```json
{
  "error": "Not Found",
  "message": "Project with ID '1e7be4ae' not found",
  "status_code": 404
}
```

**Example:**
```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8001/api/projects/1e7be4ae/info
```

**Backend Implementation Note:**
- API accepts project hash ID in URL
- Backend maps hash ID to workspace_path
- Calls task-mcp with workspace_path parameter

---

### Tasks

#### GET /api/tasks

List tasks with optional filtering.

**Query Parameters:**
- `project_id` (string, optional) - Filter by project hash ID (e.g., "1e7be4ae")
- `status` (string, optional) - Filter by status: `todo`, `in_progress`, `done`, `blocked`
- `priority` (string, optional) - Filter by priority: `low`, `medium`, `high`
- `parent_task_id` (integer, optional) - Filter by parent task (for subtasks)
- `tags` (string, optional) - Filter by tags (space-separated, partial match)
- `limit` (integer, optional) - Max results per page (default: 50, max: 100)
- `offset` (integer, optional) - Pagination offset (default: 0)

**Response (200 OK):**
```json
{
  "tasks": [
    {
      "id": 23,
      "title": "Roll out BMCIS Knowledge MCP to all 27 team members",
      "description": "Deploy to entire BMCIS sales team (27 users) after successful pilot...",
      "status": "todo",
      "priority": "medium",
      "parent_task_id": null,
      "depends_on": "[22]",
      "tags": "deployment team-rollout production adoption",
      "blocker_reason": null,
      "file_references": "[\"docs/API_KEY_SETUP.md\"]",
      "created_by": "cd5af0c5-6572-4205-9dfb-2fff942c9c41",
      "created_at": "2025-11-02T07:06:15.051308",
      "updated_at": "2025-11-02T07:06:15.051308",
      "completed_at": null,
      "deleted_at": null
    }
  ],
  "total": 24,
  "limit": 50,
  "offset": 0,
  "filters": {
    "status": "todo",
    "priority": "medium"
  },
  "meta": {
    "status_counts": {
      "todo": 16,
      "in_progress": 2,
      "done": 5,
      "blocked": 1
    },
    "priority_counts": {
      "high": 8,
      "medium": 10,
      "low": 6
    }
  }
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Bad Request",
  "message": "Invalid status value",
  "status_code": 400,
  "details": {
    "status": "invalid_status",
    "valid_values": ["todo", "in_progress", "done", "blocked"]
  }
}
```

**Examples:**

```bash
# Get all tasks for a project
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8001/api/tasks?project_id=1e7be4ae"

# Get high-priority tasks that are in progress
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8001/api/tasks?project_id=1e7be4ae&status=in_progress&priority=high"

# Get tasks tagged with "deployment"
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8001/api/tasks?project_id=1e7be4ae&tags=deployment"

# Pagination
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8001/api/tasks?project_id=1e7be4ae&limit=10&offset=20"
```

**Backend Implementation Note:**
- API accepts project_id (hash ID)
- Backend maps to workspace_path before calling task-mcp
- Meta counts help frontend display filter badges with counts

---

#### GET /api/tasks/{id}

Get a single task by ID with full details.

**Path Parameters:**
- `id` (integer, required) - Task ID

**Query Parameters:**
- `project_id` (string, optional) - Project hash ID (helps backend locate correct workspace)

**Response (200 OK):**
```json
{
  "task": {
    "id": 20,
    "title": "Deploy enhanced MCP server to Railway with API key auth",
    "description": "Deploy the merged search enhancements to Railway production...",
    "status": "todo",
    "priority": "high",
    "parent_task_id": null,
    "depends_on": null,
    "tags": "deployment railway security api-key production",
    "blocker_reason": null,
    "file_references": "[\"docs/API_KEY_SETUP.md\", \"docs/SECURITY_SUMMARY.md\"]",
    "created_by": "cd5af0c5-6572-4205-9dfb-2fff942c9c41",
    "created_at": "2025-11-02T07:05:29.807105",
    "updated_at": "2025-11-02T07:05:29.807105",
    "completed_at": null,
    "deleted_at": null
  }
}
```

**Response (404 Not Found):**
```json
{
  "error": "Not Found",
  "message": "Task with ID 20 not found or deleted",
  "status_code": 404
}
```

**Example:**
```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8001/api/tasks/20
```

---

#### GET /api/tasks/search

Search tasks by title or description (full-text search).

**Query Parameters:**
- `q` (string, required) - Search query
- `project_id` (string, optional) - Filter by project hash ID
- `limit` (integer, optional) - Max results (default: 20, max: 100)

**Response (200 OK):**
```json
{
  "tasks": [
    {
      "id": 20,
      "title": "Deploy enhanced MCP server to Railway with API key auth",
      "description": "Deploy the merged search enhancements to Railway production...",
      "status": "todo",
      "priority": "high",
      "parent_task_id": null,
      "depends_on": null,
      "tags": "deployment railway security api-key production",
      "blocker_reason": null,
      "file_references": "[\"docs/API_KEY_SETUP.md\", \"docs/SECURITY_SUMMARY.md\"]",
      "created_by": "cd5af0c5-6572-4205-9dfb-2fff942c9c41",
      "created_at": "2025-11-02T07:05:29.807105",
      "updated_at": "2025-11-02T07:05:29.807105",
      "completed_at": null,
      "deleted_at": null,
      "relevance_score": 0.92
    }
  ],
  "total": 1,
  "query": "Railway deployment",
  "limit": 20
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Bad Request",
  "message": "Search query 'q' is required",
  "status_code": 400
}
```

**Examples:**

```bash
# Search all tasks
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8001/api/tasks/search?q=Railway+deployment"

# Search within specific project
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8001/api/tasks/search?q=testing&project_id=1e7be4ae"

# Limit results
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8001/api/tasks/search?q=API&limit=5"
```

---

#### GET /api/tasks/next

Get actionable tasks (status='todo', no unresolved dependencies).

**Query Parameters:**
- `project_id` (string, optional) - Filter by project hash ID
- `limit` (integer, optional) - Max results (default: 10, max: 50)

**Response (200 OK):**
```json
{
  "tasks": [
    {
      "id": 20,
      "title": "Deploy enhanced MCP server to Railway with API key auth",
      "description": "Deploy the merged search enhancements to Railway production...",
      "status": "todo",
      "priority": "high",
      "parent_task_id": null,
      "depends_on": null,
      "tags": "deployment railway security api-key production",
      "blocker_reason": null,
      "file_references": "[\"docs/API_KEY_SETUP.md\", \"docs/SECURITY_SUMMARY.md\"]",
      "created_by": "cd5af0c5-6572-4205-9dfb-2fff942c9c41",
      "created_at": "2025-11-02T07:05:29.807105",
      "updated_at": "2025-11-02T07:05:29.807105",
      "completed_at": null,
      "deleted_at": null
    }
  ],
  "total": 1,
  "message": "Tasks ready to work on (no unresolved dependencies)"
}
```

**Example:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8001/api/tasks/next?project_id=1e7be4ae"
```

---

#### GET /api/tasks/blocked

Get all blocked tasks with blocker reasons.

**Query Parameters:**
- `project_id` (string, optional) - Filter by project hash ID

**Response (200 OK):**
```json
{
  "tasks": [
    {
      "id": 15,
      "title": "Configure custom domain",
      "description": "Set up knowledge.bmcis.net domain...",
      "status": "blocked",
      "priority": "medium",
      "blocker_reason": "Waiting for DNS access from IT department (estimated 2-3 days)",
      "parent_task_id": null,
      "depends_on": null,
      "tags": "infrastructure dns",
      "file_references": null,
      "created_by": "cd5af0c5-6572-4205-9dfb-2fff942c9c41",
      "created_at": "2025-11-01T10:00:00.000000",
      "updated_at": "2025-11-01T14:30:00.000000",
      "completed_at": null,
      "deleted_at": null
    }
  ],
  "total": 1,
  "message": "Tasks currently blocked"
}
```

**Example:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8001/api/tasks/blocked?project_id=1e7be4ae"
```

---

## Data Models

### Project

```typescript
{
  id: string;                // Project hash ID (e.g., "1e7be4ae")
  workspace_path: string;    // Absolute filesystem path
  friendly_name: string | null;  // Human-readable name
  created_at: string;        // ISO 8601 timestamp
  last_accessed: string;     // ISO 8601 timestamp
}
```

### Task

```typescript
{
  id: number;                      // Unique task ID
  title: string;                   // Task title (1-500 chars)
  description: string | null;      // Task description (max 10k chars)
  status: "todo" | "in_progress" | "done" | "blocked";
  priority: "low" | "medium" | "high";
  parent_task_id: number | null;   // Parent task for subtasks
  depends_on: string | null;       // JSON array of task IDs
  tags: string | null;             // Space-separated tags
  blocker_reason: string | null;   // Required when status='blocked'
  file_references: string | null;  // JSON array of file paths
  created_by: string;              // Conversation ID
  created_at: string;              // ISO 8601 timestamp
  updated_at: string;              // ISO 8601 timestamp
  completed_at: string | null;     // ISO 8601 timestamp
  deleted_at: string | null;       // ISO 8601 timestamp (soft delete)
  relevance_score?: number;        // Only in search results (0.0-1.0)
}
```

### Project Stats

```typescript
{
  total_tasks: number;
  by_status: {
    todo: number;
    in_progress: number;
    done: number;
    blocked: number;
  };
  by_priority: {
    high: number;
    medium: number;
    low: number;
  };
}
```

### Task List Meta (in /api/tasks response)

```typescript
{
  status_counts: {
    todo: number;
    in_progress: number;
    done: number;
    blocked: number;
  };
  priority_counts: {
    high: number;
    medium: number;
    low: number;
  };
}
```

---

## Examples

### Complete Frontend Workflow

```javascript
// 1. Health check
const health = await fetch('http://localhost:8001/health');
console.log(await health.json());
// { status: "healthy", mcp_connected: true }

// 2. Get all projects
const projectsResp = await fetch('http://localhost:8001/api/projects', {
  headers: { 'X-API-Key': 'your-api-key' }
});
const { projects } = await projectsResp.json();
console.log(`Found ${projects.length} projects`);

// 3. Select first project and get stats
const projectId = projects[0].id; // hash ID like "1e7be4ae"
const infoResp = await fetch(`http://localhost:8001/api/projects/${projectId}/info`, {
  headers: { 'X-API-Key': 'your-api-key' }
});
const { project, stats } = await infoResp.json();
console.log(`Project: ${project.friendly_name}`);
console.log(`Total tasks: ${stats.total_tasks}`);

// 4. Get high-priority tasks
const tasksResp = await fetch(
  `http://localhost:8001/api/tasks?project_id=${projectId}&priority=high`,
  { headers: { 'X-API-Key': 'your-api-key' } }
);
const { tasks, meta } = await tasksResp.json();
console.log(`Found ${tasks.length} high-priority tasks`);
console.log(`Total high priority: ${meta.priority_counts.high}`);

// 5. Get next actionable tasks
const nextResp = await fetch(
  `http://localhost:8001/api/tasks/next?project_id=${projectId}`,
  { headers: { 'X-API-Key': 'your-api-key' } }
);
const { tasks: nextTasks } = await nextResp.json();
console.log(`${nextTasks.length} tasks ready to work on`);

// 6. Search for specific tasks
const searchResp = await fetch(
  `http://localhost:8001/api/tasks/search?q=deployment&project_id=${projectId}`,
  { headers: { 'X-API-Key': 'your-api-key' } }
);
const { tasks: searchResults } = await searchResp.json();
console.log(`Found ${searchResults.length} deployment tasks`);

// 7. Get task details
const taskId = tasks[0].id;
const taskResp = await fetch(`http://localhost:8001/api/tasks/${taskId}`, {
  headers: { 'X-API-Key': 'your-api-key' }
});
const { task } = await taskResp.json();
console.log(`Task: ${task.title}`);
console.log(`Status: ${task.status}, Priority: ${task.priority}`);
```

---

## Performance Targets

- **P50 latency:** <100ms
- **P95 latency:** <250ms
- **P99 latency:** <500ms

**Optimization Strategies:**
- MCP connection pooling
- Response caching (5-second TTL for project list)
- Database query optimization
- Pagination for large result sets
- Gzip compression for responses >1KB

---

## CORS Configuration

**Allowed Origins (Development):**
- `http://localhost:8001`
- `http://127.0.0.1:8001`

**Allowed Origins (Production):**
- `https://tasks.bmcis.net`
- `https://knowledge.bmcis.net` (if hosted together)

**Allowed Methods:**
- `GET`, `OPTIONS`

**Allowed Headers:**
- `X-API-Key`, `Content-Type`

---

## Versioning

API version is included in response headers:

```
X-API-Version: 1.0.0
```

Future major versions will use URL prefix: `/api/v2/tasks`

---

## Complete Endpoint Summary

### v1.0 Endpoints (Read-Only)

```
GET  /health                      - Health check (no auth)
GET  /api/projects                - List all projects
GET  /api/projects/{id}/info      - Get project details + stats
GET  /api/tasks                   - List tasks with filters
GET  /api/tasks/{id}              - Get single task
GET  /api/tasks/search            - Full-text search
GET  /api/tasks/next              - Get actionable tasks
GET  /api/tasks/blocked           - Get blocked tasks
```

**All endpoints except `/health` require `X-API-Key` header.**

---

## Changelog

### v1.0.0 (2025-11-02)
- Initial API specification
- 8 core endpoints (health, projects, tasks)
- API key authentication
- Read-only viewer (no POST/PATCH/DELETE)
- Filtering and pagination support
- Full-text search capability
- Project hash IDs in URLs
- Status/priority counts in list responses

---

## Future Enhancements (v1.1.0+)

**Planned Features:**
- [ ] Task creation endpoint (POST /api/tasks)
- [ ] Task update endpoint (PATCH /api/tasks/:id)
- [ ] Task tree endpoint (GET /api/tasks/:id/tree)
- [ ] Entity management endpoints
- [ ] Project name update endpoint
- [ ] WebSocket support for real-time task updates
- [ ] Enhanced filtering (date ranges, multiple tags)
- [ ] Export endpoints (JSON, CSV)
- [ ] Bulk operations (batch status updates)
- [ ] Task history/audit log
- [ ] User-specific views (created_by filtering)
- [ ] Dashboard analytics endpoint
- [ ] Custom field support

---

## Support

**Questions:** Check task-mcp MCP server documentation
**Issues:** File bug reports in project repository
**MCP Tools Reference:** https://github.com/your-repo/task-mcp

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-02
**Author:** Claude Code Assistant
**Status:** REVISED - Ready for Implementation
