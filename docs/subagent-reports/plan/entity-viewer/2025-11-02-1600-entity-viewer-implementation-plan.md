# Entity Viewer Implementation Plan
**Task:** #69 - Entity Viewer for Projects  
**Created:** 2025-11-02 16:00  
**Author:** Claude Code Analysis Agent  
**Status:** Planning Phase

---

## Executive Summary

This plan outlines the implementation of an Entity Viewer feature for the task-viewer web application. The Entity Viewer will provide a comprehensive UI for viewing, filtering, and searching entities (files, vendors, etc.) and their relationships with tasks. The implementation will integrate seamlessly with the existing Vue.js/Alpine.js architecture while following established patterns from the current task viewer and usage stats implementations.

**Estimated Effort:** 12-16 hours across 3 phases  
**Risk Level:** Low (additive feature, existing patterns to follow)  
**Dependencies:** None (all MCP tools already exist)

---

## Table of Contents
1. [Architecture Analysis](#architecture-analysis)
2. [Component Design](#component-design)
3. [Backend API Endpoints](#backend-api-endpoints)
4. [Frontend Implementation](#frontend-implementation)
5. [Integration Plan](#integration-plan)
6. [Technical Challenges](#technical-challenges)
7. [Implementation Sequence](#implementation-sequence)
8. [Testing Strategy](#testing-strategy)
9. [Effort Estimates](#effort-estimates)

---

## 1. Architecture Analysis

### 1.1 Current Task Viewer Architecture

**Tech Stack:**
- **Backend:** FastAPI (Python 3.9+) with async/await
- **Frontend:** Alpine.js 3.x for reactivity (lightweight Vue alternative)
- **Styling:** Tailwind CSS 3.x via CDN
- **MCP Integration:** Direct import of task-mcp FastMCP server (no protocol overhead)
- **API Pattern:** RESTful JSON endpoints with Pydantic validation

**Key Files:**
```
task-viewer/
├── main.py                 # FastAPI backend (650 lines)
├── models.py              # Pydantic response models (113 lines)
├── mcp_client.py          # Direct MCP server access (172 lines)
├── workspace_resolver.py  # Project workspace resolution (177 lines)
└── static/
    ├── index.html         # Single-page Alpine.js app (1736 lines)
    └── js/config.js       # API configuration
```

**Current UI Pattern (Single-Page, No Tabs):**
- The existing task-viewer is a single-page application with NO tab system
- All filtering is done via dropdowns, buttons, and search on one page
- The "Usage Stats" mentioned in requirements doesn't exist as a separate tab
- Current layout: Header → Filters Bar → Task Cards Grid → Task Detail Modal

**Alpine.js State Management:**
```javascript
function taskViewer() {
  return {
    // State
    apiKey: API_CONFIG.getApiKey(),
    projects: [],
    currentProject: null,
    tasks: [],
    filteredTasks: [],
    selectedTask: null,
    
    // Filters
    statusFilter: 'all',
    priorityFilter: 'all',
    searchQuery: '',
    sortBy: 'priority_desc',
    
    // UI State
    loading: false,
    error: null,
    showModal: false,
    
    // Lifecycle
    async init() { ... },
    async loadProjects() { ... },
    async loadTasks() { ... },
    applyFilters() { ... }
  }
}
```

### 1.2 Available MCP Tools for Entities

**Entity CRUD Tools:**
1. `list_entities(workspace_path, entity_type?, tags?)` → List[Entity]
2. `get_entity(workspace_path, entity_id)` → Entity
3. `search_entities(workspace_path, search_term, entity_type?)` → List[Entity]

**Entity-Task Relationship Tools:**
4. `get_entity_tasks(workspace_path, entity_id, status?, priority?)` → List[Task]

**Entity Schema (from database.py):**
```python
{
  "id": int,
  "entity_type": "file" | "other",
  "name": str,                    # Display name
  "identifier": str | null,        # Unique ID (file path, vendor code)
  "description": str | null,       # Max 10k chars
  "metadata": str | null,          # JSON string
  "tags": str | null,              # Space-separated
  "created_by": str,               # Conversation ID
  "created_at": datetime,
  "updated_at": datetime,
  "deleted_at": datetime | null
}
```

### 1.3 Design Decision: Tab-Based Navigation

**Problem:** Adding entities to a single-page view would overcrowd the UI.

**Solution:** Implement tab-based navigation with 2 tabs:
1. **Tasks Tab** (default) - Current task viewer (keep all existing features)
2. **Entities Tab** - New entity viewer with similar filtering/search patterns

**Rationale:**
- Clean separation of concerns (tasks vs entities)
- Reuse existing filter/search UI patterns
- Room for future tabs (e.g., usage stats, project settings)
- Better UX for managing different data types

---

## 2. Component Design

### 2.1 Tab Navigation Component

**Location:** Below header, above filters bar

**HTML Structure:**
```html
<div class="sticky top-16 z-40 bg-white dark:bg-gray-900 border-b border-gray-200">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <nav class="flex space-x-8" role="tablist">
      <button
        @click="activeTab = 'tasks'"
        :class="activeTab === 'tasks' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500'"
        class="py-4 px-1 border-b-2 font-medium text-sm"
        role="tab"
      >
        Tasks
        <span class="ml-2 bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs">
          {{ statusCounts.total }}
        </span>
      </button>
      
      <button
        @click="activeTab = 'entities'; loadEntities()"
        :class="activeTab === 'entities' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500'"
        class="py-4 px-1 border-b-2 font-medium text-sm"
        role="tab"
      >
        Entities
        <span class="ml-2 bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs">
          {{ entityCounts.total }}
        </span>
      </button>
    </nav>
  </div>
</div>
```

**State Addition:**
```javascript
{
  activeTab: 'tasks',  // 'tasks' | 'entities'
  entityCounts: {
    total: 0,
    file: 0,
    other: 0
  }
}
```

### 2.2 Entity Filters Bar Component

**Similar to existing filters bar but adapted for entities:**

```html
<div x-show="activeTab === 'entities'" class="filters-bar">
  <!-- Entity Type Filter -->
  <div class="flex items-center gap-2">
    <span class="text-sm font-medium">Type:</span>
    <button @click="entityTypeFilter = 'all'">All ({{ entityCounts.total }})</button>
    <button @click="entityTypeFilter = 'file'">Files ({{ entityCounts.file }})</button>
    <button @click="entityTypeFilter = 'other'">Other ({{ entityCounts.other }})</button>
  </div>
  
  <!-- Tag Filter (reuse existing tag picker component) -->
  <div class="entity-tag-filter">
    <!-- Same dropdown pattern as task tag filter -->
  </div>
  
  <!-- Search Input -->
  <input
    type="text"
    x-model.debounce.300ms="entitySearchQuery"
    @input="applyEntityFilters()"
    placeholder="Search entities by name or identifier..."
  />
  
  <!-- Sort Dropdown -->
  <select x-model="entitySortBy" @change="applyEntityFilters()">
    <option value="name_asc">Name (A-Z)</option>
    <option value="name_desc">Name (Z-A)</option>
    <option value="created_desc">Recently Created</option>
    <option value="type_asc">Type</option>
  </select>
</div>
```

**State Addition:**
```javascript
{
  // Entity state
  entities: [],
  filteredEntities: [],
  selectedEntity: null,
  entityTags: [],
  
  // Entity filters
  entityTypeFilter: 'all',  // 'all' | 'file' | 'other'
  entitySearchQuery: '',
  entitySelectedTag: null,
  entitySortBy: 'name_asc',
  
  // Entity UI state
  loadingEntities: false,
  entityError: null,
  showEntityModal: false
}
```

### 2.3 Entity Cards Grid Component

**Layout:** Reuse existing card grid pattern (responsive 3-column)

```html
<div
  x-show="activeTab === 'entities' && !loadingEntities && !entityError"
  class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
>
  <template x-for="entity in filteredEntities" :key="entity.id">
    <div
      @click="openEntityDetail(entity)"
      class="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg p-4 border cursor-pointer"
    >
      <!-- Row 1: Entity Name (Title) -->
      <h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">
        <span x-text="entity.name"></span>
      </h3>
      
      <!-- Row 2: Identifier (if present) -->
      <p
        x-show="entity.identifier"
        class="mt-1 text-sm text-gray-600 dark:text-gray-400 font-mono truncate"
        x-text="entity.identifier"
      ></p>
      
      <!-- Row 3: Description (truncated) -->
      <p
        x-show="entity.description"
        class="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2"
        x-text="entity.description"
      ></p>
      
      <!-- Row 4: Type Badge -->
      <div class="mt-3 flex items-center gap-2">
        <span
          class="px-2.5 py-0.5 rounded-full text-xs font-medium"
          :class="{
            'bg-purple-100 text-purple-800': entity.entity_type === 'file',
            'bg-cyan-100 text-cyan-800': entity.entity_type === 'other'
          }"
          x-text="entity.entity_type === 'file' ? 'File' : 'Other'"
        ></span>
      </div>
      
      <!-- Row 5: Linked Tasks Count -->
      <div
        x-show="entityTaskCounts[entity.id]"
        class="mt-2 flex items-center gap-1 text-xs text-gray-500"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        <span x-text="`${entityTaskCounts[entity.id]} linked task${entityTaskCounts[entity.id] !== 1 ? 's' : ''}`"></span>
      </div>
      
      <!-- Row 6: Tags (if present) -->
      <div
        x-show="entity.tags"
        class="mt-2 flex flex-wrap gap-1"
      >
        <template x-for="tag in (entity.tags || '').split(' ').filter(t => t)" :key="tag">
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-700">
            <span x-text="tag"></span>
          </span>
        </template>
      </div>
      
      <!-- Metadata Row -->
      <div class="mt-3 flex items-center justify-between text-xs text-gray-500">
        <span x-text="formatRelativeTime(entity.created_at)"></span>
        <span>Entity #<span x-text="entity.id"></span></span>
      </div>
    </div>
  </template>
</div>
```

**State Addition:**
```javascript
{
  entityTaskCounts: {}  // { entityId: taskCount }
}
```

### 2.4 Entity Detail Modal Component

**Similar to existing task detail modal:**

```html
<div
  x-show="showEntityModal"
  x-cloak
  class="fixed inset-0 z-50 overflow-y-auto"
  @click.self="closeEntityModal()"
>
  <div class="min-h-screen px-4 text-center">
    <div class="inline-block w-full max-w-4xl my-8 text-left align-middle bg-white dark:bg-gray-800 rounded-lg shadow-xl">
      <!-- Header -->
      <div class="flex items-start justify-between p-6 border-b">
        <div class="flex-1">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
            <span x-text="selectedEntity?.name"></span>
          </h2>
          <p class="mt-1 text-sm text-gray-500">
            Entity #<span x-text="selectedEntity?.id"></span>
          </p>
        </div>
        <button @click="closeEntityModal()" class="text-gray-400 hover:text-gray-600">
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <!-- Body -->
      <div class="p-6 space-y-6">
        <!-- Type Badge -->
        <div>
          <span class="px-3 py-1 rounded-full text-sm font-medium">
            Type: <span x-text="selectedEntity?.entity_type"></span>
          </span>
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
          <p class="mt-1 text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
            <span x-text="selectedEntity?.description"></span>
          </p>
        </div>
        
        <!-- Metadata (if JSON) -->
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
              <span class="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm">
                <span x-text="tag"></span>
              </span>
            </template>
          </div>
        </div>
        
        <!-- Linked Tasks Section -->
        <div>
          <h3 class="text-sm font-medium text-gray-500 mb-3">
            Linked Tasks (<span x-text="entityTasks.length"></span>)
          </h3>
          
          <!-- Loading state -->
          <div x-show="loadingEntityTasks" class="text-center py-4">
            <svg class="animate-spin h-5 w-5 mx-auto text-blue-600">...</svg>
            <span class="text-sm text-gray-500">Loading linked tasks...</span>
          </div>
          
          <!-- Task list -->
          <div x-show="!loadingEntityTasks && entityTasks.length > 0" class="space-y-2">
            <template x-for="task in entityTasks" :key="task.id">
              <div
                @click="openTaskFromEntity(task)"
                class="p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <h4 class="font-medium text-sm text-gray-900 dark:text-gray-100">
                      <span x-text="task.title"></span>
                    </h4>
                    <p class="text-xs text-gray-500 mt-1">
                      Task #<span x-text="task.id"></span>
                    </p>
                  </div>
                  <div class="flex items-center gap-2 ml-4">
                    <span
                      class="px-2 py-1 rounded-full text-xs font-medium"
                      :class="getStatusBadgeClass(task.status)"
                      x-text="task.status"
                    ></span>
                    <span
                      class="px-2 py-1 rounded text-xs font-medium"
                      :class="getPriorityBadgeClass(task.priority)"
                      x-text="task.priority"
                    ></span>
                  </div>
                </div>
              </div>
            </template>
          </div>
          
          <!-- Empty state -->
          <div x-show="!loadingEntityTasks && entityTasks.length === 0" class="text-center py-6 text-gray-500">
            <svg class="h-8 w-8 mx-auto mb-2 text-gray-400">...</svg>
            <p class="text-sm">No tasks linked to this entity</p>
          </div>
        </div>
        
        <!-- Timestamps -->
        <div class="pt-4 border-t text-xs text-gray-500 space-y-1">
          <p>Created: <span x-text="formatDateTime(selectedEntity?.created_at)"></span></p>
          <p>Updated: <span x-text="formatDateTime(selectedEntity?.updated_at)"></span></p>
          <p x-show="selectedEntity?.created_by">
            By: <span x-text="selectedEntity?.created_by"></span>
          </p>
        </div>
      </div>
      
      <!-- Footer Actions -->
      <div class="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t flex justify-between">
        <button
          @click="copyEntityDetails(selectedEntity)"
          class="px-4 py-2 text-sm text-blue-600 hover:text-blue-700"
        >
          Copy Details
        </button>
        <button
          @click="closeEntityModal()"
          class="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300"
        >
          Close
        </button>
      </div>
    </div>
  </div>
</div>
```

**State Addition:**
```javascript
{
  entityTasks: [],           // Tasks linked to selected entity
  loadingEntityTasks: false  // Loading state for entity tasks
}
```

---

## 3. Backend API Endpoints

### 3.1 New FastAPI Endpoints

Add to `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/main.py`:

#### Endpoint 1: List Entities

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
    List entities with optional filtering.
    
    Query Parameters:
        - project_id: Filter by project hash ID
        - entity_type: Filter by type ('file' or 'other')
        - tags: Filter by tags (space-separated)
        - limit: Max results per page (default: 50, max: 100)
        - offset: Pagination offset (default: 0)
    
    Requires API key authentication.
    """
    await verify_api_key(x_api_key)
    
    # Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)
    
    # Build arguments for MCP call
    args: dict[str, Any] = {"workspace_path": resolved_workspace}
    if entity_type:
        args["entity_type"] = entity_type
    if tags:
        args["tags"] = tags
    
    # Call task-mcp
    entities_data = await mcp_service.call_tool("list_entities", args)
    
    # Apply pagination
    total = len(entities_data)
    paginated_entities = entities_data[offset : offset + limit]
    
    # Build meta counts
    meta = {
        "type_counts": {},
    }
    
    # Count by type
    for entity in entities_data:
        entity_type_val = entity.get("entity_type", "unknown")
        meta["type_counts"][entity_type_val] = (
            meta["type_counts"].get(entity_type_val, 0) + 1
        )
    
    return EntityListResponse(
        entities=[EntityResponse(**e) for e in paginated_entities],
        total=total,
        limit=limit,
        offset=offset,
        meta=meta,
    )
```

#### Endpoint 2: Get Entity by ID

```python
@app.get("/api/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: int,
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
):
    """
    Get a single entity by ID.
    
    Args:
        entity_id: Entity ID
        project_id: Optional project hint for workspace resolution
    
    Requires API key authentication.
    """
    await verify_api_key(x_api_key)
    
    # Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)
    
    # Call task-mcp
    entity_data = await mcp_service.call_tool(
        "get_entity", {"entity_id": entity_id, "workspace_path": resolved_workspace}
    )
    
    if not entity_data:
        raise ValueError(f"Entity with ID {entity_id} not found or deleted")
    
    return EntityResponse(**entity_data)
```

#### Endpoint 3: Search Entities

```python
@app.get("/api/entities/search", response_model=EntitySearchResponse)
async def search_entities(
    q: str,
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search entities by name or identifier (full-text search).
    
    Query Parameters:
        - q: Search query (required)
        - project_id: Filter by project
        - entity_type: Filter by type ('file' or 'other')
        - limit: Max results (default: 20, max: 100)
    
    Requires API key authentication.
    """
    await verify_api_key(x_api_key)
    
    if not q:
        raise ValueError("Search query 'q' is required")
    
    # Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)
    
    # Build arguments
    args = {
        "search_term": q,
        "workspace_path": resolved_workspace
    }
    if entity_type:
        args["entity_type"] = entity_type
    
    # Call task-mcp
    entities_data = await mcp_service.call_tool("search_entities", args)
    
    # Apply limit
    limited_entities = entities_data[:limit]
    
    return EntitySearchResponse(
        entities=[EntityResponse(**e) for e in limited_entities],
        total=len(entities_data),
        query=q,
        limit=limit,
    )
```

#### Endpoint 4: Get Entity's Linked Tasks

```python
@app.get("/api/entities/{entity_id}/tasks", response_model=TaskListResponse)
async def get_entity_tasks(
    entity_id: int,
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
):
    """
    Get all tasks linked to an entity.
    
    Args:
        entity_id: Entity ID
        status: Optional task status filter
        priority: Optional task priority filter
    
    Requires API key authentication.
    """
    await verify_api_key(x_api_key)
    
    # Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)
    
    # Build arguments
    args = {
        "entity_id": entity_id,
        "workspace_path": resolved_workspace
    }
    if status:
        args["status"] = status
    if priority:
        args["priority"] = priority
    
    # Call task-mcp
    tasks_data = await mcp_service.call_tool("get_entity_tasks", args)
    
    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in tasks_data],
        total=len(tasks_data),
        limit=len(tasks_data),
        offset=0,
    )
```

#### Endpoint 5: Get Entity Tags

```python
@app.get("/api/entity-tags")
async def get_entity_tags(
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
):
    """
    Get all unique entity tags with counts.
    
    Query Parameters:
        - project_id: Filter by project
    
    Returns:
        List of tag objects with name and count:
        [{"tag": "vendor", "count": 5}, ...]
    
    Requires API key authentication.
    """
    await verify_api_key(x_api_key)
    
    # Resolve workspace path
    resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)
    
    # Call task-mcp to get all entities
    entities_data = await mcp_service.call_tool(
        "list_entities", {"workspace_path": resolved_workspace}
    )
    
    # Extract and count tags
    tag_counts: dict[str, int] = {}
    for entity in entities_data:
        tags_str = entity.get("tags")
        if tags_str:
            tags = tags_str.strip().split()
            for tag in tags:
                tag = tag.strip()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Convert to list sorted by count
    tag_list = [{"tag": tag, "count": count} for tag, count in tag_counts.items()]
    tag_list.sort(key=lambda x: (-x["count"], x["tag"]))
    
    return {
        "tags": tag_list,
        "total": len(tag_list),
    }
```

### 3.2 New Pydantic Models

Add to `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/models.py`:

```python
class EntityResponse(BaseModel):
    """Response model for a single entity."""
    
    id: int
    entity_type: str  # 'file' | 'other'
    name: str
    identifier: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[str] = None  # JSON string
    tags: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EntityListResponse(BaseModel):
    """Response model for list of entities with pagination and metadata."""
    
    entities: list[EntityResponse]
    total: int
    limit: int = 50
    offset: int = 0
    meta: Optional[dict[str, Any]] = None  # Entity counts by type


class EntitySearchResponse(BaseModel):
    """Response model for entity search results."""
    
    entities: list[EntityResponse]
    total: int
    query: str
    limit: int = 20
```

---

## 4. Frontend Implementation

### 4.1 Alpine.js State Extensions

Add to `taskViewer()` function in `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html`:

```javascript
{
  // Tab state
  activeTab: 'tasks',  // 'tasks' | 'entities'
  
  // Entity data
  entities: [],
  filteredEntities: [],
  selectedEntity: null,
  entityTags: [],
  entityTaskCounts: {},  // { entityId: count }
  entityCounts: {
    total: 0,
    file: 0,
    other: 0
  },
  
  // Entity filters
  entityTypeFilter: 'all',  // 'all' | 'file' | 'other'
  entitySearchQuery: '',
  entitySelectedTag: null,
  entitySortBy: 'name_asc',
  
  // Entity UI state
  loadingEntities: false,
  entityError: null,
  showEntityModal: false,
  entityTasks: [],
  loadingEntityTasks: false,
}
```

### 4.2 Alpine.js Methods

Add to `taskViewer()` function:

```javascript
{
  // ... existing methods ...
  
  // Entity loading
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
        {
          headers: {
            'X-API-Key': this.apiKey,
          },
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      this.entities = data.entities || [];
      
      // Update counts from meta
      if (data.meta?.type_counts) {
        this.entityCounts.file = data.meta.type_counts.file || 0;
        this.entityCounts.other = data.meta.type_counts.other || 0;
        this.entityCounts.total = data.total || 0;
      }
      
      // Load entity tags
      await this.loadEntityTags();
      
      // Apply filters
      this.applyEntityFilters();
      
    } catch (err) {
      console.error('Failed to load entities:', err);
      this.entityError = err.message || 'Failed to load entities';
    } finally {
      this.loadingEntities = false;
    }
  },
  
  async loadEntityTags() {
    if (!this.currentProject) return;
    
    try {
      const response = await fetch(
        `${API_CONFIG.baseUrl}/api/entity-tags?project_id=${this.currentProject.id}`,
        {
          headers: {
            'X-API-Key': this.apiKey,
          },
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        this.entityTags = data.tags || [];
      }
    } catch (err) {
      console.error('Failed to load entity tags:', err);
    }
  },
  
  applyEntityFilters() {
    let filtered = [...this.entities];
    
    // Filter by type
    if (this.entityTypeFilter !== 'all') {
      filtered = filtered.filter(e => e.entity_type === this.entityTypeFilter);
    }
    
    // Filter by tag
    if (this.entitySelectedTag) {
      filtered = filtered.filter(e => {
        const tags = (e.tags || '').split(' ').filter(t => t);
        return tags.includes(this.entitySelectedTag);
      });
    }
    
    // Filter by search query
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
  
  selectEntityTag(tag) {
    this.entitySelectedTag = tag;
    this.applyEntityFilters();
  },
  
  // Entity detail modal
  async openEntityDetail(entity) {
    this.selectedEntity = entity;
    this.showEntityModal = true;
    this.entityTasks = [];
    this.loadingEntityTasks = true;
    
    // Load linked tasks
    try {
      const response = await fetch(
        `${API_CONFIG.baseUrl}/api/entities/${entity.id}/tasks?project_id=${this.currentProject.id}`,
        {
          headers: {
            'X-API-Key': this.apiKey,
          },
        }
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
  
  openTaskFromEntity(task) {
    // Close entity modal and open task modal
    this.closeEntityModal();
    this.openTaskDetail(task);
  },
  
  // Utility methods
  formatEntityMetadata(metadata) {
    if (!metadata) return '';
    try {
      const parsed = JSON.parse(metadata);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return metadata;
    }
  },
  
  copyEntityDetails(entity) {
    if (!entity) return;
    
    const details = `Entity #${entity.id}: ${entity.name}
Type: ${entity.entity_type}
${entity.identifier ? `Identifier: ${entity.identifier}\n` : ''}
${entity.description ? `Description: ${entity.description}\n` : ''}
${entity.tags ? `Tags: ${entity.tags}\n` : ''}
Created: ${this.formatDateTime(entity.created_at)}`;
    
    navigator.clipboard.writeText(details).then(() => {
      this.showToast('Entity details copied to clipboard', 'success');
    }).catch(err => {
      console.error('Failed to copy:', err);
      this.showToast('Failed to copy details', 'error');
    });
  },
  
  getStatusBadgeClass(status) {
    const classes = {
      'todo': 'bg-slate-100 text-slate-800',
      'in_progress': 'bg-blue-100 text-blue-800',
      'done': 'bg-green-100 text-green-800',
      'blocked': 'bg-red-100 text-red-800',
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  },
  
  getPriorityBadgeClass(priority) {
    const classes = {
      'low': 'bg-gray-100 text-gray-700',
      'medium': 'bg-amber-100 text-amber-800',
      'high': 'bg-red-100 text-red-800',
    };
    return classes[priority] || 'bg-gray-100 text-gray-800';
  },
}
```

### 4.3 HTML Template Modifications

**Locations in index.html:**

1. **Insert tab navigation** after `</header>` (around line 203)
2. **Duplicate filters bar** with `x-show="activeTab === 'entities'"` (after line 519)
3. **Add entity cards grid** with `x-show="activeTab === 'entities'"` (after task cards)
4. **Add entity detail modal** before closing `</div>` (before line 1060)

---

## 5. Integration Plan

### 5.1 Minimal Changes to Existing Code

**Principle:** Zero impact on existing task viewer functionality

**Changes Required:**

1. **main.py:**
   - Add 5 new endpoints (no changes to existing endpoints)
   - Add entity models to imports

2. **models.py:**
   - Add 3 new Pydantic models (EntityResponse, EntityListResponse, EntitySearchResponse)

3. **index.html:**
   - Add tab navigation HTML (20 lines)
   - Add entity filters bar (80 lines, similar to task filters)
   - Add entity cards grid (120 lines, similar to task cards)
   - Add entity detail modal (150 lines, similar to task modal)
   - Add entity state + methods to Alpine.js (200 lines)

**Total New Code:** ~600 lines (backend + frontend)  
**Modified Existing Code:** 0 lines (purely additive)

### 5.2 Backward Compatibility

- Default tab is 'tasks' (no change to existing behavior)
- All existing task viewer features remain unchanged
- No API breaking changes
- No database changes (entities already exist in task-mcp)

### 5.3 Project Switching Behavior

When user switches projects via dropdown:
1. Clear entity state (`entities = []`, `filteredEntities = []`)
2. Reset entity filters to defaults
3. If on entities tab, reload entities for new project
4. Update entity counts badge in tab

**Code:**
```javascript
async selectProject(project) {
  this.currentProject = project;
  
  // Clear entity state
  this.entities = [];
  this.filteredEntities = [];
  this.entityTags = [];
  this.entityCounts = { total: 0, file: 0, other: 0 };
  
  // Reset filters
  this.entityTypeFilter = 'all';
  this.entitySearchQuery = '';
  this.entitySelectedTag = null;
  
  // Reload current tab
  if (this.activeTab === 'tasks') {
    await this.loadTasks();
  } else if (this.activeTab === 'entities') {
    await this.loadEntities();
  }
}
```

---

## 6. Technical Challenges

### 6.1 Challenge: Entity-Task Count Display

**Problem:** Need to show linked task count on each entity card without N+1 API calls.

**Solution 1: Client-Side Count (Recommended)**
- Load all entities (already cached)
- For each entity, make single API call to `/api/entities/{id}/tasks` and cache count
- Only load counts for visible entities (lazy load on scroll)

**Solution 2: Backend Optimization**
- Extend `list_entities` endpoint to include `linked_task_count` in response
- Modify MCP tool to JOIN with task_entity_links table
- More efficient but requires MCP tool changes

**Recommended:** Solution 1 for v1 (no MCP changes), Solution 2 for v2 (optimization)

### 6.2 Challenge: Large Entity Metadata Display

**Problem:** Entity metadata is JSON string, could be large and unformatted.

**Solution:**
- Parse JSON and pretty-print with `JSON.stringify(parsed, null, 2)`
- Truncate large metadata with "Show More" expansion
- Add syntax highlighting via CSS (optional)

**Code:**
```javascript
formatEntityMetadata(metadata) {
  if (!metadata) return '';
  try {
    const parsed = JSON.parse(metadata);
    const formatted = JSON.stringify(parsed, null, 2);
    
    // Truncate if > 500 chars
    if (formatted.length > 500) {
      return formatted.substring(0, 500) + '\n... (truncated)';
    }
    return formatted;
  } catch {
    return metadata;  // Return as-is if not valid JSON
  }
}
```

### 6.3 Challenge: Entity Tag Filtering Performance

**Problem:** Same as task tags - O(n) filtering on every keystroke.

**Solution:** Reuse existing debounced search pattern (300ms delay).

**Already implemented in template:**
```html
<input
  x-model.debounce.300ms="entitySearchQuery"
  @input="applyEntityFilters()"
  ...
/>
```

### 6.4 Challenge: Tab State Persistence

**Problem:** User refreshes page, loses active tab selection.

**Solution:** Store active tab in localStorage.

**Code:**
```javascript
{
  activeTab: localStorage.getItem('activeTab') || 'tasks',
  
  // Save on change
  switchTab(tab) {
    this.activeTab = tab;
    localStorage.setItem('activeTab', tab);
    
    if (tab === 'entities' && this.entities.length === 0) {
      this.loadEntities();
    }
  }
}
```

---

## 7. Implementation Sequence

### Phase 1: Backend Foundation (4 hours)

**Tasks:**
1. Add entity Pydantic models to `models.py` (30 min)
2. Implement 5 API endpoints in `main.py` (2 hours)
3. Test endpoints with curl/Postman (1 hour)
4. Verify MCP integration works correctly (30 min)

**Deliverable:** Working REST API for entities

**Acceptance Criteria:**
- All 5 endpoints return valid JSON
- Entity filtering by type/tags works
- Search returns expected results
- Entity task linking returns correct tasks

### Phase 2: Frontend Core (6 hours)

**Tasks:**
1. Add tab navigation HTML + CSS (1 hour)
2. Add entity state to Alpine.js (1 hour)
3. Implement entity loading methods (1.5 hours)
4. Build entity filters bar (1.5 hours)
5. Build entity cards grid (1 hour)

**Deliverable:** Functional entity viewer with filtering

**Acceptance Criteria:**
- Tab switching works smoothly
- Entities load and display correctly
- Type filter works (all/file/other)
- Search filters entities correctly
- Tag filter works
- Sort options work

### Phase 3: Detail Modal + Polish (4 hours)

**Tasks:**
1. Build entity detail modal (2 hours)
2. Implement entity-task linking display (1 hour)
3. Add copy-to-clipboard features (30 min)
4. Add loading states and error handling (30 min)
5. Responsive design testing (30 min)
6. Dark mode verification (30 min)

**Deliverable:** Complete entity viewer with all features

**Acceptance Criteria:**
- Entity modal opens on card click
- Linked tasks display correctly
- Can click task to switch to task modal
- Copy details works
- Loading spinners show during API calls
- Error messages display appropriately
- Works on mobile/tablet/desktop
- Dark mode renders correctly

### Phase 4: Testing & Documentation (2 hours)

**Tasks:**
1. End-to-end testing (1 hour)
2. Update README with entity viewer docs (30 min)
3. Update QUICKSTART with entity viewer section (30 min)

**Deliverable:** Production-ready feature

**Acceptance Criteria:**
- All user flows work without errors
- Documentation updated
- No console errors
- No accessibility issues

---

## 8. Testing Strategy

### 8.1 Backend API Testing

**Test Script:** `task-viewer/test_entity_api.sh`

```bash
#!/bin/bash
API_KEY="${API_KEY:-dev-key-local-only}"
BASE_URL="http://127.0.0.1:8001"
PROJECT_ID="1e7be4ae"  # Replace with actual project ID

echo "=== Testing Entity API Endpoints ==="

# Test 1: List all entities
echo -e "\n1. List all entities:"
curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/api/entities?project_id=$PROJECT_ID" | jq '.total'

# Test 2: Filter by type
echo -e "\n2. List file entities:"
curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/api/entities?project_id=$PROJECT_ID&entity_type=file" | jq '.total'

# Test 3: Search entities
echo -e "\n3. Search entities:"
curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/api/entities/search?project_id=$PROJECT_ID&q=vendor" | jq '.total'

# Test 4: Get single entity
echo -e "\n4. Get entity #1:"
curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/api/entities/1?project_id=$PROJECT_ID" | jq '.name'

# Test 5: Get entity tasks
echo -e "\n5. Get tasks for entity #1:"
curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/api/entities/1/tasks?project_id=$PROJECT_ID" | jq '.total'

# Test 6: Get entity tags
echo -e "\n6. Get all entity tags:"
curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/api/entity-tags?project_id=$PROJECT_ID" | jq '.total'
```

### 8.2 Frontend UI Testing

**Manual Test Checklist:**

- [ ] Tab navigation switches between tasks/entities
- [ ] Entity count badge shows correct count
- [ ] Entities load when switching to tab
- [ ] Type filter (all/file/other) works
- [ ] Tag dropdown shows entity tags
- [ ] Tag filter works correctly
- [ ] Search filters by name/identifier/description
- [ ] Sort dropdown changes entity order
- [ ] Entity cards display all fields correctly
- [ ] Click entity card opens detail modal
- [ ] Entity modal shows full details
- [ ] Linked tasks section loads correctly
- [ ] Click linked task opens task modal
- [ ] Copy entity details works
- [ ] Close modal button works
- [ ] Click outside modal closes it
- [ ] Loading spinners show during API calls
- [ ] Error messages display on API failures
- [ ] Project switching reloads entities
- [ ] Responsive design works on mobile
- [ ] Dark mode renders correctly
- [ ] No console errors

### 8.3 Integration Testing

**Scenarios:**

1. **Empty Project:**
   - Select project with no entities
   - Verify empty state message shows
   - Verify no errors

2. **Large Dataset:**
   - Select project with 100+ entities
   - Verify pagination works
   - Verify search is fast (<500ms)

3. **Cross-Tab Navigation:**
   - Open task from entity modal
   - Verify task modal opens correctly
   - Close and return to entities tab
   - Verify state preserved

4. **Error Handling:**
   - Disconnect network
   - Try to load entities
   - Verify error message shows
   - Reconnect and retry
   - Verify recovery works

---

## 9. Effort Estimates

### 9.1 Detailed Breakdown

| Phase | Component | Estimated Time |
|-------|-----------|----------------|
| **Phase 1: Backend** | | **4 hours** |
| | Pydantic models | 0.5h |
| | List entities endpoint | 0.5h |
| | Get entity endpoint | 0.25h |
| | Search entities endpoint | 0.5h |
| | Get entity tasks endpoint | 0.5h |
| | Get entity tags endpoint | 0.25h |
| | Testing & debugging | 1.5h |
| **Phase 2: Frontend Core** | | **6 hours** |
| | Tab navigation UI | 1h |
| | Entity state setup | 1h |
| | Entity loading methods | 1.5h |
| | Entity filters bar | 1.5h |
| | Entity cards grid | 1h |
| **Phase 3: Modal & Polish** | | **4 hours** |
| | Entity detail modal | 2h |
| | Linked tasks display | 1h |
| | Copy/utility features | 0.5h |
| | Loading/error states | 0.5h |
| | Responsive testing | 0.5h |
| | Dark mode verification | 0.5h |
| **Phase 4: Testing & Docs** | | **2 hours** |
| | End-to-end testing | 1h |
| | Documentation updates | 1h |
| **TOTAL** | | **16 hours** |

### 9.2 Assumptions

- Developer has experience with FastAPI and Alpine.js
- No unexpected MCP tool issues
- Test data already exists in task-mcp database
- No major design changes during implementation

### 9.3 Risk Mitigation

**Risk 1: MCP Tool Performance Issues**
- Mitigation: Test with large datasets early
- Fallback: Add pagination/caching layer

**Risk 2: Complex Entity Metadata Rendering**
- Mitigation: Start with simple JSON.stringify
- Fallback: Truncate large metadata, add "View Raw" toggle

**Risk 3: Mobile Responsiveness Issues**
- Mitigation: Test on mobile early in Phase 2
- Fallback: Simplify entity cards for mobile

---

## 10. Success Metrics

### 10.1 Functional Completeness

- [ ] All 8 requirements from Task #69 implemented
- [ ] 5 backend API endpoints working
- [ ] 3 Pydantic models added
- [ ] Tab navigation functional
- [ ] Entity filtering by type/tags/search working
- [ ] Entity detail modal with linked tasks
- [ ] Copy-to-clipboard features working

### 10.2 Code Quality

- [ ] No console errors in browser
- [ ] No Python exceptions in logs
- [ ] Passes all manual test checklist items
- [ ] Responsive design verified
- [ ] Dark mode verified
- [ ] API endpoints follow existing patterns
- [ ] Frontend follows Alpine.js best practices

### 10.3 Documentation

- [ ] README updated with entity viewer section
- [ ] QUICKSTART updated with entity examples
- [ ] API endpoints documented
- [ ] Test script created

---

## 11. Future Enhancements (Not in Scope)

### v2 Features (Post-MVP)

1. **Bulk Entity Operations**
   - Select multiple entities
   - Bulk tag assignment
   - Export to CSV

2. **Advanced Filtering**
   - Multi-tag selection
   - Date range filters
   - Metadata field filters

3. **Entity Creation UI**
   - "Add Entity" button
   - Entity creation form
   - Drag-and-drop file entity creation

4. **Entity-Task Link Management**
   - Link/unlink tasks from entity modal
   - Inline task creation with auto-link
   - Visualize entity-task graph

5. **Entity Statistics Dashboard**
   - Most-linked entities
   - Entity creation timeline
   - Tag usage heatmap

6. **Performance Optimizations**
   - Virtual scrolling for large lists
   - Lazy-load entity task counts
   - Backend JOIN optimization for counts

---

## 12. Conclusion

This implementation plan provides a complete roadmap for adding the Entity Viewer feature to the task-viewer web application. The design follows established patterns from the existing codebase, minimizes risk through an incremental approach, and delivers a production-ready feature in an estimated 16 hours.

**Key Strengths:**
- Purely additive (zero impact on existing features)
- Reuses proven UI/API patterns
- Leverages existing MCP tools (no database changes)
- Tab-based architecture allows for future expansion
- Comprehensive testing strategy

**Next Steps:**
1. Review and approve this plan
2. Create subtasks for each phase
3. Begin Phase 1 implementation
4. Iterate through phases with testing at each stage

---

**Document Status:** Ready for Review  
**Last Updated:** 2025-11-02 16:00  
**Approval Required:** Yes
