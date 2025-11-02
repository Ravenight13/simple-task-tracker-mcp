# API Specification Review Report

**Date:** November 2, 2025
**Reviewer:** Architecture Review Subagent
**Document Reviewed:** `docs/task-viewer/API_SPECIFICATION.md` v1.0.0
**Status:** ⚠️ NEEDS REVISION (with recommendations)

---

## Executive Summary

The API specification demonstrates **strong RESTful design principles** and **comprehensive documentation**, but has **critical inconsistencies** that must be resolved before implementation. The specification shows professional-grade thinking around error handling, pagination, and filtering, but contains structural conflicts that would cause confusion during development.

**Overall Assessment:** 7.5/10 (Good foundation, needs alignment fixes)

**Recommendation:** APPROVE with REQUIRED REVISIONS (detailed below)

---

## Critical Issues Requiring Resolution

### 🔴 Issue 1: Base URL Path Inconsistency

**Problem:** API spec uses `/api/` prefix, but backend architecture uses `/api/v1/`

**API Spec (line 241):**
```
http://localhost:8000/api/
```

**Backend Arch (line 242):**
```
http://localhost:8000/api/v1/
```

**Impact:** HIGH - Will cause 404 errors when frontend connects to backend

**Resolution Required:**
- Choose ONE approach and standardize across all docs
- **Recommendation:** Use `/api/` (no version in URL initially)
  - Simpler for v1.0
  - Add `/v2/` prefix when breaking changes needed
  - Backend arch pattern is over-engineered for internal tool

**Action:** Update BACKEND_ARCHITECTURE.md to match `/api/` prefix

---

### 🔴 Issue 2: Project ID Type Mismatch

**Problem:** Projects have inconsistent identifier types across docs

**API Spec (line 161):**
```json
{
  "id": "1e7be4ae",  // ← String hash ID
  "workspace_path": "/Users/...",
  "friendly_name": "..."
}
```

**Backend Arch (line 733):**
```http
GET /api/v1/projects/{workspace_path}/info  // ← Uses workspace_path as ID
```

**Impact:** HIGH - Unclear which field is the primary identifier

**Current Behavior Analysis:**
- task-mcp `list_projects` returns projects with hash IDs
- task-mcp `get_project_info` expects workspace_path parameter
- API spec uses `project_id` for filtering tasks
- Backend uses `workspace_path` for project endpoints

**Resolution Required:**
Choose ONE approach:

**Option A: Use project hash ID (RECOMMENDED)**
```http
GET /api/projects/{project_id}/info
GET /api/tasks?project_id=1e7be4ae
```
- More RESTful (stable, short identifiers)
- Better for URLs
- Requires mapping layer in backend

**Option B: Use workspace_path**
```http
GET /api/projects/{workspace_path}/info
GET /api/tasks?workspace_path=/Users/...
```
- No mapping needed
- URL encoding issues with paths
- Less RESTful (long, unstable identifiers)

**Recommendation:** Option A (hash IDs) with backend mapping to workspace_path when calling MCP

**Action:** Update all endpoints to consistently use `project_id`

---

### 🟡 Issue 3: Port Number Inconsistency

**Problem:** Different ports specified across documents

**API Spec (line 30-31):**
```
Base URL: http://localhost:8001 (development)
```

**Backend Arch (line 241-242, 1432):**
```
Base URL: http://localhost:8000
PORT: int = 8000
```

**Impact:** MEDIUM - Confusion during setup, connection errors

**Resolution:** Choose one port and standardize
- **Recommendation:** Use 8001 (avoids conflicts with common dev servers)
- Update backend config.py default to 8001

**Action:** Update BACKEND_ARCHITECTURE.md to use port 8001

---

### 🟡 Issue 4: Missing CRUD Operations

**Problem:** API spec claims "read-only viewer" but backend arch has full CRUD

**API Spec:** Only GET endpoints (no POST/PATCH/DELETE)

**Backend Arch:** Full CRUD defined (lines 299-432)
- POST /api/v1/tasks (create)
- PATCH /api/v1/tasks/{task_id} (update)
- DELETE /api/v1/tasks/{task_id} (delete)

**Frontend Arch (line 38-40):**
- "Not a full CRUD interface (read-only viewer)"
- But mentions "Future: Task creation UI"

**Impact:** MEDIUM - Unclear requirements, wasted implementation effort

**Resolution Required:**
Clarify the MVP scope:

**Recommendation for v1.0 (MVP):**
- READ-ONLY viewer (API spec is correct)
- No task creation/editing in frontend
- Users continue using Claude Desktop for task management

**Recommendation for v1.1+ (Future):**
- Add POST /api/tasks (task creation)
- Add PATCH /api/tasks/:id (status updates)
- Keep DELETE as admin-only or omit

**Action:** Update BACKEND_ARCHITECTURE.md to mark POST/PATCH/DELETE as "Phase 2"

---

## Positive Findings

### ✅ Excellent RESTful Design

**Proper HTTP Methods:**
- GET for retrieval (idempotent)
- Consistent use of query parameters for filtering

**Proper Status Codes:**
- 200 OK for success
- 400 Bad Request for validation errors
- 401 Unauthorized for auth failures
- 404 Not Found for missing resources
- 500 Internal Server Error for server failures
- 503 Service Unavailable for MCP failures

**Resource-Based URLs:**
- `/api/projects` - collection
- `/api/projects/{id}/info` - resource detail
- `/api/tasks` - collection with filters
- `/api/tasks/{id}` - resource detail

**Rating:** 9/10 (excellent adherence to REST principles)

---

### ✅ Comprehensive Error Handling

**Consistent Error Format (lines 64-75):**
```json
{
  "error": "Error Type",
  "message": "Human-readable description",
  "status_code": 400,
  "details": { "field": "context" }
}
```

**Benefits:**
- Frontend can reliably parse errors
- Includes both machine-readable (status_code) and human-readable (message) info
- Optional details field for validation errors

**Edge Cases Covered:**
- MCP server unavailable (503)
- Invalid query parameters (400)
- Resource not found (404)
- Rate limiting (429)

**Rating:** 10/10 (excellent error design)

---

### ✅ Strong Filtering & Pagination

**Query Parameters (lines 256-264):**
- `status` - enum filter
- `priority` - enum filter
- `parent_task_id` - relationship filter
- `tags` - text filter (partial match)
- `limit` - pagination (default: 50, max: 100)
- `offset` - pagination offset

**Search Endpoint (lines 383-444):**
- Full-text search on title + description
- Can combine with project filter
- Includes relevance scoring

**Specialized Endpoints:**
- `/api/tasks/next` - actionable tasks (no dependencies)
- `/api/tasks/blocked` - blocked tasks with reasons

**Benefits:**
- Frontend can build complex UIs
- Performance-friendly (pagination prevents huge payloads)
- Good balance of flexibility vs. simplicity

**Rating:** 9/10 (excellent filtering design)

---

### ✅ Performance Considerations

**Rate Limiting (lines 87-108):**
- 100 requests/minute per API key
- 1000 requests/hour per API key
- Proper 429 response with retry_after

**Response Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699123456
```

**Caching Strategy (line 663):**
- 5-second TTL for project list
- Response caching planned

**Performance Targets (lines 656-660):**
- P50 < 100ms
- P95 < 250ms
- P99 < 500ms

**Optimization Strategies:**
- MCP connection pooling
- Database query optimization
- Gzip compression for >1KB responses

**Rating:** 9/10 (strong performance thinking)

---

### ✅ Clear Data Models

**TypeScript-Style Schemas (lines 536-589):**
```typescript
interface Task {
  id: number;
  title: string;
  description: string | null;
  status: "todo" | "in_progress" | "done" | "blocked";
  priority: "low" | "medium" | "high";
  // ... all fields documented
}
```

**Benefits:**
- Frontend developers know exact shapes
- Can auto-generate TypeScript types
- Clear nullability contracts

**Rating:** 10/10 (excellent type documentation)

---

### ✅ Security Design

**API Key Authentication (lines 43-58):**
- X-API-Key header (simple, appropriate for internal tool)
- Proper 401 responses
- All endpoints protected except /health

**CORS Configuration (lines 670-685):**
- Explicit allowed origins
- Proper method restrictions (GET, OPTIONS)
- Production-ready HTTPS origins planned

**Future Considerations:**
- No authentication for MVP (local dev)
- API keys for shared deployment
- JWT/OAuth2 reserved for full production

**Rating:** 8/10 (appropriate for internal tool, room for production hardening)

---

## Completeness Assessment

### ✅ Core Functionality Covered

**Projects:**
- [x] List all projects
- [x] Get project info with stats
- [ ] Set project name (documented but not in endpoints list)

**Tasks:**
- [x] List tasks with filters
- [x] Get single task
- [x] Search tasks (full-text)
- [x] Get next actionable tasks
- [x] Get blocked tasks
- [ ] Get task tree (mentioned in backend, missing from API spec)

**Entities:**
- [ ] MISSING from API spec entirely
- [ ] Backend arch has full entity CRUD (lines 544-718)
- [ ] Frontend doesn't mention entities

**Impact:** MEDIUM - Unclear if entities are v1.0 or future

**Resolution:** Clarify entity endpoints scope
- If v1.0: Add to API spec
- If future: Remove from backend arch Phase 1

---

### ⚠️ Missing Endpoints

**From Backend Arch but NOT in API Spec:**

1. **GET /api/tasks/{task_id}/tree** (line 460-488)
   - Get task with nested subtasks
   - Useful for hierarchical display
   - **Recommendation:** Add to API spec if supporting subtasks in v1.0

2. **PATCH /api/projects/{project_id}/name** (line 778-791)
   - Set project friendly name
   - Mentioned in spec but no endpoint definition
   - **Recommendation:** Add endpoint spec or remove from scope

3. **All entity endpoints** (lines 544-718)
   - 9 entity-related endpoints in backend arch
   - Zero mention in API spec
   - **Recommendation:** Clarify if entities are v1.0 or deferred

**Action:** Add missing endpoints to API spec OR mark as Phase 2 in backend arch

---

### ✅ Documentation Quality

**Excellent Documentation:**
- Clear examples for every endpoint
- Request/response schemas
- Error cases documented
- Query parameter types specified
- curl examples provided
- Complete frontend workflow example (lines 595-651)

**Minor Gaps:**
- No OpenAPI/Swagger spec (FastAPI auto-generates this)
- No authentication flow diagram
- No sequence diagrams for complex flows

**Rating:** 9/10 (excellent human-readable docs)

---

## Cross-Reference Analysis

### Backend Architecture Alignment

**✅ Matches:**
- FastAPI framework
- MCP client integration pattern
- Error handling approach
- Pydantic models for validation
- CORS configuration

**❌ Mismatches:**
- URL prefix (`/api/` vs `/api/v1/`)
- Port number (8001 vs 8000)
- CRUD scope (read-only vs full CRUD)
- Entity endpoints (missing from API spec)

**Action Required:** Align specs before implementation starts

---

### Frontend Architecture Alignment

**✅ Frontend Needs Met:**
- List projects → Project selector dropdown
- Filter tasks by status/priority → Filter chips
- Search tasks → Search input
- Get task details → Modal view
- Pagination support → Infinite scroll or page controls

**✅ Performance Aligned:**
- API targets <500ms P99
- Frontend expects <100ms perceived latency
- Both use caching strategies

**❌ Potential Gaps:**
1. Frontend wants task counts by status (for filter badges)
   - API provides this in `/api/projects/{id}/info`
   - But not in `/api/tasks` response
   - **Recommendation:** Add `meta` object to task list response:
   ```json
   {
     "tasks": [...],
     "total": 24,
     "meta": {
       "status_counts": { "todo": 10, "done": 14 },
       "priority_counts": { "high": 5, "medium": 12, "low": 7 }
     }
   }
   ```

2. Frontend shows relative timestamps ("2h ago")
   - API returns ISO 8601 strings
   - Frontend handles formatting (correct approach)

**Rating:** 8/10 (good alignment, minor enhancements possible)

---

## Security Assessment

### ✅ Appropriate for Internal Tool

**Current Design:**
- API key authentication (simple, effective)
- No PII exposure (task data is internal)
- CORS restricted to known origins
- Rate limiting prevents abuse

**No Critical Security Issues Identified**

### 🟡 Production Hardening Recommendations (Future)

**If deploying to shared server:**

1. **Add Request ID Header**
   ```
   X-Request-ID: uuid-v4
   ```
   - Aids debugging
   - Correlate frontend/backend logs

2. **Add API Version Header**
   ```
   X-API-Version: 1.0.0
   ```
   - Already planned (line 690-691)

3. **HTTPS Enforcement**
   - Redirect HTTP → HTTPS
   - HSTS headers
   - Already planned for production (line 677-678)

4. **Input Validation**
   - Already using Pydantic models (backend arch)
   - SQL injection prevented (parameterized queries)
   - Path traversal prevented (workspace validation)

**Rating:** 8/10 (secure for internal tool, standard production hardening needed later)

---

## RESTful Design Quality Analysis

### ✅ Strengths

1. **Resource-Based URLs**
   - `/api/projects` not `/api/getProjects`
   - `/api/tasks/{id}` not `/api/task?id=123`

2. **Proper HTTP Methods**
   - GET for retrieval (read-only spec is correct)
   - Idempotent operations

3. **Stateless Design**
   - No session state required
   - API key in header (not cookies)

4. **Proper Status Codes**
   - 200, 400, 401, 404, 500, 503 all used correctly

5. **HATEOAS (Partial)**
   - Includes related IDs (parent_task_id, depends_on)
   - Could add `_links` for full HATEOAS

6. **Pagination**
   - Offset-based (simple, works for this use case)
   - Could upgrade to cursor-based for large datasets

### 🟡 Minor Improvements

1. **Consistency in List Responses**

   **Current:**
   ```json
   // /api/projects
   { "projects": [...], "total": 2 }

   // /api/tasks
   { "tasks": [...], "total": 24, "limit": 50, "offset": 0 }
   ```

   **Recommendation:** Standardize envelope:
   ```json
   {
     "data": [...],
     "meta": {
       "total": 24,
       "limit": 50,
       "offset": 0,
       "status_counts": { ... }
     }
   }
   ```

2. **Add ETag Support (Future)**
   ```
   ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
   If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"
   ```
   - Enables conditional requests
   - Reduces bandwidth

3. **Add Last-Modified Header**
   ```
   Last-Modified: Sat, 02 Nov 2025 10:30:00 GMT
   ```
   - Better caching

**Rating:** 8.5/10 (strong REST fundamentals, minor polish possible)

---

## Recommendations Summary

### 🔴 REQUIRED Changes (Block Implementation)

1. **Standardize URL prefix:** `/api/` across all docs
2. **Standardize port:** 8001 across all docs
3. **Resolve project ID type:** Use hash IDs, map to workspace_path in backend
4. **Clarify CRUD scope:** Mark POST/PATCH/DELETE as Phase 2 or v1.0
5. **Entity endpoints:** Add to spec OR mark as Phase 2

### 🟡 RECOMMENDED Improvements (Before v1.0)

6. **Add task counts to list response:** Include status/priority counts
7. **Add missing endpoints:** `/api/tasks/{id}/tree`, `/api/projects/{id}/name`
8. **Standardize response envelope:** Consistent `data` + `meta` structure
9. **Add request ID header:** For debugging correlation
10. **Document workspace_path encoding:** How to handle paths with spaces in URLs

### 🟢 OPTIONAL Enhancements (Nice to Have)

11. **Add ETag support:** For conditional requests
12. **Add Last-Modified header:** Better caching
13. **Upgrade to cursor-based pagination:** If task lists exceed 1000 items
14. **Add bulk operations:** If frontend needs batch updates
15. **Add OpenAPI 3.0 spec:** FastAPI auto-generates, include in docs

---

## Questions Requiring Clarification

### For Project Owner (Cliff Clarke)

1. **Entity endpoints in v1.0?**
   - Backend arch has 9 entity endpoints
   - API spec has zero
   - Frontend doesn't mention entities
   - **Decision needed:** Include in v1.0 or defer to v1.1?

2. **Task creation in v1.0?**
   - API spec is read-only
   - Backend arch has POST /tasks
   - Frontend says "not a full CRUD interface"
   - **Decision needed:** Read-only viewer or allow task creation?

3. **Task hierarchy display?**
   - task-mcp supports parent_task_id and subtasks
   - Frontend arch shows subtasks in modal
   - API spec missing `/api/tasks/{id}/tree` endpoint
   - **Decision needed:** Show hierarchy in v1.0?

4. **Project renaming?**
   - Mentioned in spec but no endpoint defined
   - **Decision needed:** Include PATCH /projects/{id}/name?

### For Implementation Team

5. **URL encoding for workspace_path?**
   - How to handle: `/Users/cliff/My Documents/project`
   - URL encode spaces? Base64 encode entire path?
   - **Recommendation:** Use hash IDs, avoid paths in URLs

6. **Rate limiting implementation?**
   - Spec defines limits but no implementation notes
   - **Recommendation:** Use slowapi or redis-based limiter

---

## Implementation Readiness

### 🟢 Ready to Implement (After Revisions)

**Core Read-Only Viewer:**
- GET /api/projects
- GET /api/projects/{id}/info
- GET /api/tasks (with filters)
- GET /api/tasks/{id}
- GET /api/tasks/search
- GET /api/tasks/next
- GET /api/tasks/blocked

**Once Critical Issues Resolved:**
- Align URL prefixes
- Align port numbers
- Clarify project ID usage
- Confirm read-only scope

**Estimated Implementation Time:** 8-12 hours
- 3h: FastAPI app structure + MCP client
- 2h: Project endpoints
- 3h: Task endpoints
- 2h: Error handling, CORS, rate limiting
- 2h: Testing

---

### 🟡 Needs Requirements Clarification

**Entity Management:**
- All entity endpoints
- Task-entity relationships
- **Blocked until:** Entity scope decision

**Task Creation/Editing:**
- POST /api/tasks
- PATCH /api/tasks/{id}
- DELETE /api/tasks/{id}
- **Blocked until:** CRUD scope decision

**Task Hierarchy:**
- GET /api/tasks/{id}/tree
- Subtask display in frontend
- **Blocked until:** Hierarchy display decision

---

## Final Verdict

### Overall Assessment: ⚠️ NEEDS REVISION

**Strengths:**
- Excellent REST design principles (9/10)
- Comprehensive error handling (10/10)
- Strong filtering & pagination (9/10)
- Clear documentation (9/10)
- Appropriate security for internal tool (8/10)

**Critical Issues:**
- URL prefix inconsistency (blocking)
- Port number inconsistency (blocking)
- Project ID type ambiguity (blocking)
- CRUD scope unclear (blocking)
- Entity endpoints missing (blocking)

**Recommendation:**
1. ✅ **APPROVE API specification design quality** (excellent RESTful design)
2. ⚠️ **REQUIRE ALIGNMENT** with backend/frontend architecture docs
3. ⏸️ **BLOCK IMPLEMENTATION** until critical issues resolved
4. 📋 **CLARIFY SCOPE** for entities, CRUD, hierarchy features

**Estimated Time to Resolve Issues:** 2-3 hours
- Review all three architecture docs together
- Standardize URL/port across docs
- Define v1.0 scope clearly
- Update API spec with missing endpoints OR mark as Phase 2

---

## Next Steps

### Immediate Actions Required

1. **Call alignment meeting** (30 min)
   - Review this report
   - Decide on critical issues
   - Define v1.0 scope clearly

2. **Update documents** (1-2 hours)
   - Standardize URL prefix → `/api/`
   - Standardize port → `8001`
   - Choose project ID approach → hash IDs
   - Mark Phase 1 vs Phase 2 features

3. **Validate alignment** (30 min)
   - Re-read all three docs
   - Confirm consistency
   - Get sign-off from owner

4. **Begin implementation** (8-12 hours)
   - Start with read-only core
   - Add features incrementally
   - Test at each milestone

---

## Appendix: Specific Line References

### URL Prefix Issues
- API_SPEC line 30-31: `http://localhost:8001`
- API_SPEC line 150: `GET /api/projects`
- BACKEND_ARCH line 241: `http://localhost:8000/api/v1/`
- BACKEND_ARCH line 1536: `app.include_router(tasks.router, prefix="/api/v1/tasks")`

### Project ID Issues
- API_SPEC line 161: `"id": "1e7be4ae"`
- API_SPEC line 198: `GET /api/projects/{project_id}/info`
- BACKEND_ARCH line 750: `GET /api/v1/projects/{workspace_path}/info`

### CRUD Scope Issues
- API_SPEC: Only GET methods defined
- BACKEND_ARCH line 299: `POST /api/v1/tasks` (create)
- BACKEND_ARCH line 379: `PATCH /api/v1/tasks/{task_id}` (update)
- FRONTEND_ARCH line 38: "Not a full CRUD interface (read-only viewer)"

### Entity Endpoints
- API_SPEC: No entity endpoints
- BACKEND_ARCH lines 544-718: 9 entity endpoints
- FRONTEND_ARCH: No mention of entities

---

**Report Status:** COMPLETE
**Confidence Level:** HIGH
**Review Time:** 90 minutes
**Recommendation:** Address critical issues before implementation

**Reviewer Signature:** Architecture Review Subagent
**Review Date:** November 2, 2025
