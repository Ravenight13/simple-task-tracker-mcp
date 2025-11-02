# API Specification Planning Summary

**Task:** Create comprehensive REST API specification for task viewer frontend
**Date:** 2025-11-02
**Status:** COMPLETED
**Deliverable:** `docs/task-viewer/API_SPECIFICATION.md`

---

## Summary

Created a comprehensive REST API specification for wrapping task-mcp MCP tools with a FastAPI backend. The API provides 6 core endpoints that enable full task management capabilities through a browser-based interface.

---

## API Design Decisions

### 1. RESTful Resource-Based URLs

**Pattern:**
- `/api/projects` - Collection endpoints
- `/api/projects/{id}` - Single resource endpoints
- `/api/tasks/search` - Action endpoints

**Rationale:** Industry-standard REST conventions for predictability and discoverability.

---

### 2. Authentication Strategy

**Approach:** API key via `X-API-Key` header

**Why:**
- Simple for frontend implementation
- No cookie/session management needed
- Can reuse existing API key from MCP server
- Easy to test with curl

**Alternative Considered:** JWT tokens (overkill for internal tool)

---

### 3. Filtering Architecture

**Query Parameter Design:**
```
GET /api/tasks?project_id=xxx&status=todo&priority=high&tags=deployment
```

**Features:**
- Multiple simultaneous filters
- Space-separated tags (partial match)
- Pagination (limit/offset)
- Flexible combinations

**Rationale:** Aligns with task-mcp MCP tool capabilities while providing frontend flexibility.

---

### 4. Error Handling

**Consistent Format:**
```json
{
  "error": "Error Type",
  "message": "Human description",
  "status_code": 400,
  "details": {}
}
```

**HTTP Status Codes:**
- 200 OK - Success
- 400 Bad Request - Invalid parameters
- 401 Unauthorized - Auth failure
- 404 Not Found - Resource missing
- 500 Internal Server Error - Server issues
- 503 Service Unavailable - MCP connection failure

---

## Core Endpoints (6 Total)

### 1. GET /health
- **Purpose:** Uptime monitoring, MCP connection status
- **Auth:** None (public)
- **Response Time Target:** <50ms

### 2. GET /api/projects
- **Purpose:** List all projects from master DB
- **MCP Tool:** `list_projects()`
- **Response Time Target:** <100ms

### 3. GET /api/projects/{id}/info
- **Purpose:** Project details + task statistics
- **MCP Tool:** `get_project_info(workspace_path)`
- **Response Time Target:** <150ms

### 4. GET /api/tasks
- **Purpose:** List/filter tasks with rich query params
- **MCP Tool:** `list_tasks(workspace_path, status, priority, parent_task_id, tags)`
- **Pagination:** limit (default 50, max 100), offset
- **Response Time Target:** <250ms

### 5. GET /api/tasks/{id}
- **Purpose:** Single task details
- **MCP Tool:** `get_task(task_id, workspace_path)`
- **Response Time Target:** <100ms

### 6. GET /api/tasks/search
- **Purpose:** Full-text search across title/description
- **MCP Tool:** `search_tasks(search_term, workspace_path)`
- **Response Time Target:** <300ms

---

## Additional Convenience Endpoints

### GET /api/tasks/next
- **Purpose:** Get actionable tasks (no dependencies)
- **MCP Tool:** `get_next_tasks(workspace_path)`
- **Use Case:** "What can I work on now?" view

### GET /api/tasks/blocked
- **Purpose:** Get all blocked tasks with reasons
- **MCP Tool:** `get_blocked_tasks(workspace_path)`
- **Use Case:** Blocker management dashboard

---

## Data Models

### Project Model
```typescript
{
  id: string;
  workspace_path: string;
  friendly_name: string | null;
  created_at: string;  // ISO 8601
  last_accessed: string;
}
```

### Task Model (14 fields)
```typescript
{
  id: number;
  title: string;
  description: string | null;
  status: "todo" | "in_progress" | "done" | "blocked";
  priority: "low" | "medium" | "high";
  parent_task_id: number | null;
  depends_on: string | null;  // JSON array
  tags: string | null;  // space-separated
  blocker_reason: string | null;
  file_references: string | null;  // JSON array
  created_by: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  deleted_at: string | null;
}
```

### Project Stats Model
```typescript
{
  total_tasks: number;
  by_status: { todo, in_progress, done, blocked };
  by_priority: { high, medium, low };
}
```

---

## Performance Considerations

### Response Time Targets
- **P50:** <100ms
- **P95:** <250ms
- **P99:** <500ms

### Optimization Strategies
1. **MCP Connection Pooling:** Reuse connections to task-mcp
2. **Response Caching:** 5-second TTL for project list
3. **Pagination:** Prevent large result sets from slowing UI
4. **Gzip Compression:** Responses >1KB
5. **Database Query Optimization:** Leverage task-mcp's SQLite indexes

---

## Rate Limiting

**Limits:**
- 100 requests/minute per API key
- 1000 requests/hour per API key

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699123456
```

**Rationale:** Prevent abuse while allowing normal frontend usage patterns.

---

## CORS Configuration

**Development:**
- `http://localhost:8001`
- `http://127.0.0.1:8001`

**Production:**
- `https://tasks.bmcis.net`
- `https://knowledge.bmcis.net` (if co-hosted)

**Allowed Methods:** GET, OPTIONS
**Allowed Headers:** X-API-Key, Content-Type

---

## API Versioning

**Current:** v1.0.0 (in response header: `X-API-Version: 1.0.0`)

**Future:** URL-based versioning for breaking changes (`/v2/api/tasks`)

---

## Complete Frontend Workflow Example

```javascript
// 1. Health check
const health = await fetch('/health');

// 2. Get projects
const { projects } = await fetch('/api/projects', {
  headers: { 'X-API-Key': 'key' }
}).then(r => r.json());

// 3. Select project and get stats
const projectId = projects[0].id;
const { project, stats } = await fetch(
  `/api/projects/${projectId}/info`,
  { headers: { 'X-API-Key': 'key' } }
).then(r => r.json());

// 4. Filter high-priority tasks
const { tasks } = await fetch(
  `/api/tasks?project_id=${projectId}&priority=high`,
  { headers: { 'X-API-Key': 'key' } }
).then(r => r.json());

// 5. Search for deployment tasks
const { tasks: results } = await fetch(
  `/api/tasks/search?q=deployment&project_id=${projectId}`,
  { headers: { 'X-API-Key': 'key' } }
).then(r => r.json());

// 6. Get next actionable tasks
const { tasks: nextTasks } = await fetch(
  `/api/tasks/next?project_id=${projectId}`,
  { headers: { 'X-API-Key': 'key' } }
).then(r => r.json());
```

---

## Future Enhancements (v1.1.0+)

**Planned:**
- WebSocket support for real-time updates
- Task creation/update endpoints (POST/PUT)
- Task tree endpoint (hierarchical subtask view)
- Enhanced filtering (date ranges, multiple tag operators)
- Export endpoints (JSON, CSV, Markdown)
- Bulk operations (batch status updates)
- Task history/audit log
- Dashboard analytics endpoint

**Not Planned (Out of Scope):**
- User authentication system (use API key only)
- File upload/attachment management
- Email notifications
- Calendar integration

---

## Implementation Roadmap

### Phase 1: Core Endpoints (2-3 hours)
- [ ] Health check endpoint
- [ ] Projects endpoints (list, get info)
- [ ] Tasks list endpoint with filtering
- [ ] Task detail endpoint

### Phase 2: Search & Convenience (1-2 hours)
- [ ] Search endpoint
- [ ] Next tasks endpoint
- [ ] Blocked tasks endpoint

### Phase 3: Production Features (1-2 hours)
- [ ] API key authentication middleware
- [ ] Rate limiting
- [ ] CORS configuration
- [ ] Error handling standardization
- [ ] Response compression

### Phase 4: Testing & Documentation (1 hour)
- [ ] API endpoint tests
- [ ] Response format validation
- [ ] Performance benchmarking
- [ ] OpenAPI/Swagger spec generation

**Total Estimated Time:** 5-8 hours

---

## Key Design Principles Applied

1. **REST Best Practices:** Resource-based URLs, proper HTTP verbs and status codes
2. **Consistency:** All responses follow same structure, predictable error format
3. **Flexibility:** Rich filtering without complex query language
4. **Performance:** Sub-500ms targets, pagination, caching strategy
5. **Developer Experience:** Clear error messages, comprehensive examples
6. **Future-Proof:** Versioning strategy, extensible data models

---

## Questions & Considerations

### 1. Should we support PATCH for task updates?
**Decision:** Defer to v1.1.0. Start with read-only API for MVP.

**Rationale:**
- Reduces complexity for initial implementation
- Frontend can use MCP tools directly for updates if needed
- Validate API patterns with read-only first

### 2. How to handle workspace_path vs project_id?
**Decision:** Support both, prefer project_id in frontend.

**Rationale:**
- MCP tools use workspace_path (file system paths)
- Frontend UX better with short IDs
- API can map project_id → workspace_path internally

### 3. Pagination strategy: offset vs cursor?
**Decision:** Use offset/limit for v1.0.0.

**Rationale:**
- Simpler implementation
- Sufficient for expected data volumes (<1000 tasks per project)
- Can migrate to cursor-based in v1.1.0 if needed

### 4. Rate limiting enforcement?
**Decision:** Implement in middleware, use in-memory store.

**Rationale:**
- Lightweight (no Redis needed)
- Sufficient for single-instance deployment
- Can upgrade to distributed cache if needed

---

## Testing Strategy

### Unit Tests
- Parameter validation
- Error handling
- Response format consistency

### Integration Tests
- MCP tool connectivity
- End-to-end workflows
- Error scenarios (MCP down, invalid data)

### Performance Tests
- Response time benchmarks
- Concurrent request handling
- Large result set pagination

### Load Tests
- Rate limit validation
- Connection pool sizing
- Memory usage under load

---

## Documentation Deliverables

**Created:**
- ✅ `docs/task-viewer/API_SPECIFICATION.md` (3,200+ lines)

**Next:**
- Frontend implementation guide
- API client library (optional)
- OpenAPI/Swagger spec (auto-generated)

---

## Success Metrics

**Implementation Quality:**
- All 6 endpoints working correctly
- 100% test coverage for core logic
- Response times meet P95 targets
- Zero breaking changes in v1.0.x

**Developer Experience:**
- Frontend team can implement without clarification
- API spec comprehensive and unambiguous
- Examples cover all common use cases
- Error messages actionable

---

## Summary

The API specification provides a complete blueprint for implementing a production-ready REST API wrapper around task-mcp MCP tools. The design balances simplicity (for rapid implementation) with flexibility (for future expansion). All 6 core endpoints map cleanly to MCP tools while providing frontend-friendly conveniences like filtering, pagination, and search.

**Key Strengths:**
- Comprehensive endpoint coverage
- Clear filtering/pagination patterns
- Consistent error handling
- Rich examples for frontend implementation
- Performance-conscious design

**Ready for:** Immediate backend implementation by development team

---

**Status:** APPROVED FOR IMPLEMENTATION
**Next Steps:** Begin FastAPI backend implementation following specification
