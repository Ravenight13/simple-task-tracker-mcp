# Entity Viewer Implementation Notes

**Created:** 2025-11-02
**Author:** Claude Code Development Agent
**Task:** #131 - Create developer implementation notes
**Related Tasks:** #69 (Entity Viewer), #105 (Backend), #106 (Frontend)

---

## Executive Summary

This document provides comprehensive technical documentation for developers working with the Entity Viewer feature in task-viewer. The Entity Viewer is a read-only web interface for viewing, filtering, and searching entities (files, vendors, etc.) and their relationships with tasks.

**Key Technologies:**
- **Backend:** FastAPI (async Python), Pydantic v2 models
- **Frontend:** Alpine.js 3.x, Tailwind CSS 3.x
- **MCP Integration:** Direct import of task-mcp FastMCP server
- **Architecture Pattern:** Tab-based single-page application

**Implementation Status:** ✅ Production Ready (v1.0.0)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Backend Implementation](#backend-implementation)
3. [Frontend Implementation](#frontend-implementation)
4. [Data Flow Diagrams](#data-flow-diagrams)
5. [API Integration Pattern](#api-integration-pattern)
6. [State Management](#state-management)
7. [Extension Points](#extension-points)
8. [Known Limitations](#known-limitations)
9. [Future Enhancements](#future-enhancements)

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (Client)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               Alpine.js Single-Page App                   │  │
│  │  ┌──────────────────┐        ┌──────────────────┐        │  │
│  │  │  Task Viewer     │        │  Entity Viewer   │        │  │
│  │  │  Component       │        │  Component       │        │  │
│  │  │  (existing)      │◄──────►│  (new)           │        │  │
│  │  └──────────────────┘  Tab   └──────────────────┘        │  │
│  │                          Switch                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              │ HTTP/REST                         │
│                              ▼                                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ X-API-Key Auth
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Server)                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ /api/tasks   │  │/api/entities │  │/api/projects │   │  │
│  │  │ (existing)   │  │   (new)      │  │ (existing)   │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │                          │                                │  │
│  │                          ▼                                │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │         Workspace Resolver + MCP Client             │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ Direct Import
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    task-mcp MCP Server                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    MCP Tools                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ list_entities│  │ get_entity   │  │ search_      │   │  │
│  │  │              │  │              │  │ entities     │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │         │                  │                  │          │  │
│  │         └──────────────────┼──────────────────┘          │  │
│  │                            ▼                             │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │      Project SQLite Databases (per workspace)      │ │  │
│  │  │  ~/.task-mcp/databases/project_{hash}.db           │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend Framework** | Alpine.js | 3.x | Reactive UI state management |
| **Frontend Styling** | Tailwind CSS | 3.x | Utility-first CSS framework |
| **Backend Framework** | FastAPI | Latest | Async Python web framework |
| **Data Validation** | Pydantic | v2 | Request/response models |
| **MCP Integration** | task-mcp | v0.5.0+ | Direct FastMCP server import |
| **Database** | SQLite | WAL mode | Per-project entity storage |
| **Authentication** | API Key | Custom | X-API-Key header-based auth |

### 1.3 Design Principles

1. **Pattern Consistency:** Entity viewer mirrors task viewer patterns exactly
2. **Read-Only First:** Phase 1 focuses on viewing/searching (no CRUD)
3. **Zero Breaking Changes:** Purely additive feature (no existing code modified)
4. **MCP-Native:** Leverage existing MCP tools (no new backend logic needed)
5. **Progressive Enhancement:** Tab-based architecture enables future expansion

---

## 2. Backend Implementation

### 2.1 API Endpoints

All entity endpoints follow the same patterns as task endpoints: API key authentication, workspace resolution, Pydantic validation, and consistent error handling.

#### Endpoint Summary

| Method | Path | Purpose | Response Model |
|--------|------|---------|----------------|
| GET | `/api/entities` | List entities with filtering | `EntityListResponse` |
| GET | `/api/entities/search` | Full-text search | `EntitySearchResponse` |
| GET | `/api/entities/{entity_id}` | Get single entity | `EntityResponse` |
| GET | `/api/entities/{entity_id}/tasks` | Get linked tasks | `TaskListResponse` |
| GET | `/api/entities/stats` | Get aggregate stats | `EntityStatsResponse` |

**Critical Route Ordering:**
```python
# ⚠️ IMPORTANT: Specific routes MUST come BEFORE parameterized routes
# to avoid path matching conflicts

@app.get("/api/entities")              # ✅ First
@app.get("/api/entities/search")       # ✅ Second (before /{entity_id})
@app.get("/api/entities/stats")        # ✅ Third (before /{entity_id})
@app.get("/api/entities/{entity_id}/tasks")  # ✅ Fourth
@app.get("/api/entities/{entity_id}")  # ✅ Last (catches remaining paths)
```

#### 2.1.1 List Entities Endpoint

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/main.py:640-698`

```python
@app.get("/api/entities", response_model=EntityListResponse)
async def list_entities(
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
    entity_type: Optional[str] = None,  # 'file' | 'other'
    tags: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List entities with optional filtering and pagination.

    Query Parameters:
        - project_id: Project hash ID (for workspace resolution)
        - workspace_path: Explicit workspace path (alternative to project_id)
        - entity_type: Filter by type ('file' or 'other')
        - tags: Space-separated tags to filter by
        - limit: Max results per page (default: 50, max: 100)
        - offset: Pagination offset (default: 0)

    Returns:
        EntityListResponse with:
        - entities: List of entity objects
        - total: Total count matching filters
        - limit/offset: Pagination params
        - filters: Applied filters

    Requires: X-API-Key header
    """
```

**Implementation Pattern:**
1. **Authenticate:** Verify API key via `verify_api_key()`
2. **Resolve Workspace:** Use `workspace_resolver.resolve(project_id, workspace_path)`
3. **Build MCP Args:** Construct dict with `workspace_path` (REQUIRED as of v0.4.0)
4. **Call MCP Tool:** `await mcp_service.call_tool("list_entities", args)`
5. **Apply Pagination:** Slice results `[offset:offset+limit]`
6. **Return Response:** Wrap in Pydantic `EntityListResponse` model

**Critical Implementation Details:**
```python
# ✅ CORRECT: Always pass workspace_path explicitly (v0.4.0 requirement)
args: dict[str, Any] = {"workspace_path": resolved_workspace}
if entity_type:
    args["entity_type"] = entity_type
if tags:
    args["tags"] = tags

# ❌ WRONG: Missing workspace_path will cause ValueError
args = {"entity_type": entity_type}  # Missing workspace_path!
```

#### 2.1.2 Search Entities Endpoint

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/main.py:701-749`

```python
@app.get("/api/entities/search", response_model=EntitySearchResponse)
async def search_entities(
    q: str,  # Required search query
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """
    Full-text search on entity name and identifier.

    Uses MCP search_entities tool which searches both the name
    and identifier fields (case-insensitive).
    """
```

**Search Behavior:**
- Searches both `name` and `identifier` fields
- Case-insensitive matching
- No regex support (simple substring search)
- Returns up to `limit` results (default: 20, max: 100)

#### 2.1.3 Get Entity by ID Endpoint

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/main.py:810-843`

```python
@app.get("/api/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: int,
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
):
    """
    Get a single entity by ID with full details.

    Returns:
        Full entity object including metadata (JSON string)

    Raises:
        404 if entity not found or soft-deleted
    """
```

#### 2.1.4 Get Entity Tasks Endpoint (Reverse Lookup)

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/main.py:752-807`

```python
@app.get("/api/entities/{entity_id}/tasks", response_model=TaskListResponse)
async def get_entity_tasks(
    entity_id: int,
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
    status: Optional[str] = None,      # Optional filter
    priority: Optional[str] = None,    # Optional filter
):
    """
    Get all tasks linked to an entity (reverse lookup).

    Uses MCP get_entity_tasks tool which queries the
    task_entity_links junction table.

    Optional Filters:
        - status: Filter by task status (todo, in_progress, done, etc.)
        - priority: Filter by task priority (low, medium, high)

    Returns:
        TaskListResponse (reuses existing task response model)
    """
```

**Key Design Decision:** Returns `TaskListResponse` (not a custom model) to maintain consistency with task endpoints.

#### 2.1.5 Get Entity Stats Endpoint

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/main.py:846-903`

```python
@app.get("/api/entities/stats", response_model=EntityStatsResponse)
async def get_entity_stats(
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
):
    """
    Get aggregate entity statistics.

    Returns:
        - total: Total entity count
        - by_type: {file: count, other: count}
        - top_tags: [{tag: name, count: freq}, ...] (top 10)
    """
```

**Implementation Note:** Stats endpoint loads ALL entities and aggregates client-side (no DB-level aggregation). This is acceptable for current scale but could be optimized with SQL GROUP BY for larger datasets.

### 2.2 Response Models (Pydantic)

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/models.py:115-188`

#### 2.2.1 EntityResponse

```python
class EntityResponse(BaseModel):
    """Response model for a single entity.

    Entities are typed objects (file, vendor, etc.) that can be linked to tasks
    for rich context management. Entity metadata is stored as a JSON string for
    flexible domain-specific data storage.
    """

    id: int
    entity_type: str = Field(..., description="Entity type: 'file' or 'other'")
    name: str = Field(..., description="Human-readable entity name")
    identifier: Optional[str] = Field(None, description="Unique identifier (file path, vendor code, etc.)")
    description: Optional[str] = Field(None, max_length=10000, description="Entity description (max 10k chars)")
    metadata: Optional[str] = Field(None, description="Generic JSON metadata as string")
    tags: Optional[str] = Field(None, description="Space-separated tags")
    created_by: str = Field(..., description="Conversation ID that created this entity")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    updated_at: str = Field(..., description="ISO 8601 timestamp")
    deleted_at: Optional[str] = Field(None, description="Soft delete timestamp")

    class Config:
        from_attributes = True  # Pydantic v2 (replaces orm_mode)
```

**Field Notes:**
- `metadata`: Stored as JSON string (not parsed dict) to preserve flexibility
- `tags`: Space-separated string (mirrors task tags pattern)
- `identifier`: Optional but recommended (unique per entity_type in DB)

#### 2.2.2 EntityListResponse

```python
class EntityListResponse(BaseModel):
    """Response model for paginated entity list."""

    entities: list[EntityResponse]
    total: int = Field(..., description="Total number of entities matching filters")
    limit: int = Field(100, description="Maximum entities per page")
    offset: int = Field(0, description="Number of entities skipped")
    filters: Optional[dict[str, Any]] = Field(None, description="Applied filters (entity_type, tags)")
```

**Pagination Pattern:** Matches task list pagination exactly (offset-based, not cursor-based).

#### 2.2.3 EntityStatsResponse

```python
class EntityStatsResponse(BaseModel):
    """Response model for entity statistics."""

    total: int = Field(..., description="Total number of entities")
    by_type: EntityTypeCount = Field(..., description="Entity counts by type")
    top_tags: list[TagCount] = Field(..., description="Top 10 tags by frequency")

class EntityTypeCount(BaseModel):
    """Entity counts by type."""
    file: int = Field(0, description="Number of file entities")
    other: int = Field(0, description="Number of other entities")

class TagCount(BaseModel):
    """Tag with occurrence count."""
    tag: str = Field(..., description="Tag name")
    count: int = Field(..., description="Number of entities with this tag")
```

### 2.3 MCP Tool Integration

All entity endpoints call existing MCP tools from task-mcp. No new MCP tools were created for the entity viewer.

**Available MCP Tools:**

| MCP Tool | Purpose | Required Params | Optional Params |
|----------|---------|-----------------|-----------------|
| `list_entities` | List all entities | `workspace_path` | `entity_type`, `tags` |
| `get_entity` | Get single entity | `workspace_path`, `entity_id` | - |
| `search_entities` | Full-text search | `workspace_path`, `search_term` | `entity_type` |
| `get_entity_tasks` | Get linked tasks | `workspace_path`, `entity_id` | `status`, `priority` |

**MCP Client Pattern:**

```python
# Initialize MCP service (done at startup)
from mcp_client import mcp_service
await mcp_service.initialize()

# Call MCP tool from endpoint
async def my_endpoint():
    # 1. Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)

    # 2. Build arguments (ALWAYS include workspace_path)
    args = {
        "workspace_path": resolved_workspace,
        "entity_type": entity_type  # Optional params
    }

    # 3. Call MCP tool
    result = await mcp_service.call_tool("list_entities", args)

    # 4. Validate and return
    return EntityListResponse(entities=result, total=len(result))
```

**Critical Requirement (v0.4.0+):** ALL MCP tool calls MUST include explicit `workspace_path` parameter. Omitting this will cause `ValueError: workspace_path is REQUIRED`.

### 2.4 Authentication Flow

```
┌────────────┐                 ┌──────────────┐
│   Client   │                 │   FastAPI    │
│  (Browser) │                 │   Backend    │
└────────────┘                 └──────────────┘
      │                                │
      │  GET /api/entities             │
      │  X-API-Key: dev-key-local-only │
      ├───────────────────────────────►│
      │                                │
      │                                │ verify_api_key()
      │                                ├──────────┐
      │                                │          │
      │                                │◄─────────┘
      │                                │
      │                                │ Check API_KEY env var
      │                                ├──────────┐
      │                                │          │
      │                                │◄─────────┘
      │                                │
      │                                │ If match: Continue
      │                                │ If no match: 401 Unauthorized
      │                                │
      │  200 OK + JSON Response        │
      │◄───────────────────────────────┤
      │                                │
```

**Implementation:**

```python
# .env file
API_KEY=dev-key-local-only

# verify_api_key() dependency
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    expected_key = os.getenv("API_KEY", "dev-key-local-only")

    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return x_api_key

# Endpoint usage
@app.get("/api/entities")
async def list_entities(x_api_key: str = Header(None)):
    await verify_api_key(x_api_key)  # Raises 401 if invalid
    # ... rest of endpoint logic
```

### 2.5 Error Handling

FastAPI exception handlers convert Python exceptions to HTTP error responses:

```python
@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle ValueError (invalid input, not found)."""
    error_msg = str(exc)
    if "not found" in error_msg.lower():
        status_code = 404  # Entity not found
    else:
        status_code = 400  # Invalid parameters

    return JSONResponse(
        status_code=status_code,
        content={"error": "ValueError", "message": error_msg}
    )

@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc: RuntimeError):
    """Handle RuntimeError (MCP tool failures)."""
    logger.error(f"Runtime error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "RuntimeError", "message": str(exc)}
    )
```

**Error Response Schema:**
```json
{
  "error": "ValueError",
  "message": "Entity with ID 999 not found or deleted",
  "status_code": 404
}
```

---

## 3. Frontend Implementation

### 3.1 Alpine.js State Management

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html:1700-2100`

The entity viewer uses Alpine.js reactive state management within the global `taskViewer()` component.

#### 3.1.1 Entity State Variables

```javascript
function taskViewer() {
  return {
    // ... existing task state ...

    // Tab State
    activeTab: 'tasks',  // 'tasks' | 'entities'

    // Entity Data
    entities: [],              // Full entity list from API
    filteredEntities: [],      // Filtered/sorted entities for display
    selectedEntity: null,      // Currently selected entity (for modal)
    entityStats: {             // Aggregate statistics
      total: 0,
      by_type: { file: 0, other: 0 },
      top_tags: []
    },

    // Entity Filters
    entityTypeFilter: 'all',   // 'all' | 'file' | 'other'
    entitySearchQuery: '',     // Search input value
    entitySelectedTags: [],    // Selected tag filters (multi-select)
    entitySortBy: 'name_asc',  // Sort field + direction

    // Entity UI State
    loadingEntities: false,    // Loading spinner
    entityError: null,         // Error message
    showEntityModal: false,    // Entity detail modal visibility
    entityTasks: [],           // Tasks linked to selected entity
    loadingEntityTasks: false, // Loading linked tasks
  }
}
```

#### 3.1.2 Entity Methods

```javascript
{
  // ==================== Entity Loading ====================

  async loadEntities() {
    if (!this.currentProject) {
      this.entityError = 'No project selected';
      return;
    }

    this.loadingEntities = true;
    this.entityError = null;

    try {
      const response = await fetch(
        `${API_CONFIG.baseUrl}/api/entities?project_id=${this.currentProject.id}`,
        { headers: { 'X-API-Key': this.apiKey } }
      );

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      this.entities = data.entities || [];

      // Load stats separately
      await this.loadEntityStats();

      // Apply filters
      this.applyEntityFilters();

    } catch (err) {
      this.entityError = err.message || 'Failed to load entities';
    } finally {
      this.loadingEntities = false;
    }
  },

  async loadEntityStats() {
    try {
      const response = await fetch(
        `${API_CONFIG.baseUrl}/api/entities/stats?project_id=${this.currentProject.id}`,
        { headers: { 'X-API-Key': this.apiKey } }
      );

      if (response.ok) {
        this.entityStats = await response.json();
      }
    } catch (err) {
      console.error('Failed to load entity stats:', err);
    }
  },

  // ==================== Entity Filtering ====================

  applyEntityFilters() {
    let filtered = [...this.entities];

    // Filter by entity type
    if (this.entityTypeFilter !== 'all') {
      filtered = filtered.filter(e => e.entity_type === this.entityTypeFilter);
    }

    // Filter by tags (multi-select)
    if (this.entitySelectedTags.length > 0) {
      filtered = filtered.filter(entity => {
        const entityTags = (entity.tags || '').split(' ').filter(t => t);
        return this.entitySelectedTags.some(tag => entityTags.includes(tag));
      });
    }

    // Filter by search query (name, identifier, description)
    if (this.entitySearchQuery) {
      const query = this.entitySearchQuery.toLowerCase();
      filtered = filtered.filter(e => {
        return (
          (e.name || '').toLowerCase().includes(query) ||
          (e.identifier || '').toLowerCase().includes(query) ||
          (e.description || '').toLowerCase().includes(query)
        );
      });
    }

    // Sort
    filtered = this.sortEntities(filtered);

    this.filteredEntities = filtered;
  },

  sortEntities(entities) {
    const [field, order] = this.entitySortBy.split('_');

    return entities.sort((a, b) => {
      let aVal, bVal;

      switch (field) {
        case 'name':
          aVal = (a.name || '').toLowerCase();
          bVal = (b.name || '').toLowerCase();
          break;
        case 'type':
          aVal = a.entity_type;
          bVal = b.entity_type;
          break;
        case 'created':
          aVal = new Date(a.created_at);
          bVal = new Date(b.created_at);
          break;
        default:
          return 0;
      }

      if (order === 'asc') {
        return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      } else {
        return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
      }
    });
  },

  // ==================== Entity Modal ====================

  async openEntityDetail(entity) {
    this.selectedEntity = entity;
    this.showEntityModal = true;
    this.entityTasks = [];
    this.loadingEntityTasks = true;

    // Load linked tasks
    try {
      const response = await fetch(
        `${API_CONFIG.baseUrl}/api/entities/${entity.id}/tasks?project_id=${this.currentProject.id}`,
        { headers: { 'X-API-Key': this.apiKey } }
      );

      if (response.ok) {
        const data = await response.json();
        this.entityTasks = data.tasks || [];
      }
    } catch (err) {
      console.error('Failed to load entity tasks:', err);
    } finally {
      this.loadingEntityTasks = false;
    }
  },

  closeEntityModal() {
    this.showEntityModal = false;
    this.selectedEntity = null;
    this.entityTasks = [];
  },

  // ==================== Tab Switching ====================

  switchTab(tab) {
    this.activeTab = tab;
    window.location.hash = tab; // Update URL hash

    if (tab === 'entities' && this.entities.length === 0) {
      this.loadEntities(); // Lazy load entities on first tab switch
    }
  },

  handleHashChange() {
    const hash = window.location.hash.slice(1); // Remove '#'
    if (hash === 'entities') {
      this.activeTab = 'entities';
    } else {
      this.activeTab = 'tasks';
    }
  },
}
```

### 3.2 Component Structure

#### 3.2.1 Tab Navigation

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html:215-275`

```html
<!-- Tab Navigation Bar (sticky below header) -->
<div class="sticky top-16 z-40 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <nav class="flex space-x-8" role="tablist">
      <!-- Tasks Tab -->
      <button
        @click="switchTab('tasks')"
        :class="{
          'text-blue-600 dark:text-blue-400': activeTab === 'tasks',
          'text-gray-500 hover:text-gray-700': activeTab !== 'tasks'
        }"
        :aria-current="activeTab === 'tasks' ? 'page' : undefined"
      >
        <span class="flex items-center gap-2">
          Tasks
          <span x-text="statusCounts.total" class="badge"></span>
        </span>
        <!-- Active indicator line -->
        <span
          x-show="activeTab === 'tasks'"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"
        ></span>
      </button>

      <!-- Entities Tab -->
      <button @click="switchTab('entities')">
        <!-- Same structure as Tasks tab -->
        Entities
        <span x-text="entityStats.total" class="badge"></span>
      </button>
    </nav>
  </div>
</div>
```

**Tab Switching Behavior:**
1. User clicks tab button → `switchTab('entities')` called
2. `activeTab` state updated → triggers Alpine reactivity
3. URL hash updated → `window.location.hash = 'entities'`
4. If entities not loaded → `loadEntities()` called (lazy loading)
5. View toggles via `x-show="activeTab === 'entities'"` directive

#### 3.2.2 Entity Filters Bar

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html:865-950`

```html
<div class="mb-6 space-y-4">
  <!-- Entity Type Filter -->
  <div class="flex flex-wrap items-center gap-2">
    <span class="text-sm font-medium">Type:</span>

    <button
      @click="entityTypeFilter = 'all'; applyEntityFilters()"
      :class="entityTypeFilter === 'all' ? 'btn-active' : 'btn-inactive'"
    >
      All ({{ entityStats.total }})
    </button>

    <button
      @click="entityTypeFilter = 'file'; applyEntityFilters()"
      :class="entityTypeFilter === 'file' ? 'btn-active' : 'btn-inactive'"
    >
      Files ({{ entityStats.by_type.file }})
    </button>

    <button
      @click="entityTypeFilter = 'other'; applyEntityFilters()"
      :class="entityTypeFilter === 'other' ? 'btn-active' : 'btn-inactive'"
    >
      Other ({{ entityStats.by_type.other }})
    </button>
  </div>

  <!-- Tag Filter (Multi-Select) -->
  <div class="flex items-center gap-2">
    <label class="text-sm font-medium">Tags:</label>

    <div x-data="{ open: false }" class="relative">
      <button @click="open = !open" class="dropdown-trigger">
        {{ entitySelectedTags.length > 0 ? entitySelectedTags.join(', ') : 'All tags' }}
      </button>

      <!-- Dropdown menu -->
      <div x-show="open" @click.away="open = false" class="dropdown-menu">
        <template x-for="tagInfo in entityStats.top_tags" :key="tagInfo.tag">
          <label class="checkbox-item">
            <input
              type="checkbox"
              :value="tagInfo.tag"
              x-model="entitySelectedTags"
              @change="applyEntityFilters()"
            />
            <span>{{ tagInfo.tag }} ({{ tagInfo.count }})</span>
          </label>
        </template>
      </div>
    </div>
  </div>

  <!-- Search Input -->
  <div class="flex items-center gap-2">
    <label class="text-sm font-medium">Search:</label>
    <input
      type="text"
      x-model.debounce.300ms="entitySearchQuery"
      @input="applyEntityFilters()"
      placeholder="Search by name, identifier, or description..."
      class="search-input"
    />
  </div>

  <!-- Sort Dropdown -->
  <div class="flex items-center gap-2">
    <label class="text-sm font-medium">Sort:</label>
    <select x-model="entitySortBy" @change="applyEntityFilters()">
      <option value="name_asc">Name (A-Z)</option>
      <option value="name_desc">Name (Z-A)</option>
      <option value="type_asc">Type</option>
      <option value="created_desc">Recently Created</option>
    </select>
  </div>
</div>
```

**Filter Logic:**
1. **Type Filter:** Buttons toggle `entityTypeFilter` state → `applyEntityFilters()` runs
2. **Tag Filter:** Multi-select checkboxes update `entitySelectedTags[]` array → filter runs
3. **Search:** Debounced input (300ms) updates `entitySearchQuery` → filter runs
4. **Sort:** Dropdown changes `entitySortBy` → `sortEntities()` runs

#### 3.2.3 Entity Cards Grid

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html:980-1120`

```html
<!-- Entity Cards Grid (3-column responsive) -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
  <template x-for="entity in filteredEntities" :key="entity.id">
    <div
      @click="openEntityDetail(entity)"
      class="entity-card bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer p-4 border border-gray-200 dark:border-gray-700"
    >
      <!-- Header: Type Badge + Name -->
      <div class="flex items-start justify-between mb-2">
        <!-- Entity Type Badge -->
        <span
          class="px-2.5 py-0.5 rounded-full text-xs font-medium"
          :class="{
            'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300': entity.entity_type === 'file',
            'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-300': entity.entity_type === 'other'
          }"
          x-text="entity.entity_type === 'file' ? 'File' : 'Other'"
        ></span>
      </div>

      <!-- Entity Name (Title) -->
      <h3 class="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">
        <span x-text="entity.name"></span>
      </h3>

      <!-- Identifier (if present) -->
      <p
        x-show="entity.identifier"
        class="text-sm text-gray-600 dark:text-gray-400 font-mono truncate mb-2"
        x-text="entity.identifier"
      ></p>

      <!-- Description (truncated) -->
      <p
        x-show="entity.description"
        class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3"
        x-text="entity.description"
      ></p>

      <!-- Tags -->
      <div x-show="entity.tags" class="flex flex-wrap gap-1 mb-2">
        <template x-for="tag in (entity.tags || '').split(' ').filter(t => t)" :key="tag">
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
            <span x-text="tag"></span>
          </span>
        </template>
      </div>

      <!-- Footer: Created Date + Entity ID -->
      <div class="mt-3 flex items-center justify-between text-xs text-gray-500">
        <span x-text="formatRelativeTime(entity.created_at)"></span>
        <span>Entity #<span x-text="entity.id"></span></span>
      </div>
    </div>
  </template>
</div>
```

**Card Interaction:**
- Click card → `openEntityDetail(entity)` → Modal opens
- Tags are read-only (no click action in Phase 1)
- Hover effect via Tailwind `hover:shadow-lg`

#### 3.2.4 Entity Detail Modal

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html:1650-1750`

```html
<!-- Entity Detail Modal (full-screen overlay) -->
<div
  x-show="showEntityModal"
  x-cloak
  class="fixed inset-0 z-50 overflow-y-auto"
  @click.self="closeEntityModal()"
  @keydown.escape.window="closeEntityModal()"
>
  <div class="min-h-screen px-4 text-center">
    <!-- Modal Content -->
    <div class="inline-block w-full max-w-4xl my-8 text-left align-middle bg-white dark:bg-gray-800 rounded-lg shadow-xl">
      <!-- Header -->
      <div class="flex items-start justify-between p-6 border-b">
        <div class="flex-1">
          <h2 class="text-2xl font-bold" x-text="selectedEntity?.name"></h2>
          <p class="text-sm text-gray-500">
            Entity #<span x-text="selectedEntity?.id"></span>
          </p>
        </div>
        <button @click="closeEntityModal()" class="close-btn">×</button>
      </div>

      <!-- Body (Scrollable) -->
      <div class="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
        <!-- Entity Type Badge -->
        <div>
          <span class="badge" x-text="selectedEntity?.entity_type"></span>
        </div>

        <!-- Identifier -->
        <div x-show="selectedEntity?.identifier">
          <h3 class="text-sm font-medium text-gray-500">Identifier</h3>
          <p class="mt-1 font-mono text-sm bg-gray-50 dark:bg-gray-900 p-2 rounded">
            <span x-text="selectedEntity?.identifier"></span>
          </p>
        </div>

        <!-- Description -->
        <div x-show="selectedEntity?.description">
          <h3 class="text-sm font-medium text-gray-500">Description</h3>
          <p class="mt-1 text-sm whitespace-pre-wrap">
            <span x-text="selectedEntity?.description"></span>
          </p>
        </div>

        <!-- Metadata (JSON Pretty-Printed) -->
        <div x-show="selectedEntity?.metadata">
          <h3 class="text-sm font-medium text-gray-500">Metadata</h3>
          <pre class="mt-1 text-xs bg-gray-50 dark:bg-gray-900 p-3 rounded overflow-x-auto">
            <code x-text="formatEntityMetadata(selectedEntity?.metadata)"></code>
          </pre>
        </div>

        <!-- Tags -->
        <div x-show="selectedEntity?.tags">
          <h3 class="text-sm font-medium text-gray-500 mb-2">Tags</h3>
          <div class="flex flex-wrap gap-2">
            <template x-for="tag in (selectedEntity?.tags || '').split(' ').filter(t => t)" :key="tag">
              <span class="tag-badge" x-text="tag"></span>
            </template>
          </div>
        </div>

        <!-- Linked Tasks Section -->
        <div>
          <h3 class="text-sm font-medium text-gray-500 mb-3">
            Linked Tasks (<span x-text="entityTasks.length"></span>)
          </h3>

          <!-- Loading State -->
          <div x-show="loadingEntityTasks" class="text-center py-4">
            <svg class="animate-spin h-5 w-5 mx-auto text-blue-600">...</svg>
          </div>

          <!-- Task List -->
          <div x-show="!loadingEntityTasks && entityTasks.length > 0" class="space-y-2">
            <template x-for="task in entityTasks" :key="task.id">
              <div
                @click="openTaskFromEntity(task)"
                class="task-item p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <h4 class="font-medium text-sm" x-text="task.title"></h4>
                    <p class="text-xs text-gray-500">Task #<span x-text="task.id"></span></p>
                  </div>
                  <!-- Status + Priority Badges -->
                  <div class="flex items-center gap-2">
                    <span class="status-badge" x-text="task.status"></span>
                    <span class="priority-badge" x-text="task.priority"></span>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- Empty State -->
          <div x-show="!loadingEntityTasks && entityTasks.length === 0" class="text-center py-6">
            <p class="text-sm text-gray-500">No tasks linked to this entity</p>
          </div>
        </div>

        <!-- Timestamps -->
        <div class="pt-4 border-t text-xs text-gray-500 space-y-1">
          <p>Created: <span x-text="formatDateTime(selectedEntity?.created_at)"></span></p>
          <p>Updated: <span x-text="formatDateTime(selectedEntity?.updated_at)"></span></p>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t flex justify-between">
        <button @click="copyEntityDetails(selectedEntity)" class="btn-secondary">
          Copy Details
        </button>
        <button @click="closeEntityModal()" class="btn-primary">
          Close
        </button>
      </div>
    </div>
  </div>
</div>
```

**Modal Features:**
- **Click outside to close:** `@click.self="closeEntityModal()"`
- **Escape key to close:** `@keydown.escape.window`
- **Linked tasks clickable:** Opens task detail modal (switches modals seamlessly)
- **Copy to clipboard:** `copyEntityDetails()` helper method

### 3.3 Event Handlers

```javascript
{
  // Format entity metadata (parse JSON and pretty-print)
  formatEntityMetadata(metadata) {
    if (!metadata) return '';
    try {
      const parsed = JSON.parse(metadata);
      return JSON.stringify(parsed, null, 2); // Pretty-print with 2-space indent
    } catch {
      return metadata; // Return raw if JSON parse fails
    }
  },

  // Copy entity details to clipboard
  async copyEntityDetails(entity) {
    if (!entity) return;

    const details = `Entity #${entity.id}: ${entity.name}
Type: ${entity.entity_type}
${entity.identifier ? `Identifier: ${entity.identifier}\n` : ''}
${entity.description ? `Description: ${entity.description}\n` : ''}
${entity.tags ? `Tags: ${entity.tags}\n` : ''}
Created: ${this.formatDateTime(entity.created_at)}`;

    try {
      await navigator.clipboard.writeText(details);
      this.showToast('Entity details copied to clipboard', 'success');
    } catch (err) {
      console.error('Failed to copy:', err);
      this.showToast('Failed to copy details', 'error');
    }
  },

  // Open task modal from entity modal (cross-modal navigation)
  openTaskFromEntity(task) {
    this.closeEntityModal();        // Close entity modal first
    setTimeout(() => {
      this.openTaskDetail(task);    // Open task modal after transition
    }, 100);                         // Small delay for smooth transition
  },
}
```

### 3.4 API Client Integration

All API calls use the Fetch API with consistent error handling:

```javascript
// Helper method for entity API calls
async function fetchEntityAPI(endpoint, params = {}) {
  const queryString = new URLSearchParams({
    project_id: this.currentProject.id,
    ...params
  }).toString();

  const response = await fetch(
    `${API_CONFIG.baseUrl}${endpoint}?${queryString}`,
    {
      headers: {
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json'
      }
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}
```

**Usage Pattern:**
```javascript
// Load entities
const data = await this.fetchEntityAPI('/api/entities', {
  entity_type: 'file',
  limit: 50,
  offset: 0
});
this.entities = data.entities;

// Search entities
const results = await this.fetchEntityAPI('/api/entities/search', {
  q: 'vendor',
  limit: 20
});
this.entities = results.entities;

// Get entity tasks
const tasks = await this.fetchEntityAPI(`/api/entities/${entityId}/tasks`, {
  status: 'in_progress'
});
this.entityTasks = tasks.tasks;
```

---

## 4. Data Flow Diagrams

### 4.1 Entity List Loading Flow

```
┌────────────────────────────────────────────────────────────────┐
│ 1. User Action: Click "Entities" Tab                          │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. Alpine.js: switchTab('entities')                           │
│    - Set activeTab = 'entities'                               │
│    - Update URL hash: #entities                               │
│    - Check if entities loaded                                 │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼ (if entities.length === 0)
┌────────────────────────────────────────────────────────────────┐
│ 3. Alpine.js: loadEntities()                                  │
│    - Set loadingEntities = true                               │
│    - Clear entityError                                        │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 4. Frontend: fetch('/api/entities?project_id=...')            │
│    - Include X-API-Key header                                 │
│    - Send GET request to FastAPI backend                      │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 5. FastAPI: list_entities() endpoint                          │
│    - Verify API key (401 if invalid)                          │
│    - Resolve workspace path via workspace_resolver            │
│    - Build MCP args with workspace_path                       │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 6. MCP Client: call_tool("list_entities", args)               │
│    - Direct import call to task-mcp FastMCP server            │
│    - No network protocol overhead                             │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 7. task-mcp: list_entities() tool                             │
│    - Query project SQLite database                            │
│    - Filter by entity_type/tags if provided                   │
│    - Return list of entity dicts                              │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 8. FastAPI: Process response                                  │
│    - Apply pagination (offset/limit)                          │
│    - Wrap in EntityListResponse Pydantic model                │
│    - Return JSON to frontend                                  │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 9. Alpine.js: Handle response                                 │
│    - Set entities = data.entities                             │
│    - Call loadEntityStats() in parallel                       │
│    - Call applyEntityFilters()                                │
│    - Set loadingEntities = false                              │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 10. Alpine.js: applyEntityFilters()                           │
│    - Filter by entity type (all/file/other)                   │
│    - Filter by selected tags (if any)                         │
│    - Filter by search query (if any)                          │
│    - Sort by entitySortBy (name/type/date)                    │
│    - Set filteredEntities = result                            │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 11. Alpine.js: Reactive render                                │
│    - x-show="activeTab === 'entities'" becomes true           │
│    - x-for iterates over filteredEntities                     │
│    - Entity cards rendered to DOM                             │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Entity Search Flow

```
┌────────────────────────────────────────────────────────────────┐
│ 1. User Action: Type in search input                          │
│    "vendor ABC"                                                │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. Alpine.js: x-model.debounce.300ms="entitySearchQuery"      │
│    - Wait 300ms after last keystroke                          │
│    - Update entitySearchQuery = "vendor ABC"                  │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. Alpine.js: @input="applyEntityFilters()"                   │
│    - Trigger filter re-application                            │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 4. Alpine.js: applyEntityFilters()                            │
│    - Get current entities list                                │
│    - Filter by entitySearchQuery:                             │
│      • Check entity.name.includes("vendor ABC")               │
│      • Check entity.identifier.includes("vendor ABC")         │
│      • Check entity.description.includes("vendor ABC")        │
│    - Return matching entities                                 │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ 5. Alpine.js: Update filteredEntities                         │
│    - filteredEntities = [matches]                             │
│    - Reactive render updates DOM                              │
└────────────────────────────────────────────────────────────────┘
```

**Note:** Search is client-side filtering (no API call). For server-side search, use `/api/entities/search` endpoint.

### 4.3 Filter Application Flow

```
┌────────────────────────────────────────────────────────────────┐
│ User Action: Change filter                                    │
│ (Type, Tag, Search, or Sort)                                  │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ Alpine.js: Update state variable                              │
│ - entityTypeFilter = 'file'         (type button click)       │
│ - entitySelectedTags += ['vendor']  (tag checkbox change)     │
│ - entitySearchQuery = 'ABC'         (search input change)     │
│ - entitySortBy = 'name_desc'        (sort dropdown change)    │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ Alpine.js: applyEntityFilters()                               │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Step 1: Start with all entities                          │ │
│ │   let filtered = [...this.entities]                      │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Step 2: Filter by entity type                            │ │
│ │   if (entityTypeFilter !== 'all')                        │ │
│ │     filtered = filtered.filter(e =>                      │ │
│ │       e.entity_type === entityTypeFilter)                │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Step 3: Filter by tags (multi-select)                    │ │
│ │   if (entitySelectedTags.length > 0)                     │ │
│ │     filtered = filtered.filter(entity =>                 │ │
│ │       entitySelectedTags.some(tag =>                     │ │
│ │         entity.tags.includes(tag)))                      │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Step 4: Filter by search query                           │ │
│ │   if (entitySearchQuery)                                 │ │
│ │     filtered = filtered.filter(e =>                      │ │
│ │       e.name.includes(query) ||                          │ │
│ │       e.identifier.includes(query) ||                    │ │
│ │       e.description.includes(query))                     │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Step 5: Sort results                                     │ │
│ │   filtered = this.sortEntities(filtered)                 │ │
│ │     (Sort by name/type/date, asc/desc)                   │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Step 6: Update filteredEntities                          │ │
│ │   this.filteredEntities = filtered                       │ │
│ └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ Alpine.js: Reactive Render                                    │
│ - x-for="entity in filteredEntities" re-renders              │
│ - Card grid updates with filtered results                    │
└────────────────────────────────────────────────────────────────┘
```

### 4.4 Modal Interaction Flow

```
┌────────────────────────────────────────────────────────────────┐
│ User Action: Click entity card                                │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ Alpine.js: @click="openEntityDetail(entity)"                  │
│ - Set selectedEntity = entity                                 │
│ - Set showEntityModal = true                                  │
│ - Set loadingEntityTasks = true                               │
│ - Clear entityTasks = []                                      │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ Alpine.js: x-show="showEntityModal" triggers                  │
│ - Modal overlay appears                                       │
│ - Modal content rendered with selectedEntity data             │
│ - Loading spinner shown in "Linked Tasks" section             │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼ (parallel async request)
┌────────────────────────────────────────────────────────────────┐
│ Alpine.js: Fetch linked tasks                                 │
│ fetch('/api/entities/{entity.id}/tasks')                      │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ FastAPI: get_entity_tasks() endpoint                          │
│ - Call MCP get_entity_tasks tool                              │
│ - Return TaskListResponse                                     │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ Alpine.js: Handle response                                    │
│ - Set entityTasks = data.tasks                                │
│ - Set loadingEntityTasks = false                              │
│ - Tasks rendered in modal                                     │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼ (user interaction)
┌────────────────────────────────────────────────────────────────┐
│ User Action: Click linked task                                │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ Alpine.js: openTaskFromEntity(task)                           │
│ - Close entity modal: closeEntityModal()                      │
│ - Wait 100ms (transition delay)                               │
│ - Open task modal: openTaskDetail(task)                       │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│ Task detail modal now open (cross-modal navigation)           │
└────────────────────────────────────────────────────────────────┘
```

---

## 5. API Integration Pattern

### 5.1 MCP Tool Call Pattern

**Standard pattern used across all entity endpoints:**

```python
# Step 1: Authenticate
await verify_api_key(x_api_key)  # Raises 401 if invalid

# Step 2: Resolve workspace path
resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)
# Returns absolute workspace path from project_id hash or explicit path

# Step 3: Build MCP arguments
args: dict[str, Any] = {"workspace_path": resolved_workspace}
if entity_type:
    args["entity_type"] = entity_type
if tags:
    args["tags"] = tags
# CRITICAL: workspace_path is REQUIRED (v0.4.0+)

# Step 4: Call MCP tool
try:
    result = await mcp_service.call_tool("list_entities", args)
except Exception as e:
    logger.error(f"MCP tool failed: {e}", exc_info=True)
    raise RuntimeError(f"Failed to call MCP tool: {e}")

# Step 5: Process and validate response
entities = [EntityResponse(**entity) for entity in result]
# Pydantic validation ensures type safety

# Step 6: Return response
return EntityListResponse(
    entities=entities,
    total=len(entities),
    limit=limit,
    offset=offset
)
```

### 5.2 Workspace Resolution

**Workspace resolver handles project_id → workspace_path mapping:**

```python
# Initialize workspace resolver at startup
await workspace_resolver.initialize(mcp_service)
# Loads all projects from master.db via MCP list_projects tool

# In endpoint: Resolve workspace
resolved_workspace = workspace_resolver.resolve(
    project_id="a1b2c3d4",        # Optional: Project hash ID
    workspace_path=None            # Optional: Explicit workspace path
)
# Returns: "/Users/user/projects/my-project"

# Resolution logic:
# 1. If workspace_path provided → validate and return it
# 2. If project_id provided → lookup workspace_path from cache
# 3. If both provided → prefer workspace_path, validate project_id matches
# 4. If neither provided → raise ValueError
```

**Workspace Resolver Implementation:**

```python
class WorkspaceResolver:
    def __init__(self):
        self._projects: dict[str, str] = {}  # {project_id: workspace_path}

    async def initialize(self, mcp_service):
        """Load all projects at startup."""
        projects = await mcp_service.call_tool("list_projects", {})
        for project in projects:
            self._projects[project["id"]] = project["workspace_path"]

    def resolve(
        self,
        project_id: Optional[str] = None,
        workspace_path: Optional[str] = None
    ) -> str:
        """Resolve workspace path from project_id or explicit path."""
        if workspace_path:
            return workspace_path  # Explicit path always takes precedence

        if project_id:
            if project_id not in self._projects:
                raise ValueError(f"Unknown project ID: {project_id}")
            return self._projects[project_id]

        raise ValueError("Must provide either project_id or workspace_path")
```

### 5.3 Error Handling Pattern

**Exception → HTTP Status Code Mapping:**

```python
# Exception Handlers (main.py:142-174)

@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """
    Handle ValueError → 400 or 404

    Examples:
    - "Entity with ID 999 not found" → 404
    - "Invalid entity_type: foo" → 400
    - "workspace_path is REQUIRED" → 400
    """
    error_msg = str(exc)
    if "not found" in error_msg.lower():
        status_code = 404
    else:
        status_code = 400

    return JSONResponse(
        status_code=status_code,
        content={"error": "ValueError", "message": error_msg}
    )

@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc: RuntimeError):
    """
    Handle RuntimeError → 500

    Examples:
    - MCP tool call failures
    - Database connection errors
    - Unexpected internal errors
    """
    logger.error(f"Runtime error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "RuntimeError", "message": str(exc)}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """
    Handle HTTPException → Custom status code

    Examples:
    - 401 Unauthorized (invalid API key)
    - 403 Forbidden
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTPException", "message": exc.detail}
    )
```

**Endpoint Error Handling:**

```python
@app.get("/api/entities/{entity_id}")
async def get_entity(entity_id: int, ...):
    try:
        # Authenticate
        await verify_api_key(x_api_key)  # Raises HTTPException(401) if invalid

        # Resolve workspace
        resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)
        # Raises ValueError if project_id invalid

        # Call MCP tool
        entity_data = await mcp_service.call_tool(
            "get_entity",
            {"entity_id": entity_id, "workspace_path": resolved_workspace}
        )
        # MCP tool raises ValueError if entity not found

        if not entity_data:
            raise ValueError(f"Entity with ID {entity_id} not found or deleted")

        # Validate with Pydantic
        return EntityResponse(**entity_data)
        # Raises ValidationError if data invalid (caught by default handler → 422)

    except ValueError as e:
        # Caught by value_error_handler → 404 or 400
        raise

    except Exception as e:
        # Unexpected error → log and convert to RuntimeError
        logger.error(f"Failed to fetch entity {entity_id}: {e}", exc_info=True)
        raise RuntimeError(f"Failed to fetch entity: {e}")
```

---

## 6. State Management

### 6.1 Alpine.js Reactivity Model

Alpine.js uses a reactive data model where state changes automatically trigger DOM updates.

**Reactivity Flow:**

```javascript
// 1. Define reactive state in x-data
function taskViewer() {
  return {
    entities: [],           // ← Reactive state
    filteredEntities: [],   // ← Derived state
    entityTypeFilter: 'all' // ← Filter state
  }
}

// 2. Bind state to DOM elements
<div x-data="taskViewer()">
  <!-- Reactive binding: Updates when entityTypeFilter changes -->
  <button
    @click="entityTypeFilter = 'file'"
    :class="{ active: entityTypeFilter === 'file' }"
  >
    Files
  </button>

  <!-- Reactive rendering: Re-renders when filteredEntities changes -->
  <template x-for="entity in filteredEntities" :key="entity.id">
    <div x-text="entity.name"></div>
  </template>
</div>

// 3. Update state programmatically
this.entityTypeFilter = 'other';  // ← DOM auto-updates

// 4. Derived state updates
this.applyEntityFilters();  // ← Updates filteredEntities
// ← DOM automatically re-renders entity cards
```

### 6.2 State Synchronization

**Tab State Persistence:**

```javascript
// On tab switch: Update URL hash
switchTab(tab) {
  this.activeTab = tab;
  window.location.hash = tab;  // Persist in URL
}

// On page load/hash change: Restore tab
init() {
  window.addEventListener('hashchange', () => this.handleHashChange());
  this.handleHashChange();  // Initial restore
}

handleHashChange() {
  const hash = window.location.hash.slice(1);
  if (hash === 'entities') {
    this.activeTab = 'entities';
  } else {
    this.activeTab = 'tasks';
  }
}
```

**Filter State Reset on Project Switch:**

```javascript
async selectProject(project) {
  this.currentProject = project;

  // Clear entity state
  this.entities = [];
  this.filteredEntities = [];
  this.entityStats = { total: 0, by_type: { file: 0, other: 0 }, top_tags: [] };

  // Reset filters to defaults
  this.entityTypeFilter = 'all';
  this.entitySearchQuery = '';
  this.entitySelectedTags = [];
  this.entitySortBy = 'name_asc';

  // Reload current tab
  if (this.activeTab === 'entities') {
    await this.loadEntities();
  }
}
```

### 6.3 Loading States

**Three-State Loading Pattern:**

```javascript
{
  // State 1: Initial (not loaded)
  entities: [],
  loadingEntities: false,

  // State 2: Loading
  async loadEntities() {
    this.loadingEntities = true;  // ← Trigger loading UI
    this.entityError = null;

    try {
      const data = await fetch(...);
      this.entities = data.entities;
      // ← State 3: Loaded successfully
    } catch (err) {
      this.entityError = err.message;
      // ← State 3: Loaded with error
    } finally {
      this.loadingEntities = false;  // ← Exit loading state
    }
  }
}
```

**Loading UI Templates:**

```html
<!-- Loading State (skeleton) -->
<div x-show="loadingEntities" class="space-y-4">
  <div class="skeleton h-32 bg-gray-200 rounded-lg"></div>
  <div class="skeleton h-32 bg-gray-200 rounded-lg"></div>
</div>

<!-- Error State -->
<div x-show="entityError && !loadingEntities" class="alert alert-error">
  <span x-text="entityError"></span>
</div>

<!-- Success State (data) -->
<div x-show="!loadingEntities && !entityError && filteredEntities.length > 0">
  <!-- Entity cards -->
</div>

<!-- Empty State (no data) -->
<div x-show="!loadingEntities && !entityError && filteredEntities.length === 0">
  <p>No entities found</p>
</div>
```

### 6.4 Cross-Component Communication

**Entity Modal ↔ Task Modal Navigation:**

```javascript
// From entity modal: Open task detail
openTaskFromEntity(task) {
  // 1. Close entity modal
  this.closeEntityModal();

  // 2. Wait for close transition
  setTimeout(() => {
    // 3. Open task modal
    this.openTaskDetail(task);
  }, 100);  // 100ms delay matches CSS transition
}

// From task modal: Open entity detail (hypothetical)
openEntityFromTask(entity) {
  this.closeTaskModal();
  setTimeout(() => {
    this.openEntityDetail(entity);
  }, 100);
}
```

**Shared State Between Tabs:**

```javascript
{
  // Shared across tabs
  currentProject: null,   // Currently selected project
  apiKey: '',             // API key for authentication

  // Tab-specific state (isolated)
  tasks: [],              // Only used in tasks tab
  entities: [],           // Only used in entities tab

  // Tab switching doesn't lose data
  switchTab(tab) {
    this.activeTab = tab;
    // Tasks remain in this.tasks
    // Entities remain in this.entities
  }
}
```

---

## 7. Extension Points

### 7.1 Adding New Entity Types

**Current:** Only `file` and `other` are supported.

**To add a new type (e.g., `vendor`):**

1. **Backend:** Add validation in Pydantic model (optional)
   ```python
   # models.py
   class EntityResponse(BaseModel):
       entity_type: Literal["file", "other", "vendor"]  # Add "vendor"
   ```

2. **Frontend:** Add type filter button
   ```html
   <!-- Filter bar -->
   <button
     @click="entityTypeFilter = 'vendor'; applyEntityFilters()"
     :class="entityTypeFilter === 'vendor' ? 'btn-active' : 'btn-inactive'"
   >
     Vendors ({{ entityStats.by_type.vendor || 0 }})
   </button>
   ```

3. **Frontend:** Add type badge styling
   ```html
   <!-- Entity card -->
   <span
     class="badge"
     :class="{
       'bg-purple-100 text-purple-800': entity.entity_type === 'file',
       'bg-cyan-100 text-cyan-800': entity.entity_type === 'other',
       'bg-green-100 text-green-800': entity.entity_type === 'vendor'
     }"
     x-text="entity.entity_type"
   ></span>
   ```

4. **Backend:** Update stats aggregation
   ```python
   # main.py: get_entity_stats()
   type_counts = {"file": 0, "other": 0, "vendor": 0}  # Add vendor
   ```

**Note:** No database migration needed (entity_type is free-form string).

### 7.2 Adding New Filters

**Example: Add "Created Date" Range Filter**

1. **Add state variables:**
   ```javascript
   {
     entityDateFilter: 'all',  // 'all' | 'today' | 'week' | 'month'
   }
   ```

2. **Add filter UI:**
   ```html
   <div class="flex items-center gap-2">
     <span class="text-sm font-medium">Created:</span>
     <button @click="entityDateFilter = 'today'; applyEntityFilters()">Today</button>
     <button @click="entityDateFilter = 'week'; applyEntityFilters()">This Week</button>
     <button @click="entityDateFilter = 'month'; applyEntityFilters()">This Month</button>
   </div>
   ```

3. **Update filter logic:**
   ```javascript
   applyEntityFilters() {
     let filtered = [...this.entities];

     // Existing filters...

     // Date filter
     if (this.entityDateFilter !== 'all') {
       const now = new Date();
       const ranges = {
         today: 24 * 60 * 60 * 1000,
         week: 7 * 24 * 60 * 60 * 1000,
         month: 30 * 24 * 60 * 60 * 1000
       };
       const cutoff = new Date(now - ranges[this.entityDateFilter]);

       filtered = filtered.filter(e =>
         new Date(e.created_at) >= cutoff
       );
     }

     this.filteredEntities = filtered;
   }
   ```

### 7.3 Extending Metadata Display

**Current:** Metadata displayed as raw JSON pretty-printed.

**Enhancement: Render vendor-specific metadata:**

1. **Add metadata parser:**
   ```javascript
   parseVendorMetadata(entity) {
     if (entity.entity_type !== 'other') return null;

     try {
       const metadata = JSON.parse(entity.metadata);
       if (metadata.vendor_code) {
         return {
           type: 'vendor',
           code: metadata.vendor_code,
           phase: metadata.phase,
           formats: metadata.formats || [],
           brands: metadata.brands || []
         };
       }
     } catch {
       return null;
     }
   }
   ```

2. **Add custom metadata display:**
   ```html
   <!-- In entity modal -->
   <div x-show="parseVendorMetadata(selectedEntity)">
     <h3 class="text-sm font-medium">Vendor Details</h3>
     <dl class="mt-2 space-y-1 text-sm">
       <dt class="font-medium">Vendor Code:</dt>
       <dd x-text="parseVendorMetadata(selectedEntity)?.code"></dd>

       <dt class="font-medium">Phase:</dt>
       <dd x-text="parseVendorMetadata(selectedEntity)?.phase"></dd>

       <dt class="font-medium">Supported Formats:</dt>
       <dd>
         <template x-for="fmt in parseVendorMetadata(selectedEntity)?.formats">
           <span class="badge" x-text="fmt"></span>
         </template>
       </dd>
     </dl>
   </div>
   ```

### 7.4 Custom Entity Actions

**Example: Add "View in File System" action for file entities**

1. **Add action button to entity modal:**
   ```html
   <!-- Modal footer -->
   <div class="px-6 py-4 border-t flex justify-between">
     <!-- Existing buttons... -->

     <button
       x-show="selectedEntity?.entity_type === 'file'"
       @click="openFileInSystem(selectedEntity)"
       class="btn-secondary"
     >
       Open in Finder
     </button>
   </div>
   ```

2. **Implement action handler:**
   ```javascript
   openFileInSystem(entity) {
     if (!entity.identifier) {
       this.showToast('No file path available', 'error');
       return;
     }

     // Call backend endpoint to open file
     fetch(`${API_CONFIG.baseUrl}/api/files/open`, {
       method: 'POST',
       headers: {
         'X-API-Key': this.apiKey,
         'Content-Type': 'application/json'
       },
       body: JSON.stringify({ file_path: entity.identifier })
     })
     .then(() => this.showToast('Opening file...', 'success'))
     .catch(err => this.showToast('Failed to open file', 'error'));
   }
   ```

3. **Add backend endpoint:**
   ```python
   @app.post("/api/files/open")
   async def open_file(
       file_path: str,
       x_api_key: str = Header(None)
   ):
       await verify_api_key(x_api_key)

       import subprocess
       subprocess.run(["open", file_path])  # macOS
       # subprocess.run(["xdg-open", file_path])  # Linux

       return {"success": True}
   ```

---

## 8. Known Limitations

### 8.1 Stats Endpoint Route Ordering Issue

**Problem:** FastAPI route matching can conflict if parameterized routes come before specific routes.

**Example:**
```python
# ❌ WRONG ORDER: /{entity_id} matches before /stats
@app.get("/api/entities/{entity_id}")
async def get_entity(entity_id: int, ...): ...

@app.get("/api/entities/stats")  # ← Never reached! "stats" matches as entity_id
async def get_entity_stats(...): ...
```

**Solution:** Declare specific routes BEFORE parameterized routes.

```python
# ✅ CORRECT ORDER
@app.get("/api/entities/search")  # Specific route first
@app.get("/api/entities/stats")   # Specific route second
@app.get("/api/entities/{entity_id}/tasks")  # Nested route third
@app.get("/api/entities/{entity_id}")  # Parameterized route LAST
```

**Impact:** If routes are misordered, `/api/entities/stats` will return 404 or try to parse "stats" as an entity ID.

### 8.2 Pagination Requires Server-Side Support

**Current Implementation:** Pagination is client-side (all entities loaded, then sliced).

```python
# Backend: Load ALL entities
entities_data = await mcp_service.call_tool("list_entities", args)

# Backend: Slice for pagination (client-side)
paginated_entities = entities_data[offset : offset + limit]
```

**Limitation:** For projects with 1000+ entities, initial load is slow.

**Future Enhancement:** Add offset/limit support to MCP `list_entities` tool for true server-side pagination.

```python
# Ideal: Pass pagination to MCP tool
entities_data = await mcp_service.call_tool("list_entities", {
    "workspace_path": workspace,
    "limit": limit,
    "offset": offset  # ← Not currently supported
})
```

### 8.3 No Real-Time Updates

**Current:** Entities are loaded once on tab switch and cached.

**Limitation:** If entities are created/updated/deleted via Claude Code MCP tools, the entity viewer won't reflect changes until manual refresh.

**Workaround:** Add "Refresh" button to reload entities.

```html
<button @click="loadEntities()" class="btn-secondary">
  <svg class="refresh-icon">...</svg>
  Refresh Entities
</button>
```

**Future Enhancement:** Add WebSocket support or SSE (Server-Sent Events) for real-time updates.

### 8.4 No Entity CRUD from UI (Read-Only)

**Current:** Entity viewer is read-only. Users cannot:
- Create new entities
- Edit entity fields
- Delete entities
- Link/unlink entities to tasks

**Rationale:** Phase 1 focuses on viewing. Entity creation is the domain of Claude Code MCP tools.

**Future Enhancement (Phase 2):** Add "Create Entity" modal, edit forms, delete confirmations, etc.

### 8.5 Client-Side Search (No Full-Text Index)

**Current:** Search is client-side filtering (JavaScript `.includes()` on name/identifier/description).

**Limitation:**
- No regex support
- No fuzzy matching
- No stemming/lemmatization
- Case-insensitive but exact substring match only

**Backend Search Alternative:** Use `/api/entities/search` endpoint for server-side full-text search via MCP tool.

```javascript
// Client-side search (current)
const filtered = entities.filter(e =>
  e.name.toLowerCase().includes(query.toLowerCase())
);

// Server-side search (available via API)
const response = await fetch('/api/entities/search?q=ABC&limit=20');
const { entities } = await response.json();
```

**Recommendation:** Use server-side search for large datasets (100+ entities).

### 8.6 No Bulk Operations

**Current:** No support for:
- Bulk tag assignment
- Bulk delete
- Bulk export (CSV/JSON)

**Future Enhancement:** Add checkbox selection and bulk action bar.

---

## 9. Future Enhancements

### 9.1 Entity Creation/Editing UI

**Goal:** Allow users to create and edit entities from the web interface.

**Design:**

1. **Add "Create Entity" button:**
   ```html
   <button @click="openCreateEntityModal()" class="btn-primary">
     + Create Entity
   </button>
   ```

2. **Create entity form modal:**
   ```html
   <div x-show="showCreateEntityModal">
     <form @submit.prevent="submitCreateEntity()">
       <select x-model="newEntity.entity_type" required>
         <option value="file">File</option>
         <option value="other">Other</option>
       </select>

       <input x-model="newEntity.name" placeholder="Entity name" required />
       <input x-model="newEntity.identifier" placeholder="Identifier (optional)" />
       <textarea x-model="newEntity.description" placeholder="Description"></textarea>
       <input x-model="newEntity.tags" placeholder="Tags (space-separated)" />

       <button type="submit">Create Entity</button>
     </form>
   </div>
   ```

3. **Add backend POST endpoint:**
   ```python
   @app.post("/api/entities", response_model=EntityResponse)
   async def create_entity(
       entity_data: CreateEntityRequest,
       x_api_key: str = Header(None),
       ...
   ):
       await verify_api_key(x_api_key)

       result = await mcp_service.call_tool("create_entity", {
           "workspace_path": resolved_workspace,
           "entity_type": entity_data.entity_type,
           "name": entity_data.name,
           "identifier": entity_data.identifier,
           ...
       })

       return EntityResponse(**result)
   ```

### 9.2 Real-Time Entity Updates

**Goal:** Auto-refresh entity list when changes occur in the database.

**Approaches:**

1. **WebSocket Connection:**
   ```python
   # Backend: WebSocket endpoint
   @app.websocket("/ws/entities")
   async def entity_websocket(websocket: WebSocket):
       await websocket.accept()
       # Send updates when entities change
       while True:
           await websocket.send_json({"event": "entity_created", "entity": {...}})
   ```

2. **Server-Sent Events (SSE):**
   ```python
   # Backend: SSE endpoint
   @app.get("/api/entities/events")
   async def entity_events(x_api_key: str = Header(None)):
       async def event_generator():
           while True:
               yield f"data: {json.dumps({...})}\n\n"
               await asyncio.sleep(5)

       return StreamingResponse(event_generator(), media_type="text/event-stream")
   ```

3. **Polling (Simple but Inefficient):**
   ```javascript
   // Frontend: Poll every 30 seconds
   setInterval(() => {
     if (this.activeTab === 'entities') {
       this.loadEntities();
     }
   }, 30000);
   ```

**Recommendation:** Use SSE for simplicity (no WebSocket server config needed).

### 9.3 Advanced Search Operators

**Goal:** Support advanced search syntax like:
- `type:file` → Filter by entity type
- `tag:vendor` → Filter by tag
- `created:>2025-11-01` → Date range
- `name:"ABC Insurance"` → Exact phrase match

**Implementation:**

1. **Parse search query:**
   ```javascript
   parseSearchQuery(query) {
     const filters = {
       text: '',
       type: null,
       tags: [],
       dateRange: null
     };

     // Parse operators
     const typeMatch = query.match(/type:(\w+)/);
     if (typeMatch) filters.type = typeMatch[1];

     const tagMatches = query.match(/tag:(\w+)/g);
     if (tagMatches) filters.tags = tagMatches.map(t => t.replace('tag:', ''));

     // Extract plain text (remove operators)
     filters.text = query.replace(/\w+:\S+/g, '').trim();

     return filters;
   }
   ```

2. **Apply advanced filters:**
   ```javascript
   applyAdvancedSearch() {
     const filters = this.parseSearchQuery(this.entitySearchQuery);

     let filtered = [...this.entities];

     if (filters.type) {
       filtered = filtered.filter(e => e.entity_type === filters.type);
     }

     if (filters.tags.length > 0) {
       filtered = filtered.filter(e =>
         filters.tags.some(tag => e.tags.includes(tag))
       );
     }

     if (filters.text) {
       filtered = filtered.filter(e =>
         e.name.includes(filters.text) || e.identifier.includes(filters.text)
       );
     }

     this.filteredEntities = filtered;
   }
   ```

### 9.4 Bulk Operations

**Goal:** Enable users to select multiple entities and perform batch actions.

**Design:**

1. **Add checkbox to entity cards:**
   ```html
   <div class="entity-card">
     <input
       type="checkbox"
       :value="entity.id"
       x-model="selectedEntityIds"
       class="absolute top-2 left-2"
     />
     <!-- Rest of card -->
   </div>
   ```

2. **Add bulk action bar:**
   ```html
   <div x-show="selectedEntityIds.length > 0" class="bulk-action-bar">
     <span>{{ selectedEntityIds.length }} selected</span>

     <button @click="bulkAddTag()">Add Tag</button>
     <button @click="bulkDelete()">Delete</button>
     <button @click="bulkExport()">Export</button>
   </div>
   ```

3. **Implement bulk actions:**
   ```javascript
   async bulkAddTag() {
     const tag = prompt('Enter tag to add:');
     if (!tag) return;

     for (const entityId of this.selectedEntityIds) {
       await fetch(`/api/entities/${entityId}`, {
         method: 'PATCH',
         body: JSON.stringify({ add_tag: tag }),
         ...
       });
     }

     this.loadEntities();  // Refresh
   }
   ```

### 9.5 Export Functionality

**Goal:** Export entities as CSV or JSON for external processing.

**Implementation:**

1. **Add export button:**
   ```html
   <button @click="exportEntities('csv')" class="btn-secondary">
     Export as CSV
   </button>
   ```

2. **Export method:**
   ```javascript
   exportEntities(format) {
     const data = this.filteredEntities;  // Export filtered results

     if (format === 'csv') {
       const csv = this.entitiesToCSV(data);
       this.downloadFile(csv, 'entities.csv', 'text/csv');
     } else if (format === 'json') {
       const json = JSON.stringify(data, null, 2);
       this.downloadFile(json, 'entities.json', 'application/json');
     }
   }

   entitiesToCSV(entities) {
     const headers = ['ID', 'Type', 'Name', 'Identifier', 'Tags', 'Created'];
     const rows = entities.map(e => [
       e.id,
       e.entity_type,
       e.name,
       e.identifier || '',
       e.tags || '',
       e.created_at
     ]);

     return [headers, ...rows]
       .map(row => row.map(cell => `"${cell}"`).join(','))
       .join('\n');
   }

   downloadFile(content, filename, mimeType) {
     const blob = new Blob([content], { type: mimeType });
     const url = URL.createObjectURL(blob);
     const a = document.createElement('a');
     a.href = url;
     a.download = filename;
     a.click();
     URL.revokeObjectURL(url);
   }
   ```

---

## Appendix A: File Locations

**Backend Files:**
- `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/main.py` (lines 637-903)
- `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/models.py` (lines 115-188)
- `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/mcp_client.py`
- `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/workspace_resolver.py`

**Frontend Files:**
- `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html` (lines 215-275, 857-1750)
- `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/js/config.js`

**Documentation:**
- `/Users/cliffclarke/Claude_Code/task-mcp/CLAUDE.md` (Entity System section)
- `/Users/cliffclarke/Claude_Code/task-mcp/docs/subagent-reports/plan/entity-viewer/`
- `/Users/cliffclarke/Claude_Code/task-mcp/docs/subagent-reports/architecture-review/entity-viewer/`

---

## Appendix B: Related Tasks

| Task ID | Title | Status | Description |
|---------|-------|--------|-------------|
| #69 | Enhancement #21: Entity Viewer for Projects | done | Parent task for entity viewer feature |
| #105 | Backend API endpoints (entity-viewer) | done | Implement 5 REST endpoints for entities |
| #106 | Frontend UI (entity-viewer) | done | Build Alpine.js entity viewer UI |
| #131 | Create developer implementation notes | in_progress | This document |

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Alpine.js** | Lightweight JavaScript framework for reactive UIs (alternative to Vue/React) |
| **Entity** | Typed object (file, vendor, etc.) that can be linked to tasks |
| **MCP** | Model Context Protocol - protocol for AI tool integration |
| **Pydantic** | Python data validation library using type hints |
| **FastAPI** | Modern async Python web framework |
| **WAL Mode** | Write-Ahead Logging - SQLite mode for concurrent reads |
| **Soft Delete** | Marking records as deleted (deleted_at timestamp) instead of hard deletion |
| **Junction Table** | Table linking two entities (task_entity_links) |
| **Reactive State** | Data that automatically triggers UI updates when changed |
| **Debounce** | Delay function execution until input stops (e.g., search input) |
| **Modal** | Overlay dialog box (e.g., entity detail view) |
| **Workspace** | Project directory containing tasks and entities |

---

**Document Metadata:**
- **Version:** 1.0.0
- **Last Updated:** 2025-11-02
- **Maintained By:** Claude Code Development Team
- **Related Documentation:** [CLAUDE.md](/Users/cliffclarke/Claude_Code/task-mcp/CLAUDE.md), [Entity System Docs](/Users/cliffclarke/Claude_Code/task-mcp/docs/entity-system-production-readiness.md)
