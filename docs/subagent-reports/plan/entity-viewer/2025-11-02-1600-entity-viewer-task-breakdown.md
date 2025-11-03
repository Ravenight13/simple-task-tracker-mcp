# Entity Viewer Task Breakdown
**Date:** 2025-11-02 16:00
**Parent Task:** #69 - Enhancement #21: Entity Viewer for Projects
**Prepared By:** Task Breakdown Subagent

## Overview
This document provides a comprehensive hierarchical task breakdown for implementing the Entity Viewer feature in task-mcp. The breakdown is structured into 4 major phases with 23 granular subtasks, designed for parallel execution by multiple subagents using micro-commits.

## Task Hierarchy Structure

```
Task #69: Entity Viewer for Projects (Parent)
├── Phase 1: Backend API Development (6 subtasks)
│   ├── Add entity list endpoint
│   ├── Add entity detail endpoint
│   ├── Add entity search endpoint
│   ├── Add entity statistics endpoint
│   ├── Add entity-tasks endpoint
│   └── Add entity type filter endpoint
├── Phase 2: Frontend UI Development (10 subtasks)
│   ├── Create entities tab component
│   ├── Create entity card component
│   ├── Create entity detail modal
│   ├── Create entity type badge component
│   ├── Create entity metadata display
│   ├── Add entity filtering controls
│   ├── Add entity search bar
│   ├── Add entity statistics panel
│   ├── Add entity-task linking display
│   └── Add entity pagination
├── Phase 3: Integration & Testing (4 subtasks)
│   ├── API integration testing
│   ├── UI component testing
│   ├── End-to-end entity workflow testing
│   └── Performance testing for large entity sets
└── Phase 4: Documentation (3 subtasks)
    ├── Update API documentation
    ├── Update user guide
    └── Create developer implementation notes
```

---

## Phase 1: Backend API Development

### Parent Task 1.0: Backend API Development
**Title:** Implement Entity Viewer Backend API Endpoints
**Description:** Create REST API endpoints in task-viewer/main.py to expose entity-related MCP tools through HTTP interface.

**Acceptance Criteria:**
- All endpoints follow existing API patterns (authentication, error handling)
- All endpoints support project_id and workspace_path parameters
- All endpoints return consistent JSON response models
- CORS configured for entity endpoints
- Error responses follow existing error handler patterns

**Priority:** High
**Estimated Effort:** 8 hours total
**Dependencies:** None (can start immediately)
**File References:**
- `task-viewer/main.py`
- `task-viewer/models.py`
- `task-viewer/mcp_client.py`

**Tags:** backend api-development entity-viewer

---

#### Subtask 1.1: Add Entity List Endpoint
**Title:** Implement GET /api/entities endpoint
**Description:** Create endpoint to list all entities with optional filtering by type and tags.

**Acceptance Criteria:**
- Endpoint: `GET /api/entities`
- Query parameters: `entity_type` (optional), `tags` (optional), `limit`, `offset`
- Calls MCP tool: `list_entities(workspace_path, entity_type, tags)`
- Returns paginated entity list with total count
- Includes filtering metadata in response
- API key authentication required

**Implementation Details:**
```python
@app.get("/api/entities", response_model=EntityListResponse)
async def list_entities(
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
    entity_type: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    # Verify API key
    # Resolve workspace path
    # Call MCP list_entities
    # Apply pagination
    # Return EntityListResponse
```

**Priority:** High
**Estimated Effort:** 1.5 hours
**Dependencies:** None
**File References:**
- `task-viewer/main.py` (lines 436-558 - similar to list_tasks endpoint)
- `task-viewer/models.py` (add EntityListResponse model)

**Tags:** backend api entity-list

---

#### Subtask 1.2: Add Entity Detail Endpoint
**Title:** Implement GET /api/entities/{entity_id} endpoint
**Description:** Create endpoint to retrieve single entity by ID with full details.

**Acceptance Criteria:**
- Endpoint: `GET /api/entities/{entity_id}`
- Calls MCP tool: `get_entity(entity_id, workspace_path)`
- Returns full entity object including metadata
- Returns 404 if entity not found or deleted
- API key authentication required

**Implementation Details:**
```python
@app.get("/api/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: int,
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
):
    # Verify API key
    # Resolve workspace path
    # Call MCP get_entity
    # Return EntityResponse
```

**Priority:** High
**Estimated Effort:** 1 hour
**Dependencies:** None
**File References:**
- `task-viewer/main.py` (lines 597-627 - similar to get_task endpoint)
- `task-viewer/models.py` (add EntityResponse model)

**Tags:** backend api entity-detail

---

#### Subtask 1.3: Add Entity Search Endpoint
**Title:** Implement GET /api/entities/search endpoint
**Description:** Create endpoint for full-text search of entities by name or identifier.

**Acceptance Criteria:**
- Endpoint: `GET /api/entities/search`
- Query parameters: `q` (required), `entity_type` (optional), `limit`
- Calls MCP tool: `search_entities(search_term, workspace_path, entity_type)`
- Returns matching entities with search metadata
- API key authentication required

**Implementation Details:**
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
    # Verify API key
    # Resolve workspace path
    # Call MCP search_entities
    # Apply limit
    # Return EntitySearchResponse
```

**Priority:** High
**Estimated Effort:** 1 hour
**Dependencies:** None
**File References:**
- `task-viewer/main.py` (lines 271-311 - similar to search_tasks endpoint)
- `task-viewer/models.py` (add EntitySearchResponse model)

**Tags:** backend api entity-search

---

#### Subtask 1.4: Add Entity Statistics Endpoint
**Title:** Implement GET /api/entities/stats endpoint
**Description:** Create endpoint to return entity statistics (counts by type, top tags, etc.).

**Acceptance Criteria:**
- Endpoint: `GET /api/entities/stats`
- Returns entity counts by type (file, other)
- Returns top tags with counts
- Returns total entity count
- Calculated from entity list (no new MCP tool needed)
- API key authentication required

**Implementation Details:**
```python
@app.get("/api/entities/stats")
async def get_entity_stats(
    x_api_key: str = Header(None),
    project_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
):
    # Verify API key
    # Resolve workspace path
    # Call MCP list_entities (no filters)
    # Calculate type counts
    # Calculate tag counts (similar to /api/tags)
    # Return stats object
```

**Priority:** Medium
**Estimated Effort:** 1.5 hours
**Dependencies:** Subtask 1.1 (entity list logic)
**File References:**
- `task-viewer/main.py` (lines 385-433 - similar to get_tags endpoint)

**Tags:** backend api entity-stats

---

#### Subtask 1.5: Add Entity-Tasks Endpoint
**Title:** Implement GET /api/entities/{entity_id}/tasks endpoint
**Description:** Create endpoint to get all tasks linked to a specific entity (reverse lookup).

**Acceptance Criteria:**
- Endpoint: `GET /api/entities/{entity_id}/tasks`
- Query parameters: `status` (optional), `priority` (optional)
- Calls MCP tool: `get_entity_tasks(entity_id, workspace_path, status, priority)`
- Returns task list with link metadata
- Returns 404 if entity not found
- API key authentication required

**Implementation Details:**
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
    # Verify API key
    # Resolve workspace path
    # Call MCP get_entity_tasks
    # Return TaskListResponse with link metadata
```

**Priority:** High
**Estimated Effort:** 1.5 hours
**Dependencies:** None
**File References:**
- `task-viewer/main.py` (add new endpoint)
- `task-viewer/models.py` (reuse TaskListResponse)

**Tags:** backend api entity-tasks linking

---

#### Subtask 1.6: Add Entity Response Models
**Title:** Create Pydantic models for entity API responses
**Description:** Add entity response models to models.py for type safety and API documentation.

**Acceptance Criteria:**
- `EntityResponse` model with all entity fields
- `EntityListResponse` model with pagination
- `EntitySearchResponse` model with search metadata
- Models include proper type hints and field validation
- Models render correctly in /api/docs

**Implementation Details:**
```python
class EntityResponse(BaseModel):
    id: int
    entity_type: str
    name: str
    identifier: Optional[str]
    description: Optional[str]
    metadata: Optional[str]  # JSON string
    tags: Optional[str]
    created_by: str
    created_at: str
    updated_at: str
    deleted_at: Optional[str]

class EntityListResponse(BaseModel):
    entities: list[EntityResponse]
    total: int
    limit: int
    offset: int
    filters: Optional[dict] = None

class EntitySearchResponse(BaseModel):
    entities: list[EntityResponse]
    total: int
    query: str
    limit: int
```

**Priority:** High
**Estimated Effort:** 1.5 hours
**Dependencies:** None
**File References:**
- `task-viewer/models.py` (add after existing models)

**Tags:** backend models api-schema

---

## Phase 2: Frontend UI Development

### Parent Task 2.0: Frontend UI Development
**Title:** Implement Entity Viewer Frontend Components
**Description:** Build UI components for entity display, filtering, search, and task linking visualization.

**Acceptance Criteria:**
- Entities tab integrated into existing task viewer
- All components follow existing design system (Tailwind CSS)
- Alpine.js used for state management
- Responsive design (mobile-friendly)
- Accessibility standards met (ARIA labels, keyboard navigation)

**Priority:** High
**Estimated Effort:** 14 hours total
**Dependencies:** Phase 1 (Backend API) must be complete
**File References:**
- `task-viewer/static/index.html`
- `task-viewer/static/js/config.js`

**Tags:** frontend ui entity-viewer

---

#### Subtask 2.1: Create Entities Tab Component
**Title:** Add "Entities" navigation tab to task viewer
**Description:** Add new tab to main navigation and create entities view container.

**Acceptance Criteria:**
- "Entities" tab added to main navigation (after "Tasks" tab)
- Tab switching works correctly (Alpine.js state management)
- Entities container displays when tab is active
- Tab count badge shows total entity count
- URL hash routing supported (#entities)

**Implementation Details:**
- Add tab button to navigation (similar to existing tabs)
- Add `x-data` state for `activeTab` and `entityData`
- Add `x-show` directive to entities container
- Fetch entity count for badge on load
- Wire up tab click handlers

**Priority:** High
**Estimated Effort:** 1.5 hours
**Dependencies:** None
**File References:**
- `task-viewer/static/index.html` (lines 100-200 - navigation section)

**Tags:** frontend ui navigation tabs

---

#### Subtask 2.2: Create Entity Card Component
**Title:** Build entity card component for list view
**Description:** Create reusable card component to display entity summary in grid/list layout.

**Acceptance Criteria:**
- Card displays: name, identifier, type badge, tags, linked task count
- Card hover state shows metadata preview
- Card click opens entity detail modal
- Type-specific icons (file icon for files, generic for others)
- Truncated text with tooltips for long names/identifiers
- Responsive grid layout (1-3 columns based on screen size)

**Implementation Details:**
```html
<template x-for="entity in entities" :key="entity.id">
  <div @click="openEntityModal(entity)"
       class="entity-card bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer p-4">
    <!-- Entity type badge -->
    <span class="type-badge" :class="entity.entity_type === 'file' ? 'bg-blue-100' : 'bg-purple-100'">
      <x-text x-text="entity.entity_type"></x-text>
    </span>

    <!-- Entity name -->
    <h3 class="font-semibold text-lg mt-2" x-text="entity.name"></h3>

    <!-- Identifier -->
    <p class="text-sm text-gray-600 truncate" x-text="entity.identifier"></p>

    <!-- Tags -->
    <div class="tags mt-2" x-show="entity.tags">
      <!-- Tag badges -->
    </div>

    <!-- Linked tasks count -->
    <div class="mt-3 text-sm text-gray-500">
      <span x-text="entity.linked_tasks_count || 0"></span> linked tasks
    </div>
  </div>
</template>
```

**Priority:** High
**Estimated Effort:** 2 hours
**Dependencies:** Subtask 2.1 (entities container)
**File References:**
- `task-viewer/static/index.html` (add component template)

**Tags:** frontend ui entity-card component

---

#### Subtask 2.3: Create Entity Detail Modal
**Title:** Build modal to display full entity details and linked tasks
**Description:** Create modal component showing complete entity information and task relationships.

**Acceptance Criteria:**
- Modal displays all entity fields (name, identifier, type, description, metadata, tags)
- JSON metadata displayed in formatted/pretty-printed view
- Lists all linked tasks with status/priority badges
- Click task to navigate to task detail
- Modal can be closed (X button, ESC key, backdrop click)
- Modal is accessible (focus trap, ARIA labels)

**Implementation Details:**
```html
<div x-show="entityModalOpen"
     x-cloak
     @keydown.escape="closeEntityModal()"
     class="fixed inset-0 z-50 overflow-y-auto">
  <!-- Backdrop -->
  <div @click="closeEntityModal()" class="fixed inset-0 bg-black bg-opacity-50"></div>

  <!-- Modal content -->
  <div class="relative bg-white rounded-lg max-w-4xl mx-auto my-8 p-6">
    <!-- Header -->
    <div class="flex justify-between items-start">
      <h2 class="text-2xl font-bold" x-text="selectedEntity.name"></h2>
      <button @click="closeEntityModal()">Close</button>
    </div>

    <!-- Entity details -->
    <div class="mt-4 grid grid-cols-2 gap-4">
      <!-- Type, identifier, description, metadata -->
    </div>

    <!-- Linked tasks section -->
    <div class="mt-6">
      <h3 class="text-lg font-semibold">Linked Tasks</h3>
      <div class="task-list mt-3">
        <!-- Task cards -->
      </div>
    </div>
  </div>
</div>
```

**Priority:** High
**Estimated Effort:** 2.5 hours
**Dependencies:** Subtask 1.5 (entity-tasks endpoint)
**File References:**
- `task-viewer/static/index.html` (add modal component)

**Tags:** frontend ui modal entity-detail

---

#### Subtask 2.4: Create Entity Type Badge Component
**Title:** Build reusable badge component for entity types
**Description:** Create styled badge component to display entity type (file/other) consistently.

**Acceptance Criteria:**
- Badge component accepts entity_type prop
- Different colors for "file" (blue) vs "other" (purple)
- Icon + label format
- Consistent sizing and styling
- Reusable across card and modal views

**Implementation Details:**
```html
<span class="entity-type-badge inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
      :class="{
        'bg-blue-100 text-blue-800': entity.entity_type === 'file',
        'bg-purple-100 text-purple-800': entity.entity_type === 'other'
      }">
  <!-- Icon (file or generic) -->
  <svg class="w-3 h-3 mr-1" x-show="entity.entity_type === 'file'">...</svg>
  <svg class="w-3 h-3 mr-1" x-show="entity.entity_type === 'other'">...</svg>

  <span x-text="entity.entity_type"></span>
</span>
```

**Priority:** Medium
**Estimated Effort:** 1 hour
**Dependencies:** None
**File References:**
- `task-viewer/static/index.html` (add badge component)

**Tags:** frontend ui component badge

---

#### Subtask 2.5: Create Entity Metadata Display
**Title:** Build JSON metadata viewer component
**Description:** Create component to display entity metadata in readable format.

**Acceptance Criteria:**
- Parses JSON metadata string safely
- Pretty-printed JSON with syntax highlighting
- Collapsible sections for nested objects
- Handles null/empty metadata gracefully
- Copy-to-clipboard button for metadata

**Implementation Details:**
```html
<div class="metadata-viewer bg-gray-50 rounded p-3">
  <div class="flex justify-between items-center mb-2">
    <h4 class="text-sm font-semibold">Metadata</h4>
    <button @click="copyMetadata()">Copy</button>
  </div>

  <template x-if="entity.metadata">
    <pre class="text-xs overflow-x-auto"><code x-text="formatJSON(entity.metadata)"></code></pre>
  </template>

  <template x-if="!entity.metadata">
    <p class="text-sm text-gray-500 italic">No metadata</p>
  </template>
</div>
```

**JavaScript helper:**
```javascript
function formatJSON(jsonString) {
  try {
    const obj = JSON.parse(jsonString);
    return JSON.stringify(obj, null, 2);
  } catch (e) {
    return jsonString; // Return as-is if not valid JSON
  }
}
```

**Priority:** Medium
**Estimated Effort:** 1.5 hours
**Dependencies:** None
**File References:**
- `task-viewer/static/index.html` (add component)

**Tags:** frontend ui metadata json-viewer

---

#### Subtask 2.6: Add Entity Filtering Controls
**Title:** Implement filter controls for entity type and tags
**Description:** Add UI controls to filter entities by type (file/other/all) and tags.

**Acceptance Criteria:**
- Entity type dropdown (All, File, Other)
- Tag multi-select picker (reuse existing tag logic from tasks)
- Active filters displayed as removable chips
- Filter changes trigger API call to refresh entity list
- Filter state persisted in URL query params

**Implementation Details:**
```html
<div class="filters-bar flex gap-4 mb-4">
  <!-- Entity type dropdown -->
  <select x-model="entityFilters.type" @change="fetchEntities()">
    <option value="">All Types</option>
    <option value="file">Files</option>
    <option value="other">Other</option>
  </select>

  <!-- Tag picker -->
  <div class="tag-picker">
    <!-- Multi-select dropdown similar to task tag filter -->
  </div>

  <!-- Active filters chips -->
  <div class="active-filters flex gap-2">
    <template x-for="filter in activeFilters">
      <span class="filter-chip" @click="removeFilter(filter)">
        <span x-text="filter.label"></span>
        <button>×</button>
      </span>
    </template>
  </div>
</div>
```

**Priority:** High
**Estimated Effort:** 2 hours
**Dependencies:** Subtask 1.1 (entity list endpoint)
**File References:**
- `task-viewer/static/index.html` (add filter controls)

**Tags:** frontend ui filters controls

---

#### Subtask 2.7: Add Entity Search Bar
**Title:** Implement search bar for entity name/identifier search
**Description:** Add search input with debouncing to search entities by name or identifier.

**Acceptance Criteria:**
- Search input with icon
- Debounced search (300ms delay)
- Search triggers API call to /api/entities/search
- Clear button to reset search
- Loading state during search
- Search results replace main entity list

**Implementation Details:**
```html
<div class="search-bar mb-4">
  <div class="relative">
    <input type="text"
           x-model="entitySearch"
           @input.debounce.300ms="searchEntities()"
           placeholder="Search entities by name or identifier..."
           class="w-full pl-10 pr-4 py-2 border rounded-lg">

    <!-- Search icon -->
    <svg class="absolute left-3 top-3 w-4 h-4 text-gray-400">...</svg>

    <!-- Clear button -->
    <button x-show="entitySearch"
            @click="clearSearch()"
            class="absolute right-3 top-3">×</button>
  </div>

  <!-- Search result count -->
  <p x-show="entitySearch" class="text-sm text-gray-600 mt-2">
    Found <span x-text="searchResultCount"></span> entities
  </p>
</div>
```

**Priority:** High
**Estimated Effort:** 1.5 hours
**Dependencies:** Subtask 1.3 (search endpoint)
**File References:**
- `task-viewer/static/index.html` (add search component)

**Tags:** frontend ui search debounce

---

#### Subtask 2.8: Add Entity Statistics Panel
**Title:** Build statistics panel showing entity metrics
**Description:** Create panel displaying entity counts by type, top tags, and other metrics.

**Acceptance Criteria:**
- Total entity count
- Counts by type (file vs other) with percentage
- Top 5 tags with counts
- Bar chart or visual representation of distributions
- Updates when filters change
- Collapsible panel (optional)

**Implementation Details:**
```html
<div class="stats-panel bg-white rounded-lg shadow p-4 mb-4">
  <h3 class="text-lg font-semibold mb-3">Entity Statistics</h3>

  <!-- Total count -->
  <div class="stat-item">
    <span class="label">Total Entities:</span>
    <span class="value font-bold" x-text="entityStats.total"></span>
  </div>

  <!-- Type breakdown -->
  <div class="stat-item mt-2">
    <span class="label">Files:</span>
    <span class="value" x-text="entityStats.file_count"></span>
    <span class="percentage" x-text="'(' + entityStats.file_percentage + '%)'"></span>
  </div>

  <div class="stat-item">
    <span class="label">Other:</span>
    <span class="value" x-text="entityStats.other_count"></span>
    <span class="percentage" x-text="'(' + entityStats.other_percentage + '%)'"></span>
  </div>

  <!-- Top tags -->
  <div class="top-tags mt-4">
    <h4 class="text-sm font-semibold mb-2">Top Tags</h4>
    <template x-for="tag in entityStats.top_tags">
      <div class="tag-stat flex justify-between text-sm">
        <span x-text="tag.name"></span>
        <span x-text="tag.count"></span>
      </div>
    </template>
  </div>
</div>
```

**Priority:** Medium
**Estimated Effort:** 2 hours
**Dependencies:** Subtask 1.4 (stats endpoint)
**File References:**
- `task-viewer/static/index.html` (add stats panel)

**Tags:** frontend ui statistics metrics

---

#### Subtask 2.9: Add Entity-Task Linking Display
**Title:** Display task relationships on entity cards and detail view
**Description:** Show which tasks are linked to each entity with visual indicators.

**Acceptance Criteria:**
- Entity card shows linked task count badge
- Entity detail modal lists all linked tasks
- Linked tasks show status and priority badges
- Click task to navigate to task detail or open task modal
- Show link creation timestamp ("Linked 2 days ago")
- Empty state message when no tasks linked

**Implementation Details:**
```html
<!-- In entity detail modal -->
<div class="linked-tasks-section mt-6">
  <h3 class="text-lg font-semibold flex items-center gap-2">
    Linked Tasks
    <span class="badge" x-text="linkedTasks.length"></span>
  </h3>

  <template x-if="linkedTasks.length === 0">
    <p class="text-gray-500 italic mt-3">No tasks linked to this entity</p>
  </template>

  <template x-if="linkedTasks.length > 0">
    <div class="task-list grid gap-3 mt-3">
      <template x-for="task in linkedTasks">
        <div @click="openTaskDetail(task.id)"
             class="task-card bg-gray-50 rounded p-3 hover:bg-gray-100 cursor-pointer">
          <!-- Task title -->
          <h4 class="font-medium" x-text="task.title"></h4>

          <!-- Status + priority badges -->
          <div class="badges flex gap-2 mt-2">
            <span class="status-badge" x-text="task.status"></span>
            <span class="priority-badge" x-text="task.priority"></span>
          </div>

          <!-- Link timestamp -->
          <p class="text-xs text-gray-500 mt-2">
            Linked <span x-text="formatRelativeTime(task.link_created_at)"></span>
          </p>
        </div>
      </template>
    </div>
  </template>
</div>
```

**Priority:** High
**Estimated Effort:** 2 hours
**Dependencies:** Subtask 1.5 (entity-tasks endpoint), Subtask 2.3 (modal)
**File References:**
- `task-viewer/static/index.html` (modal component)

**Tags:** frontend ui linking tasks

---

#### Subtask 2.10: Add Entity Pagination
**Title:** Implement pagination for entity list
**Description:** Add pagination controls to handle large entity lists efficiently.

**Acceptance Criteria:**
- Pagination controls (Previous, Next, page numbers)
- Page size selector (25, 50, 100 items)
- Shows "Showing X-Y of Z entities"
- Pagination state synced with URL query params
- Smooth scroll to top on page change
- Disable Previous/Next when at boundaries

**Implementation Details:**
```html
<div class="pagination-controls flex justify-between items-center mt-6">
  <!-- Results summary -->
  <p class="text-sm text-gray-600">
    Showing <span x-text="paginationStart"></span>-<span x-text="paginationEnd"></span>
    of <span x-text="totalEntities"></span> entities
  </p>

  <!-- Page navigation -->
  <div class="flex gap-2">
    <button @click="previousPage()"
            :disabled="currentPage === 1"
            class="px-3 py-1 border rounded">
      Previous
    </button>

    <!-- Page numbers (show max 5) -->
    <template x-for="page in visiblePages">
      <button @click="goToPage(page)"
              :class="currentPage === page ? 'bg-blue-500 text-white' : 'bg-white'"
              class="px-3 py-1 border rounded"
              x-text="page">
      </button>
    </template>

    <button @click="nextPage()"
            :disabled="currentPage === totalPages"
            class="px-3 py-1 border rounded">
      Next
    </button>
  </div>

  <!-- Page size selector -->
  <select x-model="pageSize" @change="changePageSize()">
    <option value="25">25 per page</option>
    <option value="50">50 per page</option>
    <option value="100">100 per page</option>
  </select>
</div>
```

**Priority:** Medium
**Estimated Effort:** 1.5 hours
**Dependencies:** Subtask 2.2 (entity cards)
**File References:**
- `task-viewer/static/index.html` (add pagination)

**Tags:** frontend ui pagination

---

## Phase 3: Integration & Testing

### Parent Task 3.0: Integration & Testing
**Title:** Test Entity Viewer Integration and Performance
**Description:** Comprehensive testing of entity viewer feature including API, UI, and end-to-end workflows.

**Acceptance Criteria:**
- All API endpoints tested with various inputs
- UI components render correctly in all browsers
- Entity workflows (view, search, filter, detail) work end-to-end
- Performance acceptable with 1000+ entities
- No console errors or warnings

**Priority:** High
**Estimated Effort:** 6 hours total
**Dependencies:** Phase 1 and Phase 2 complete
**File References:**
- `tests/test_task_viewer_api.py` (create new test file)
- `task-viewer/static/index.html`

**Tags:** testing integration qa

---

#### Subtask 3.1: API Integration Testing
**Title:** Test all entity API endpoints
**Description:** Write integration tests for all new entity endpoints using pytest.

**Acceptance Criteria:**
- Tests for GET /api/entities (list)
- Tests for GET /api/entities/{id} (detail)
- Tests for GET /api/entities/search
- Tests for GET /api/entities/stats
- Tests for GET /api/entities/{id}/tasks
- Tests cover success cases and error cases (404, 401)
- Tests verify response models
- Tests check pagination behavior
- All tests pass

**Implementation Details:**
```python
# tests/test_entity_api.py
def test_list_entities(client, api_key):
    response = client.get(
        "/api/entities",
        headers={"X-API-Key": api_key},
        params={"project_id": "test123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
    assert "total" in data

def test_get_entity(client, api_key, test_entity_id):
    response = client.get(
        f"/api/entities/{test_entity_id}",
        headers={"X-API-Key": api_key},
        params={"project_id": "test123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_entity_id

def test_search_entities(client, api_key):
    response = client.get(
        "/api/entities/search",
        headers={"X-API-Key": api_key},
        params={"q": "test", "project_id": "test123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
    assert "query" in data
```

**Priority:** High
**Estimated Effort:** 2 hours
**Dependencies:** All Phase 1 subtasks
**File References:**
- `tests/test_entity_api.py` (create new file)
- `tests/conftest.py` (fixtures)

**Tags:** testing api pytest

---

#### Subtask 3.2: UI Component Testing
**Title:** Manual testing of entity UI components
**Description:** Test all entity UI components for functionality and visual correctness.

**Test Checklist:**
- [ ] Entities tab appears in navigation
- [ ] Entity cards render correctly (all fields visible)
- [ ] Entity type badges show correct colors
- [ ] Entity detail modal opens and displays data
- [ ] Metadata JSON displays formatted
- [ ] Linked tasks display in modal
- [ ] Search bar works with debouncing
- [ ] Filters apply correctly (type, tags)
- [ ] Active filter chips removable
- [ ] Statistics panel shows correct counts
- [ ] Pagination works (previous, next, page numbers)
- [ ] Page size selector updates results
- [ ] Responsive design works on mobile
- [ ] Dark mode compatible (if applicable)
- [ ] Accessibility: keyboard navigation works
- [ ] Accessibility: screen reader labels present

**Priority:** High
**Estimated Effort:** 2 hours
**Dependencies:** All Phase 2 subtasks
**File References:**
- `task-viewer/static/index.html`

**Tags:** testing ui manual-testing

---

#### Subtask 3.3: End-to-End Entity Workflow Testing
**Title:** Test complete entity viewer workflows
**Description:** Test full user workflows from start to finish.

**Test Scenarios:**

**Scenario 1: Browse and View Entity**
1. Navigate to Entities tab
2. View list of entities
3. Apply type filter (File)
4. Click entity card
5. View entity detail modal
6. View linked tasks
7. Click task to view task detail
8. Close modal

**Scenario 2: Search for Entity**
1. Navigate to Entities tab
2. Enter search query in search bar
3. View search results
4. Clear search
5. Verify original list restored

**Scenario 3: Filter Entities by Tag**
1. Navigate to Entities tab
2. Open tag picker
3. Select tag
4. View filtered results
5. Remove tag filter
6. Verify full list restored

**Scenario 4: View Entity Statistics**
1. Navigate to Entities tab
2. View statistics panel
3. Check total count
4. Check type breakdown
5. Check top tags
6. Apply filter and verify stats update

**Priority:** High
**Estimated Effort:** 1.5 hours
**Dependencies:** Subtasks 3.1, 3.2
**File References:**
- `docs/testing-checklist.md` (create new file)

**Tags:** testing e2e workflow qa

---

#### Subtask 3.4: Performance Testing with Large Entity Sets
**Title:** Test entity viewer performance with 1000+ entities
**Description:** Verify acceptable performance with large datasets.

**Test Cases:**
- Create test database with 1000+ entities
- Measure page load time (should be < 2 seconds)
- Measure search response time (should be < 500ms)
- Measure filter application time (should be < 300ms)
- Verify pagination limits prevent loading all entities
- Check memory usage in browser dev tools
- Test smooth scrolling with large lists

**Performance Benchmarks:**
- Initial page load: < 2 seconds
- Entity list fetch: < 1 second
- Search: < 500ms
- Filter change: < 300ms
- Modal open: < 200ms
- No memory leaks after 20 interactions

**Priority:** Medium
**Estimated Effort:** 1.5 hours
**Dependencies:** Subtasks 3.1, 3.2, 3.3
**File References:**
- `docs/performance-benchmarks.md` (create new file)

**Tags:** testing performance benchmarking

---

## Phase 4: Documentation

### Parent Task 4.0: Documentation
**Title:** Document Entity Viewer Feature
**Description:** Create comprehensive documentation for entity viewer API, UI, and implementation.

**Acceptance Criteria:**
- API endpoints documented in OpenAPI/Swagger
- User guide explains entity viewer features
- Developer notes explain implementation details
- Screenshots included in user guide
- Code comments added to complex sections

**Priority:** Medium
**Estimated Effort:** 4 hours total
**Dependencies:** Phase 3 complete
**File References:**
- `docs/api-documentation.md`
- `docs/user-guide.md`
- `docs/entity-viewer-implementation.md`

**Tags:** documentation user-guide api-docs

---

#### Subtask 4.1: Update API Documentation
**Title:** Document entity API endpoints in OpenAPI schema
**Description:** Add entity endpoints to API documentation with examples.

**Acceptance Criteria:**
- All entity endpoints documented in /api/docs
- Request/response schemas complete
- Example requests included
- Error responses documented
- Authentication requirements specified

**Documentation Sections:**
- GET /api/entities
- GET /api/entities/{entity_id}
- GET /api/entities/search
- GET /api/entities/stats
- GET /api/entities/{entity_id}/tasks

**Priority:** Medium
**Estimated Effort:** 1.5 hours
**Dependencies:** Phase 1 complete
**File References:**
- `task-viewer/main.py` (OpenAPI docstrings)
- `docs/api-documentation.md`

**Tags:** documentation api-docs openapi

---

#### Subtask 4.2: Update User Guide
**Title:** Add entity viewer section to user guide
**Description:** Document entity viewer features with screenshots and usage examples.

**Acceptance Criteria:**
- Entity viewer section added to user guide
- Screenshots of entity list, cards, modal
- Step-by-step usage instructions
- Filtering and search explained
- Statistics panel explained
- Common use cases documented (vendor tracking, file tracking)

**Content Outline:**
1. Introduction to Entity Viewer
2. Navigating to Entities Tab
3. Understanding Entity Types (File vs Other)
4. Browsing Entities
5. Searching Entities
6. Filtering by Type and Tags
7. Viewing Entity Details
8. Understanding Linked Tasks
9. Entity Statistics
10. Use Cases: Vendor Tracking, File Tracking

**Priority:** Medium
**Estimated Effort:** 2 hours
**Dependencies:** Phase 2 complete
**File References:**
- `docs/user-guide.md` (add new section)
- `docs/screenshots/` (add screenshots)

**Tags:** documentation user-guide tutorial

---

#### Subtask 4.3: Create Developer Implementation Notes
**Title:** Document entity viewer implementation for developers
**Description:** Create technical documentation explaining implementation details.

**Acceptance Criteria:**
- Architecture overview diagram
- Component hierarchy explained
- API integration pattern documented
- State management approach explained
- Extension points identified
- Known limitations documented

**Content Outline:**
1. Architecture Overview
2. Backend Implementation
   - API endpoints
   - MCP tool integration
   - Response models
3. Frontend Implementation
   - Alpine.js state management
   - Component structure
   - API client integration
4. Data Flow Diagrams
5. Extension Points
6. Known Limitations
7. Future Enhancements

**Priority:** Medium
**Estimated Effort:** 1.5 hours
**Dependencies:** Phase 1 and Phase 2 complete
**File References:**
- `docs/entity-viewer-implementation.md` (create new file)

**Tags:** documentation architecture developer-docs

---

## Summary Statistics

### Task Counts
- **Total Tasks:** 23 subtasks + 4 parent tasks = 27 tasks
- **Phase 1 (Backend):** 6 subtasks
- **Phase 2 (Frontend):** 10 subtasks
- **Phase 3 (Testing):** 4 subtasks
- **Phase 4 (Documentation):** 3 subtasks

### Effort Estimation
- **Total Effort:** 32 hours
- **Phase 1:** 8 hours
- **Phase 2:** 14 hours
- **Phase 3:** 6 hours
- **Phase 4:** 4 hours

### Priority Breakdown
- **High Priority:** 16 tasks
- **Medium Priority:** 7 tasks
- **Low Priority:** 0 tasks

### Critical Path Dependencies
1. Phase 1 must complete before Phase 2 can start
2. Phase 3 requires both Phase 1 and Phase 2 complete
3. Phase 4 requires Phase 3 complete (especially for screenshots)

### Parallel Execution Opportunities
- **Within Phase 1:** Subtasks 1.1-1.3 and 1.5-1.6 can run in parallel
- **Within Phase 2:** Subtasks 2.1, 2.4, 2.5 can start early; others depend on 2.1
- **Within Phase 3:** Subtasks 3.1 and 3.2 can run in parallel
- **Within Phase 4:** All subtasks can run in parallel

### File Impact Analysis
**Backend Files Modified:**
- `task-viewer/main.py` (5 new endpoints)
- `task-viewer/models.py` (3 new response models)

**Frontend Files Modified:**
- `task-viewer/static/index.html` (major additions: tab, cards, modal, filters, search, pagination)

**Test Files Created:**
- `tests/test_entity_api.py`

**Documentation Files Created/Modified:**
- `docs/api-documentation.md` (update)
- `docs/user-guide.md` (update)
- `docs/entity-viewer-implementation.md` (new)
- `docs/testing-checklist.md` (new)
- `docs/performance-benchmarks.md` (new)

---

## Risk Assessment

### High Risk Areas
1. **Frontend Complexity:** Alpine.js state management for entity modal + linked tasks may be complex
2. **Performance:** Large entity sets (1000+) may require pagination optimization
3. **JSON Metadata Display:** Parsing and rendering arbitrary JSON safely

### Mitigation Strategies
1. Break down complex Alpine.js components into smaller, testable units
2. Implement pagination from start (don't load all entities at once)
3. Use safe JSON parsing with try-catch; sanitize before rendering

### Dependencies on External Systems
- MCP tools: list_entities, get_entity, search_entities, get_entity_tasks
- Task-viewer API patterns (authentication, error handling)
- Tailwind CSS and Alpine.js CDN availability

---

## Recommendations

### For Optimal Execution
1. **Start with Backend (Phase 1):** Complete all API endpoints first to unblock frontend work
2. **Create Mock Data:** Generate test entities early for frontend development
3. **Incremental Testing:** Test each subtask immediately after completion
4. **Use Micro-Commits:** Commit after each subtask completion
5. **Tag Properly:** Use `project:entity-viewer` tag for all tasks

### Extension Points for Future
- Edit/update entity functionality (Phase 2 is read-only)
- Create entity from UI
- Link/unlink tasks to entities
- Bulk operations (delete multiple entities)
- Export entity list to CSV
- Advanced filtering (date ranges, metadata queries)

---

## Appendix: MCP Tool Reference

### Available Entity MCP Tools

**list_entities:**
```python
list_entities(
    workspace_path: str,
    entity_type: str | None = None,  # 'file' or 'other'
    tags: str | None = None          # space-separated tags
) -> list[dict]
```

**get_entity:**
```python
get_entity(
    entity_id: int,
    workspace_path: str
) -> dict
```

**search_entities:**
```python
search_entities(
    search_term: str,
    workspace_path: str,
    entity_type: str | None = None
) -> list[dict]
```

**get_entity_tasks:**
```python
get_entity_tasks(
    entity_id: int,
    workspace_path: str,
    status: str | None = None,    # 'todo', 'in_progress', 'done', etc.
    priority: str | None = None   # 'low', 'medium', 'high'
) -> list[dict]  # Returns tasks with link metadata
```

---

**End of Task Breakdown**
**Prepared:** 2025-11-02 16:00
**Version:** 1.0
