# Entity Viewer API Documentation

## Overview

The Entity Viewer API provides read-only HTTP endpoints for managing and querying entities in the task-mcp system. Entities are typed objects (files, vendors, etc.) that can be linked to tasks for rich context management.

**Base URL:** `http://localhost:8001`
**API Version:** 1.0.0
**OpenAPI Documentation:** `/api/docs`
**ReDoc Documentation:** `/api/redoc`

## Authentication

All entity endpoints require API key authentication via the `X-API-Key` header.

**Header:**
```
X-API-Key: your-api-key-here
```

**Default Development Key:** `dev-key-local-only` (configured in `.env` file)

**Error Responses:**
- **401 Unauthorized** - Missing or invalid API key
  ```json
  {
    "detail": "Missing API key. Include X-API-Key header."
  }
  ```

## Entity Data Model

### Entity Object

```json
{
  "id": 1,
  "entity_type": "file",
  "name": "Authentication Controller",
  "identifier": "/src/api/auth.py",
  "description": "Handles user authentication and session management",
  "metadata": "{\"language\": \"python\", \"line_count\": 250}",
  "tags": "backend api authentication",
  "created_by": "conv-123",
  "created_at": "2025-11-02T10:00:00",
  "updated_at": "2025-11-02T10:00:00",
  "deleted_at": null
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique entity identifier (auto-generated) |
| `entity_type` | string | Entity type: `"file"` or `"other"` |
| `name` | string | Human-readable display name (required) |
| `identifier` | string \| null | Unique identifier (e.g., file path, vendor code) |
| `description` | string \| null | Detailed description (max 10,000 chars) |
| `metadata` | string \| null | JSON string for flexible data storage |
| `tags` | string \| null | Space-separated tags (normalized to lowercase) |
| `created_by` | string | Conversation ID that created the entity |
| `created_at` | string | ISO 8601 timestamp (creation time) |
| `updated_at` | string | ISO 8601 timestamp (last update time) |
| `deleted_at` | string \| null | ISO 8601 timestamp (soft delete time) |

### Entity Types

- **`file`** - Code files, configuration files, documentation
- **`other`** - Vendors, people, organizations, custom entities

## Endpoints

### 1. List Entities

Get a paginated list of entities with optional filtering.

**Endpoint:** `GET /api/entities`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_id` | string | No | - | Filter by project hash ID |
| `workspace_path` | string | No | - | Explicit workspace path |
| `entity_type` | string | No | - | Filter by type: `"file"` or `"other"` |
| `tags` | string | No | - | Filter by tags (space-separated, partial match) |
| `limit` | integer | No | 50 | Max results per page (1-100) |
| `offset` | integer | No | 0 | Pagination offset (≥0) |

**Example Request:**

```bash
# List all entities
curl -X GET "http://localhost:8001/api/entities" \
  -H "X-API-Key: dev-key-local-only"

# Filter by entity type
curl -X GET "http://localhost:8001/api/entities?entity_type=file&limit=20" \
  -H "X-API-Key: dev-key-local-only"

# Filter by tags
curl -X GET "http://localhost:8001/api/entities?tags=vendor+insurance" \
  -H "X-API-Key: dev-key-local-only"

# Pagination
curl -X GET "http://localhost:8001/api/entities?limit=10&offset=20" \
  -H "X-API-Key: dev-key-local-only"
```

**Response:** `200 OK`

```json
{
  "entities": [
    {
      "id": 1,
      "entity_type": "file",
      "name": "Authentication Controller",
      "identifier": "/src/api/auth.py",
      "description": "Handles user authentication",
      "metadata": "{\"language\": \"python\"}",
      "tags": "backend api authentication",
      "created_by": "conv-123",
      "created_at": "2025-11-02T10:00:00",
      "updated_at": "2025-11-02T10:00:00",
      "deleted_at": null
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0,
  "filters": {
    "entity_type": "file"
  }
}
```

**Error Responses:**

- **401 Unauthorized** - Missing or invalid API key
- **422 Validation Error** - Invalid query parameters
  ```json
  {
    "detail": [
      {
        "loc": ["query", "limit"],
        "msg": "ensure this value is less than or equal to 100",
        "type": "value_error.number.not_le"
      }
    ]
  }
  ```
- **500 Internal Server Error** - MCP connection failure

---

### 2. Get Single Entity

Retrieve a single entity by ID.

**Endpoint:** `GET /api/entities/{entity_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_id` | integer | Yes | Entity ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | No | Project hint for workspace resolution |
| `workspace_path` | string | No | Explicit workspace path |

**Example Request:**

```bash
curl -X GET "http://localhost:8001/api/entities/42" \
  -H "X-API-Key: dev-key-local-only"
```

**Response:** `200 OK`

```json
{
  "id": 42,
  "entity_type": "other",
  "name": "ABC Insurance",
  "identifier": "ABC-INS",
  "description": "Primary insurance data vendor",
  "metadata": "{\"phase\": \"active\", \"formats\": [\"xlsx\", \"pdf\"]}",
  "tags": "vendor insurance active",
  "created_by": "conv-123",
  "created_at": "2025-11-02T10:00:00",
  "updated_at": "2025-11-02T10:00:00",
  "deleted_at": null
}
```

**Error Responses:**

- **401 Unauthorized** - Missing or invalid API key
- **404 Not Found** - Entity not found or deleted
  ```json
  {
    "error": "Not Found",
    "message": "Entity with ID 42 not found or deleted",
    "status_code": 404
  }
  ```
- **422 Validation Error** - Invalid entity_id format
- **500 Internal Server Error** - MCP connection failure

---

### 3. Search Entities

Search entities by name or identifier using full-text search.

**Endpoint:** `GET /api/entities/search`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | Yes | - | Search query (name or identifier) |
| `project_id` | string | No | - | Filter by project |
| `workspace_path` | string | No | - | Explicit workspace path |
| `entity_type` | string | No | - | Filter by type: `"file"` or `"other"` |
| `limit` | integer | No | 20 | Max results (1-100) |

**Example Request:**

```bash
# Search all entities
curl -X GET "http://localhost:8001/api/entities/search?q=auth" \
  -H "X-API-Key: dev-key-local-only"

# Search with type filter
curl -X GET "http://localhost:8001/api/entities/search?q=controller&entity_type=file" \
  -H "X-API-Key: dev-key-local-only"

# Search with limit
curl -X GET "http://localhost:8001/api/entities/search?q=vendor&limit=10" \
  -H "X-API-Key: dev-key-local-only"
```

**Response:** `200 OK`

```json
{
  "entities": [
    {
      "id": 1,
      "entity_type": "file",
      "name": "Authentication Controller",
      "identifier": "/src/api/auth.py",
      "description": "Handles user authentication",
      "metadata": "{\"language\": \"python\"}",
      "tags": "backend api authentication",
      "created_by": "conv-123",
      "created_at": "2025-11-02T10:00:00",
      "updated_at": "2025-11-02T10:00:00",
      "deleted_at": null
    }
  ],
  "total": 5,
  "query": "auth",
  "limit": 20
}
```

**Error Responses:**

- **400 Bad Request** - Missing search query
  ```json
  {
    "error": "Bad Request",
    "message": "Search query 'q' is required",
    "status_code": 400
  }
  ```
- **401 Unauthorized** - Missing or invalid API key
- **422 Validation Error** - Invalid query parameters
- **500 Internal Server Error** - MCP connection failure

---

### 4. Get Entity Statistics

Get entity statistics including counts by type and top tags.

**Endpoint:** `GET /api/entities/stats`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | No | Filter by project hash ID |
| `workspace_path` | string | No | Explicit workspace path |

**Example Request:**

```bash
curl -X GET "http://localhost:8001/api/entities/stats" \
  -H "X-API-Key: dev-key-local-only"
```

**Response:** `200 OK`

```json
{
  "total": 125,
  "by_type": {
    "file": 80,
    "other": 45
  },
  "top_tags": [
    {
      "tag": "vendor",
      "count": 25
    },
    {
      "tag": "backend",
      "count": 18
    },
    {
      "tag": "api",
      "count": 15
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total entity count |
| `by_type.file` | integer | Count of file entities |
| `by_type.other` | integer | Count of other entities |
| `top_tags` | array | Top 10 tags by frequency |
| `top_tags[].tag` | string | Tag name |
| `top_tags[].count` | integer | Tag usage count |

**Error Responses:**

- **401 Unauthorized** - Missing or invalid API key
- **500 Internal Server Error** - MCP connection failure

---

### 5. Get Linked Tasks

Get all tasks linked to a specific entity (reverse lookup).

**Endpoint:** `GET /api/entities/{entity_id}/tasks`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_id` | integer | Yes | Entity ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | No | Project hint for workspace resolution |
| `workspace_path` | string | No | Explicit workspace path |
| `status` | string | No | Filter by task status (todo, in_progress, done, etc.) |
| `priority` | string | No | Filter by task priority (low, medium, high) |

**Example Request:**

```bash
# Get all tasks for entity
curl -X GET "http://localhost:8001/api/entities/42/tasks" \
  -H "X-API-Key: dev-key-local-only"

# Filter by status
curl -X GET "http://localhost:8001/api/entities/42/tasks?status=in_progress" \
  -H "X-API-Key: dev-key-local-only"

# Filter by priority
curl -X GET "http://localhost:8001/api/entities/42/tasks?priority=high" \
  -H "X-API-Key: dev-key-local-only"

# Combine filters
curl -X GET "http://localhost:8001/api/entities/42/tasks?status=todo&priority=high" \
  -H "X-API-Key: dev-key-local-only"
```

**Response:** `200 OK`

```json
{
  "tasks": [
    {
      "id": 15,
      "title": "Integrate ABC Insurance vendor data",
      "description": "Implement ETL pipeline for ABC Insurance",
      "status": "in_progress",
      "priority": "high",
      "parent_task_id": null,
      "depends_on": null,
      "tags": "vendor integration",
      "blocker_reason": null,
      "file_references": null,
      "created_by": "conv-123",
      "created_at": "2025-11-02T10:00:00",
      "updated_at": "2025-11-02T11:00:00",
      "completed_at": null,
      "deleted_at": null,
      "link_created_at": "2025-11-02T10:05:00",
      "link_created_by": "conv-123"
    }
  ],
  "total": 3,
  "limit": 3,
  "offset": 0,
  "filters": {
    "status": "in_progress"
  }
}
```

**Response Fields:**

Tasks include standard task fields plus link metadata:

| Field | Type | Description |
|-------|------|-------------|
| `link_created_at` | string | ISO 8601 timestamp when link was created |
| `link_created_by` | string | Conversation ID that created the link |

**Error Responses:**

- **401 Unauthorized** - Missing or invalid API key
- **404 Not Found** - Entity not found or deleted
  ```json
  {
    "error": "Not Found",
    "message": "Entity with ID 42 not found or deleted",
    "status_code": 404
  }
  ```
- **422 Validation Error** - Invalid query parameters
- **500 Internal Server Error** - MCP connection failure

---

## Common Response Patterns

### Pagination

All list endpoints support pagination:

```json
{
  "entities": [...],
  "total": 100,      // Total matching entities
  "limit": 50,       // Max results per page
  "offset": 0        // Current page offset
}
```

**Pagination Calculation:**
- Page 1: `offset=0&limit=50`
- Page 2: `offset=50&limit=50`
- Page 3: `offset=100&limit=50`

### Filtering

Applied filters are returned in the response:

```json
{
  "entities": [...],
  "filters": {
    "entity_type": "file",
    "tags": "vendor insurance"
  }
}
```

### Error Response Format

All error responses follow this structure:

```json
{
  "error": "Error Type",
  "message": "Detailed error message",
  "status_code": 400
}
```

## Use Cases

### File Entities

Track code files involved in tasks:

```bash
# List all file entities
curl -X GET "http://localhost:8001/api/entities?entity_type=file" \
  -H "X-API-Key: dev-key-local-only"

# Search for authentication files
curl -X GET "http://localhost:8001/api/entities/search?q=auth&entity_type=file" \
  -H "X-API-Key: dev-key-local-only"

# Get tasks for a specific file
curl -X GET "http://localhost:8001/api/entities/5/tasks?status=in_progress" \
  -H "X-API-Key: dev-key-local-only"
```

### Vendor Entities

Manage vendor relationships:

```bash
# List all vendors
curl -X GET "http://localhost:8001/api/entities?tags=vendor" \
  -H "X-API-Key: dev-key-local-only"

# Get vendor statistics
curl -X GET "http://localhost:8001/api/entities/stats" \
  -H "X-API-Key: dev-key-local-only"

# Find high-priority tasks for a vendor
curl -X GET "http://localhost:8001/api/entities/42/tasks?priority=high" \
  -H "X-API-Key: dev-key-local-only"
```

## Rate Limiting

Currently not implemented. Future versions may include:
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`
- 429 Too Many Requests response

## CORS Configuration

Allowed origins:
- `http://localhost:8001` (same origin)
- `http://localhost:3000` (React dev server)
- `http://localhost:5173` (Vite dev server)
- `http://127.0.0.1:8001`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`

Allowed methods: `GET`, `OPTIONS` (read-only API)

Allowed headers: `Content-Type`, `X-API-Key`

## OpenAPI Schema

Full OpenAPI 3.0 schema available at:
- Swagger UI: `http://localhost:8001/api/docs`
- ReDoc: `http://localhost:8001/api/redoc`
- JSON: `http://localhost:8001/api/openapi.json`

## Related Documentation

- [Task Endpoints Documentation](/docs/api/task-endpoints.md)
- [Project Endpoints Documentation](/docs/api/project-endpoints.md)
- [Entity System Overview](/CLAUDE.md#entity-system)
- [MCP Tools Reference](/docs/mcp-tools-reference.md)

## Changelog

### v1.0.0 (2025-11-02)
- Initial release of Entity Viewer API
- 5 entity endpoints implemented
- Full-text search support
- Task-entity relationship queries
- Statistics and aggregation endpoints
