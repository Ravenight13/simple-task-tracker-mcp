# Entity Viewer Architecture Review
**Date:** 2025-11-02 16:00
**Reviewer:** Architecture Review Agent (Software Architecture Specialist)
**Task:** #69 - Enhancement #21: Entity Viewer for Projects
**Review Type:** Pre-Implementation Architecture Assessment

---

## Executive Summary

This review provides architectural guidance for implementing an Entity Viewer feature in the task-viewer web application. The review was conducted proactively based on task requirements (#69) and existing codebase analysis, since no implementation plan was provided at review time.

**Overall Assessment:** ✅ **APPROVED WITH RECOMMENDATIONS**

The proposed Entity Viewer feature is architecturally sound and aligns well with existing patterns. However, several architectural considerations must be addressed to ensure scalability, maintainability, and consistency with the existing codebase.

---

## Review Context

### Task Requirements Analysis
- **Scope:** Add comprehensive entity viewing/management UI to task-viewer
- **Data Source:** Leverage existing MCP entity tools (list_entities, get_entity, search_entities, get_entity_tasks)
- **Integration Points:** Task-viewer frontend (Alpine.js/Tailwind) + FastAPI backend
- **Key Features:** Entity list, filtering, search, task linkage display, statistics

### Existing Architecture (Current State)

**Frontend Stack:**
- Alpine.js 3.x for reactivity (with Focus and Collapse plugins)
- Tailwind CSS 3.x for styling (via CDN)
- Vanilla JavaScript for API client
- Single-page application pattern

**Backend Stack:**
- FastAPI with async/await
- MCP client service (mcp_service) for task-mcp integration
- Workspace resolver for project/workspace path resolution
- Pydantic models for type safety
- API key authentication (X-API-Key header)

**Current API Patterns:**
```python
# Route structure
GET /api/projects
GET /api/projects/{project_id}/info
GET /api/tasks
GET /api/tasks/search
GET /api/tasks/{task_id}
GET /api/tasks/{task_id}/tree
GET /api/tags

# All routes require:
- API key authentication
- Workspace resolution (project_id or workspace_path)
- Consistent error handling (ValueError → 400/404, RuntimeError → 500)
```

---

## Architectural Assessment

### 1. Pattern Consistency ✅ EXCELLENT

**Strengths:**
- Entity system follows identical architectural patterns to task system
- MCP tools already exist (list_entities, get_entity, search_entities, get_entity_tasks)
- Database schema supports soft deletes, tags, metadata (consistent with tasks)
- Entity-task linking via junction table mirrors established patterns

**Alignment Score:** 9/10 (Excellent consistency with existing patterns)

### 2. API Design Considerations

#### Recommended API Endpoints

```python
# Entity CRUD (Read-Only for Phase 1)
GET /api/entities
  - Query params: entity_type, tags, limit, offset
  - Returns: EntityListResponse with pagination

GET /api/entities/{entity_id}
  - Returns: EntityResponse with full details

GET /api/entities/search
  - Query params: q (search term), entity_type, limit
  - Returns: EntitySearchResponse

GET /api/entities/{entity_id}/tasks
  - Query params: status, priority
  - Returns: TaskListResponse (reuse existing model)

# Statistics
GET /api/entities/stats
  - Returns: EntityStatsResponse with type counts, top linked entities
```

**Critical Design Decisions:**

**✅ DO:**
1. **Reuse TaskResponse model** for get_entity_tasks() responses (consistency)
2. **Mirror task API pagination** pattern (limit/offset query params)
3. **Follow workspace resolution** pattern (project_id or workspace_path)
4. **Apply same authentication** (X-API-Key header via verify_api_key())
5. **Use Pydantic models** for all request/response validation
6. **Handle workspace_path explicitly** (v0.4.0 requirement - no auto-detection)

**❌ DON'T:**
1. Create separate authentication mechanism
2. Use different pagination patterns
3. Skip workspace validation
4. Return raw database entities (always use response models)

#### Proposed Response Models

```python
# models.py additions
class EntityResponse(BaseModel):
    id: int
    entity_type: str  # 'file' or 'other'
    name: str
    identifier: Optional[str]
    description: Optional[str]
    metadata: Optional[str]  # JSON string
    tags: Optional[str]  # Space-separated
    created_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]

    # Enriched fields (computed)
    linked_task_count: Optional[int] = 0
    recent_tasks: Optional[List[int]] = []

class EntityListResponse(BaseModel):
    entities: List[EntityResponse]
    total: int
    limit: int
    offset: int
    filters: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None  # Type counts, etc.

class EntitySearchResponse(BaseModel):
    entities: List[EntityResponse]
    total: int
    query: str
    limit: int

class EntityStatsResponse(BaseModel):
    total_entities: int
    by_type: Dict[str, int]  # {"file": 42, "other": 15}
    top_linked: List[Dict[str, Any]]  # Most linked entities
    recent_entities: List[EntityResponse]
```

### 3. Frontend Architecture

#### Recommended UI Structure

**Tab/Section Approach (Preferred):**
```
[Tasks] [Entities] [Statistics]
  ^        ^           ^
  └─ Existing └─ New  └─ Future
```

**Benefits:**
- Clean separation of concerns
- Reuses existing filter bar patterns
- Enables future expansion (Statistics, Settings, etc.)
- Familiar navigation pattern

**Alternative: Sidebar Approach (Not Recommended)**
- More complex state management
- Harder to maintain responsive design
- Breaks existing single-column flow

#### Component Architecture (Alpine.js)

```javascript
// Recommended Alpine component structure
function entityViewer() {
  return {
    // State
    entities: [],
    selectedEntity: null,
    entityTypeFilter: 'all', // 'all', 'file', 'other'
    entityTags: [],
    selectedEntityTag: null,
    searchQuery: '',
    loading: false,
    error: null,

    // Pagination
    limit: 50,
    offset: 0,
    total: 0,

    // View state
    currentView: 'list', // 'list', 'detail'

    // Methods
    async fetchEntities() { /* ... */ },
    async fetchEntity(entityId) { /* ... */ },
    async fetchEntityTasks(entityId) { /* ... */ },
    selectEntity(entity) { /* ... */ },
    clearEntitySelection() { /* ... */ },
    applyEntityFilters() { /* ... */ },

    // Lifecycle
    init() {
      this.fetchEntities();
      this.fetchEntityTags();
    }
  }
}
```

**Integration with Existing taskViewer():**

**Option A: Separate Component (Recommended)**
```html
<div x-data="taskViewer()" x-init="init()">
  <div x-show="activeTab === 'tasks'">
    <!-- Existing task viewer -->
  </div>

  <div x-show="activeTab === 'entities'" x-data="entityViewer()" x-init="init()">
    <!-- New entity viewer -->
  </div>
</div>
```

**Option B: Merged Component (Not Recommended)**
- Risk of component bloat (taskViewer already ~800 lines JS)
- Harder to test independently
- Violates Single Responsibility Principle

### 4. Performance Considerations

#### Critical Performance Issues

**❗ MEDIUM RISK: Entity List Pagination**

**Problem:** Entity lists could grow large (100s of vendors, 1000s of files)

**Mitigation:**
1. **Enforce pagination** on backend (max limit: 100, default: 50)
2. **Add virtual scrolling** for large lists (consider using Alpine.js plugin or vanilla implementation)
3. **Index entity queries** in SQLite:
   ```sql
   CREATE INDEX idx_entities_type ON entities(entity_type) WHERE deleted_at IS NULL;
   CREATE INDEX idx_entities_tags ON entities(tags) WHERE deleted_at IS NULL;
   ```
4. **Lazy-load entity tasks** (only fetch when entity card expanded)

**❗ LOW RISK: Metadata Parsing**

**Problem:** Entity metadata is JSON string, requires parsing on every render

**Mitigation:**
1. Parse metadata once in backend response model
2. Cache parsed metadata in Alpine component state
3. Consider adding metadata preview field to EntityResponse (avoid parsing large JSON)

#### Caching Strategy

**Recommended:**
```javascript
// Frontend caching
const CACHE_TTL = 60000; // 60 seconds
const entityCache = new Map();

async function fetchEntityWithCache(entityId) {
  const cached = entityCache.get(entityId);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }

  const data = await api.getEntity(entityId);
  entityCache.set(entityId, { data, timestamp: Date.now() });
  return data;
}
```

### 5. Security Considerations ✅ SECURE

**Strengths:**
- API key authentication already in place (X-API-Key)
- Read-only operations (no create/update/delete in Phase 1)
- Workspace isolation enforced via workspace_path resolution
- SQL injection prevention via Pydantic models + parameterized queries

**Recommendations:**
1. **Sanitize entity metadata** display (XSS prevention):
   ```javascript
   // When displaying metadata in UI
   function sanitizeMetadata(metadataJson) {
     try {
       const parsed = JSON.parse(metadataJson);
       // Recursively escape HTML in string values
       return escapeHtml(JSON.stringify(parsed, null, 2));
     } catch {
       return 'Invalid JSON';
     }
   }
   ```

2. **Rate limiting** (future consideration):
   - Current API has no rate limiting
   - Consider adding FastAPI rate limiter for production

3. **Input validation**:
   - Validate entity_type enum ('file', 'other')
   - Sanitize search queries (max length, no special chars)
   - Validate pagination params (0 < limit <= 100, offset >= 0)

### 6. Data Consistency & Integrity

**✅ Strong Foundation:**
- Soft delete pattern prevents orphaned references
- Foreign key constraints on task_entity_links
- Cascade deletes on entity removal (links auto-deleted)

**Architectural Guidelines:**

1. **Entity-Task Link Display:**
   ```python
   # Backend: Enrich entity responses with task counts
   async def get_entity(entity_id: int, ...):
       entity_data = await mcp_service.call_tool("get_entity", {...})

       # Get linked task count
       tasks = await mcp_service.call_tool("get_entity_tasks", {
           "entity_id": entity_id,
           "workspace_path": resolved_workspace
       })

       entity_data["linked_task_count"] = len(tasks)
       entity_data["recent_tasks"] = [t["id"] for t in tasks[:5]]

       return EntityResponse(**entity_data)
   ```

2. **Workspace Validation (v0.4.0 Compliance):**
   ```python
   # CRITICAL: Always pass workspace_path explicitly
   # All MCP entity tools require workspace_path parameter

   # ❌ WRONG (will fail in v0.4.0+)
   await mcp_service.call_tool("list_entities", {})

   # ✅ CORRECT
   resolved_workspace = workspace_resolver.resolve(project_id, workspace_path)
   await mcp_service.call_tool("list_entities", {
       "workspace_path": resolved_workspace
   })
   ```

3. **Error Handling Consistency:**
   ```python
   # Match existing task endpoint patterns
   @app.get("/api/entities/{entity_id}", response_model=EntityResponse)
   async def get_entity(entity_id: int, ...):
       try:
           entity_data = await mcp_service.call_tool(
               "get_entity",
               {"entity_id": entity_id, "workspace_path": resolved_workspace}
           )

           if not entity_data:
               raise ValueError(f"Entity with ID {entity_id} not found or deleted")

           return EntityResponse(**entity_data)

       except ValueError as e:
           # Will be caught by exception handler → 404
           raise
       except Exception as e:
           # Will be caught by exception handler → 500
           logger.error(f"Failed to fetch entity: {e}", exc_info=True)
           raise RuntimeError(f"Failed to fetch entity: {e}")
   ```

### 7. UI/UX Considerations

#### Entity Card Design (Consistency with Task Cards)

**Recommended Structure:**
```html
<!-- Entity Card (mirrors task card pattern) -->
<div class="entity-card bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-lg transition-shadow cursor-pointer">
  <!-- Header: Type Badge + Name -->
  <div class="flex items-start justify-between mb-2">
    <div class="flex items-center gap-2">
      <span class="entity-type-badge" :class="entity.entity_type === 'file' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'">
        {{ entity.entity_type }}
      </span>
      <h3 class="font-semibold text-gray-900 dark:text-gray-100">
        {{ entity.name }}
      </h3>
    </div>

    <!-- Linked task count badge -->
    <span class="text-sm text-gray-500 dark:text-gray-400">
      {{ entity.linked_task_count }} tasks
    </span>
  </div>

  <!-- Identifier (if exists) -->
  <div class="text-sm text-gray-600 dark:text-gray-400 mb-2 font-mono truncate">
    {{ entity.identifier || 'No identifier' }}
  </div>

  <!-- Tags (reuse task tag styling) -->
  <div class="flex flex-wrap gap-1 mb-2">
    <template x-for="tag in (entity.tags || '').split(' ').filter(t => t)">
      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
        {{ tag }}
      </span>
    </template>
  </div>

  <!-- Metadata preview (collapsed by default) -->
  <div x-show="expanded" x-collapse>
    <div class="mt-2 p-2 bg-gray-50 dark:bg-gray-700 rounded text-xs font-mono overflow-x-auto">
      <pre>{{ formatMetadata(entity.metadata) }}</pre>
    </div>
  </div>
</div>
```

**Interaction Patterns:**
- Click card → Expand entity details inline (like task cards)
- Click "View Tasks" button → Navigate to tasks view filtered by entity
- Click tag → Filter entities by that tag
- Hover → Show tooltip with full identifier path

#### Filter Bar Integration

**Recommended:**
```html
<!-- Add entity type filter (parallel to task status filter) -->
<div class="flex flex-wrap items-center gap-2 mb-3">
  <span class="text-sm font-medium">Entity Type:</span>

  <button @click="entityTypeFilter = 'all'" :class="entityTypeFilter === 'all' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'">
    All ({{ stats.total }})
  </button>

  <button @click="entityTypeFilter = 'file'" :class="entityTypeFilter === 'file' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'">
    Files ({{ stats.by_type.file || 0 }})
  </button>

  <button @click="entityTypeFilter = 'other'" :class="entityTypeFilter === 'other' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'">
    Other ({{ stats.by_type.other || 0 }})
  </button>
</div>

<!-- Reuse existing tag filter dropdown (same component) -->
<div x-data="tagFilter('entity')">
  <!-- Same tag dropdown as tasks -->
</div>
```

#### Empty States & Loading States

**Critical UX Elements:**
```html
<!-- Loading skeleton (reuse task card skeleton pattern) -->
<template x-if="loading">
  <div class="space-y-4">
    <div class="skeleton h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
    <div class="skeleton h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
  </div>
</template>

<!-- Empty state: No entities -->
<template x-if="!loading && entities.length === 0 && !searchQuery">
  <div class="text-center py-12">
    <svg class="mx-auto h-12 w-12 text-gray-400">...</svg>
    <h3 class="mt-2 text-sm font-medium text-gray-900">No entities</h3>
    <p class="mt-1 text-sm text-gray-500">Get started by creating entities via Claude Code</p>
  </div>
</template>

<!-- Empty state: No search results -->
<template x-if="!loading && entities.length === 0 && searchQuery">
  <div class="text-center py-12">
    <svg class="mx-auto h-12 w-12 text-gray-400">...</svg>
    <h3 class="mt-2 text-sm font-medium text-gray-900">No results found</h3>
    <p class="mt-1 text-sm text-gray-500">Try adjusting your search or filters</p>
  </div>
</template>
```

### 8. Testability Assessment

**Current Testing Gap:**
- Task-viewer has no automated tests (only Playwright for task-mcp)
- Manual testing required for frontend changes

**Recommended Testing Strategy:**

**Phase 1: Manual Testing Checklist**
```
[ ] Entity list loads with pagination
[ ] Entity type filter works (all/file/other)
[ ] Entity tag filter works (reuse task tag filter)
[ ] Entity search returns correct results
[ ] Entity card displays all fields correctly
[ ] Entity metadata preview renders valid JSON
[ ] Clicking entity shows linked tasks
[ ] Linked task count is accurate
[ ] Empty states render correctly
[ ] Loading states render correctly
[ ] Error states display user-friendly messages
[ ] Dark mode styling works
[ ] Responsive design works (mobile/tablet/desktop)
[ ] Accessibility: Keyboard navigation works
[ ] Accessibility: Screen reader announces entity info
```

**Phase 2: Automated Testing (Future)**
- Add Playwright tests for entity viewer
- Test API endpoints with pytest
- Add integration tests for MCP tool calls

### 9. Implementation Risks & Mitigation

#### HIGH RISK: Workspace Path Resolution

**Risk:** Forgetting to pass workspace_path to MCP entity tools (v0.4.0 requirement)

**Impact:** ❌ Tool calls will fail with ValueError

**Mitigation:**
```python
# Create a helper function to ensure workspace_path is always included
def build_mcp_args(
    workspace_path: str,
    project_id: Optional[str] = None,
    workspace_path_param: Optional[str] = None,
    **kwargs
) -> dict:
    """Build MCP tool args with guaranteed workspace_path."""
    resolved = workspace_resolver.resolve(project_id, workspace_path_param)
    return {"workspace_path": resolved, **kwargs}

# Usage in endpoints
@app.get("/api/entities")
async def list_entities(...):
    args = build_mcp_args(
        workspace_path=resolved_workspace,
        entity_type=entity_type,
        tags=tags
    )
    entities = await mcp_service.call_tool("list_entities", args)
```

#### MEDIUM RISK: Entity Metadata Display

**Risk:** Entity metadata is arbitrary JSON, could contain:
- Very large payloads (>10k chars)
- Malformed JSON
- XSS vectors (if rendered unsafely)

**Mitigation:**
1. **Truncate large metadata** in list view (show preview only)
2. **Validate JSON** in backend before returning:
   ```python
   def safe_metadata_preview(metadata_str: str, max_chars: int = 200) -> str:
       """Return safe, truncated metadata preview."""
       if not metadata_str:
           return ""
       try:
           parsed = json.loads(metadata_str)
           preview = json.dumps(parsed, separators=(',', ':'))[:max_chars]
           return preview + "..." if len(preview) >= max_chars else preview
       except json.JSONDecodeError:
           return "[Invalid JSON]"
   ```
3. **Use text content** (not innerHTML) when rendering metadata in UI

#### LOW RISK: Tag Dropdown Performance

**Risk:** Entity tag dropdown could have 100+ unique tags (slow rendering)

**Impact:** Minor UI lag on tag dropdown open

**Mitigation:**
- Implement virtual scrolling for tag dropdown
- Cache tag list client-side (invalidate on entity list refresh)
- Limit tag dropdown to top 50 tags by count

### 10. Future Scalability Considerations

**Phase 2 Features (Deferred):**
1. **Entity CRUD Operations**
   - POST /api/entities (create entity)
   - PUT /api/entities/{entity_id} (update entity)
   - DELETE /api/entities/{entity_id} (soft delete)
   - POST /api/entities/{entity_id}/tasks/{task_id} (link entity to task)

2. **Advanced Filtering**
   - Filter by metadata fields (requires JSON indexing in SQLite)
   - Filter by linked task status (show entities with blocked tasks)
   - Filter by date ranges (created_at, updated_at)

3. **Bulk Operations**
   - Bulk tag updates
   - Bulk delete
   - Export entities as CSV/JSON

4. **Entity Relationships**
   - Show entity-to-entity relationships (e.g., vendor → files)
   - Graph visualization of entity connections

**Architecture Impact:**
- Current architecture supports these extensions with minimal refactoring
- MCP tools already exist for all CRUD operations
- Frontend component architecture is extensible

---

## Architectural Recommendations Summary

### MUST HAVE (Blocking Issues)

1. **✅ Workspace Path Resolution**
   - ALL MCP entity tool calls MUST include explicit workspace_path parameter
   - Use workspace_resolver.resolve() to get correct workspace path
   - Failure to do this will cause tool call failures in v0.4.0+

2. **✅ API Authentication**
   - ALL entity endpoints MUST use verify_api_key() dependency
   - No exceptions for read-only operations

3. **✅ Pagination**
   - Enforce max limit: 100, default: 50
   - Required for scalability (entity lists can grow to 1000+)

4. **✅ Response Models**
   - Use Pydantic models for ALL responses (type safety)
   - Enrich entity responses with computed fields (linked_task_count)

5. **✅ Error Handling**
   - Match existing exception handler patterns
   - ValueError → 400/404, RuntimeError → 500
   - Log all errors with context

### SHOULD HAVE (Important for Quality)

1. **✅ Frontend Component Separation**
   - Create separate entityViewer() Alpine component
   - Don't merge with taskViewer() (SRP violation)

2. **✅ Metadata Sanitization**
   - Parse and validate JSON in backend
   - Escape HTML in frontend rendering (XSS prevention)
   - Truncate large metadata in list view

3. **✅ UI Consistency**
   - Mirror task card styling for entity cards
   - Reuse tag filter dropdown component
   - Maintain dark mode support

4. **✅ Loading & Empty States**
   - Skeleton loaders during fetch
   - Friendly empty state messages
   - Clear error messages

### NICE TO HAVE (Quality of Life)

1. **Caching**
   - Frontend cache for entity list (60s TTL)
   - Cache entity tags separately

2. **Virtual Scrolling**
   - For entity lists > 100 items
   - For tag dropdowns > 50 tags

3. **Statistics Dashboard**
   - Top 10 most linked entities
   - Entity type distribution chart
   - Recent entities timeline

---

## Approval Decision

**✅ APPROVED WITH RECOMMENDATIONS**

**Rationale:**
- Proposed feature aligns perfectly with existing architecture
- MCP tools already exist (no backend protocol changes needed)
- UI patterns are well-established (minimal design risk)
- Security model is sound (read-only + API key auth)
- Performance concerns are manageable (pagination + caching)

**Conditions for Approval:**
1. MUST implement workspace_path resolution correctly (v0.4.0 requirement)
2. MUST use Pydantic response models (no raw MCP tool responses)
3. MUST enforce pagination (max 100 items per page)
4. SHOULD sanitize entity metadata (XSS prevention)
5. SHOULD create separate Alpine component (maintain SRP)

**Implementation Priority:**
- Phase 1 (MVP): Entity list, search, filtering, task linkage display
- Phase 2 (Future): Entity CRUD, bulk operations, advanced analytics

**Estimated Effort:** 6-10 hours (as stated in task description)
- Backend API endpoints: 2-3 hours
- Frontend component: 3-4 hours
- Testing & refinement: 1-3 hours

---

## Architectural Decision Records (ADRs)

### ADR-1: Use Separate Alpine Component for Entity Viewer

**Decision:** Create entityViewer() as a separate Alpine.js component, not merged with taskViewer()

**Rationale:**
- taskViewer() is already ~800 lines (too large)
- Violates Single Responsibility Principle
- Harder to test and maintain merged component
- Separate component enables independent evolution

**Alternatives Considered:**
- Merge into taskViewer() (rejected: component bloat)
- Use Vue.js/React (rejected: maintain existing tech stack)

**Status:** ✅ Approved

---

### ADR-2: Mirror Task API Pagination Pattern

**Decision:** Use identical pagination pattern as /api/tasks (limit/offset query params)

**Rationale:**
- Consistency with existing API
- Frontend developers already familiar with pattern
- Simplifies client-side code (reuse pagination components)
- Standard REST pagination pattern

**Alternatives Considered:**
- Cursor-based pagination (rejected: over-engineering for current scale)
- Page-based pagination (rejected: less flexible than offset-based)

**Status:** ✅ Approved

---

### ADR-3: Read-Only Entity Operations (Phase 1)

**Decision:** Phase 1 only implements GET operations (no create/update/delete)

**Rationale:**
- Matches task-viewer's original read-only design
- Reduces implementation complexity
- Entity creation should remain in Claude Code (primary workflow)
- Enables faster MVP delivery

**Alternatives Considered:**
- Full CRUD in Phase 1 (rejected: scope creep)
- No entity viewer at all (rejected: high user value)

**Status:** ✅ Approved

---

## Next Steps for Implementation Team

1. **Review existing MCP entity tools** - Understand parameters and return types
2. **Create Pydantic response models** - EntityResponse, EntityListResponse, etc.
3. **Implement backend API endpoints** - Start with /api/entities (simplest)
4. **Create Alpine.js component** - Scaffold entityViewer() with basic state
5. **Build entity card UI** - Mirror task card styling
6. **Implement filtering** - Entity type, tags, search
7. **Add task linkage display** - Show linked tasks when entity expanded
8. **Test workspace resolution** - Verify workspace_path is passed correctly
9. **Manual testing checklist** - Verify all functionality works
10. **Deploy to staging** - Test with real project data

---

## References

- Task #69: Enhancement #21: Entity Viewer for Projects
- CLAUDE.md: Entity System Documentation (Lines 611-768)
- task-viewer/main.py: Existing API patterns
- task-viewer/static/index.html: Frontend component architecture
- src/task_mcp/database.py: Entity CRUD implementation

---

**Review Completed:** 2025-11-02 16:00
**Reviewer Signature:** Architecture Review Agent
**Distribution:** Development Team, Project Stakeholders
