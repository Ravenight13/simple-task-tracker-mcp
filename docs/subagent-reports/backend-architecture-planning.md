# Backend Architecture Planning Report

**Date:** November 2, 2025
**Agent:** Backend Architecture Planning Subagent
**Task:** Design FastAPI backend for task-mcp web viewer
**Status:** Complete

---

## Executive Summary

Successfully created comprehensive backend architecture planning document for a FastAPI-based REST API that wraps the task-mcp MCP server. The architecture provides a clean, extensible foundation for a web-based task viewer frontend.

**Key Deliverable:** `/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp/docs/task-viewer/BACKEND_ARCHITECTURE.md`

---

## Key Architectural Decisions

### 1. FastMCP Client Integration

**Decision:** Use FastMCP's Client class to programmatically call task-mcp tools

**Rationale:**
- FastMCP provides a well-typed, Pythonic interface for MCP servers
- Supports multiple connection methods (stdio, HTTP, in-memory)
- Automatic transport inference
- Async/await native support
- Perfect for wrapping MCP tools in REST endpoints

**Implementation:**
```python
from fastmcp import Client

async with Client("task-mcp") as client:
    result = await client.call_tool("mcp__task-mcp__list_tasks", {"status": "todo"})
    return result.content[0].text
```

### 2. Three-Layer Architecture

**Decision:** Separate concerns into Service, API, and Model layers

**Layers:**
1. **Service Layer** (`services/mcp_client.py`)
   - Manages MCP client connections
   - Handles connection lifecycle
   - Wraps tool calls with error handling
   - Connection pooling/limiting

2. **API Layer** (`api/tasks.py`, `api/entities.py`, `api/projects.py`)
   - REST endpoint definitions
   - Request/response handling
   - HTTP status codes
   - Route organization

3. **Model Layer** (`models/requests.py`, `models/responses.py`)
   - Pydantic request validation
   - Response serialization
   - Type safety
   - Input validation

**Benefits:**
- Clean separation of concerns
- Easy to test each layer independently
- Simple to extend with new endpoints
- Clear dependency flow

### 3. RESTful API Design

**Decision:** Follow REST conventions with standard HTTP methods

**Endpoint Structure:**
- `GET /api/v1/tasks` - List tasks (with filters)
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks/{id}` - Get task by ID
- `PATCH /api/v1/tasks/{id}` - Update task (partial)
- `DELETE /api/v1/tasks/{id}` - Delete task
- Similar patterns for entities and projects

**Rationale:**
- Industry standard conventions
- Easy for frontend developers to understand
- Predictable URL patterns
- Clear HTTP semantics
- RESTful caching benefits

### 4. No Authentication (Phase 1)

**Decision:** Launch without authentication for local development

**Rationale:**
- Internal developer tool
- Runs locally on developer's machine
- No network exposure
- MCP server already provides workspace isolation
- Simplifies initial implementation

**Future Options:**
- Phase 2: API key authentication (simple, effective)
- Phase 3: JWT tokens (if needed for shared deployment)
- Phase 4: OAuth2 (if needed for production)

### 5. CORS Configuration for Local Dev

**Decision:** Allow localhost origins for frontend dev servers

**Allowed Origins:**
- `http://localhost:3000` (React/Next.js)
- `http://localhost:5173` (Vite)
- `http://localhost:8080` (Alternative)

**Rationale:**
- Frontend and backend run on different ports during development
- Browser enforces CORS policy
- Allow credentials for future session support
- Cache preflight requests (1 hour)

### 6. Comprehensive Error Handling

**Decision:** Global exception handlers with consistent error format

**Error Response Format:**
```json
{
  "error": "Resource not found",
  "detail": "Task with id 999 does not exist",
  "status_code": 404
}
```

**HTTP Status Codes:**
- 200 OK - Successful GET/PATCH
- 201 Created - Successful POST
- 204 No Content - Successful DELETE
- 400 Bad Request - Invalid input
- 404 Not Found - Resource not found
- 422 Unprocessable Entity - Validation error
- 500 Internal Server Error - Server/MCP error

**Benefits:**
- Consistent error format across all endpoints
- Easy for frontend to handle errors
- Proper HTTP semantics
- Detailed logging without exposing internals

### 7. Structured Logging

**Decision:** Request logging middleware + structured logs

**What We Log:**
- All incoming requests (method, path, query params)
- All MCP tool calls (tool name, arguments)
- All errors and exceptions
- Response times and status codes
- Request IDs for tracing

**What We Don't Log:**
- Sensitive data (API keys, tokens)
- Personal information
- Full database records (IDs only)

**Logging Levels:**
- DEBUG: MCP tool details, response data
- INFO: Requests, responses, cache operations
- WARNING: Validation errors, not found
- ERROR: MCP failures, unhandled exceptions
- CRITICAL: Service unavailable

### 8. Performance Optimizations

**Key Strategies:**

1. **Connection Limiting**
   - Semaphore to limit concurrent MCP connections
   - Prevents overwhelming the MCP server
   - Default: 5 concurrent connections

2. **Async Operations**
   - All MCP calls are async
   - Use `asyncio.gather()` for parallel operations
   - Example: Fetch task + entities in parallel

3. **Request Timeouts**
   - Default 30-second timeout per MCP call
   - Prevents hanging requests
   - Configurable per environment

4. **Pagination**
   - Default limit: 100 items per page
   - Offset-based pagination
   - Total count included in response

5. **Future: Caching**
   - In-memory cache for read-heavy endpoints
   - 60-second TTL for task lists
   - Cache invalidation on updates

---

## API Endpoint Summary

### Task Endpoints (21 total)

**Core CRUD:**
1. `GET /api/v1/tasks` - List/filter tasks
2. `POST /api/v1/tasks` - Create task
3. `GET /api/v1/tasks/{id}` - Get task by ID
4. `PATCH /api/v1/tasks/{id}` - Update task
5. `DELETE /api/v1/tasks/{id}` - Delete task

**Search & Filter:**
6. `GET /api/v1/tasks/search` - Full-text search
7. `GET /api/v1/tasks/{id}/tree` - Get task with subtasks
8. `GET /api/v1/tasks/blocked` - Get blocked tasks
9. `GET /api/v1/tasks/next` - Get actionable tasks

**Entity Relations:**
10. `GET /api/v1/tasks/{id}/entities` - Get linked entities
11. `POST /api/v1/tasks/{id}/entities/{entity_id}` - Link entity

### Entity Endpoints (18 total)

**Core CRUD:**
1. `GET /api/v1/entities` - List/filter entities
2. `POST /api/v1/entities` - Create entity
3. `GET /api/v1/entities/{id}` - Get entity by ID
4. `PATCH /api/v1/entities/{id}` - Update entity
5. `DELETE /api/v1/entities/{id}` - Delete entity

**Search & Relations:**
6. `GET /api/v1/entities/search` - Full-text search
7. `GET /api/v1/entities/{id}/tasks` - Get linked tasks

### Project Endpoints (3 total)

1. `GET /api/v1/projects` - List projects
2. `GET /api/v1/projects/{path}/info` - Get project stats
3. `PATCH /api/v1/projects/{path}/name` - Set friendly name

**Total Endpoints:** 21 task + 18 entity + 3 project = **42 endpoints**

---

## Technology Stack

### Core Framework
- **FastAPI 0.104+** - Modern async web framework
- **Uvicorn** - ASGI server with auto-reload
- **Pydantic 2.5+** - Data validation and serialization
- **FastMCP 0.2+** - MCP client for calling tools

### Development Tools
- **pytest** - Unit and integration testing
- **black** - Code formatting
- **ruff** - Linting
- **httpx** - HTTP client (for TestClient)

### Python Version
- **Python 3.11+** - For modern async features

---

## File Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── config.py                  # Configuration management
├── requirements.txt           # Dependencies
├── .env                       # Environment variables
├── .env.example              # Environment template
├── models/
│   ├── __init__.py
│   ├── requests.py           # Pydantic request models
│   └── responses.py          # Pydantic response models
├── api/
│   ├── __init__.py
│   ├── tasks.py              # Task endpoints
│   ├── entities.py           # Entity endpoints
│   └── projects.py           # Project endpoints
├── services/
│   ├── __init__.py
│   └── mcp_client.py         # FastMCP client wrapper
├── middleware/
│   ├── __init__.py
│   ├── cors.py               # CORS configuration
│   └── error_handler.py      # Global error handling
├── utils/
│   ├── __init__.py
│   └── logging.py            # Logging configuration
└── tests/
    ├── __init__.py
    ├── test_mcp_service.py   # Service layer tests
    ├── test_api.py           # API endpoint tests
    └── conftest.py           # pytest fixtures
```

**Total Files:** ~20 files, ~2,000-2,500 lines of code

---

## Implementation Priorities

### Phase 1: MVP (Week 1)

1. Core application setup
   - `main.py` - FastAPI app
   - `config.py` - Settings
   - `requirements.txt` - Dependencies

2. MCP client service
   - `services/mcp_client.py` - Client wrapper
   - Connection lifecycle management
   - Error handling

3. Task endpoints (highest priority)
   - `api/tasks.py` - All task endpoints
   - `models/requests.py` - Request models
   - `models/responses.py` - Response models

4. Error handling
   - `middleware/error_handler.py` - Global handlers
   - Consistent error responses

5. CORS configuration
   - `middleware/cors.py` - CORS setup

### Phase 2: Full Features (Week 2)

6. Entity endpoints
   - `api/entities.py` - Entity CRUD and search

7. Project endpoints
   - `api/projects.py` - Project management

8. Logging
   - `utils/logging.py` - Structured logging
   - Request logging middleware

9. Testing
   - Unit tests for service layer
   - Integration tests for endpoints

### Phase 3: Polish (Week 3)

10. Performance optimizations
    - Connection pooling
    - Timeouts
    - Caching (if needed)

11. Documentation
    - API documentation
    - Development guide
    - Deployment instructions

12. Deployment
    - Docker configuration (if needed)
    - Production settings

---

## Testing Strategy

### Unit Tests

Test individual components:
- MCP client service (mock MCP server)
- Pydantic models (validation)
- Utility functions

### Integration Tests

Test API endpoints:
- FastAPI TestClient
- End-to-end request/response
- Error cases
- Edge cases

### Test Coverage Goals

- Service layer: 90%+
- API endpoints: 80%+
- Models: 100% (easy with Pydantic)
- Overall: 85%+

---

## Configuration Management

### Environment Variables

```bash
# Server
HOST=127.0.0.1
PORT=8000
RELOAD=true

# MCP Connection
MCP_CONNECTION=task-mcp
MCP_TIMEOUT=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO
JSON_LOGS=false

# Performance
MAX_CONCURRENT_CONNECTIONS=5
REQUEST_TIMEOUT=30
```

### Pydantic Settings

- Type-safe configuration
- Automatic `.env` loading
- Validation on startup
- Default values

---

## Security Considerations

### Current (Phase 1)

- Input validation via Pydantic
- SQL injection prevention (task-mcp uses parameterized queries)
- Path traversal prevention
- No authentication (local only)

### Future (Phase 2+)

- API key authentication
- Rate limiting (100 req/min per IP)
- HTTPS via reverse proxy
- CORS origin whitelist
- Request size limits

---

## Performance Benchmarks (Estimated)

### Target Performance

- **List tasks (100 items):** <100ms
- **Create task:** <50ms
- **Get task by ID:** <20ms
- **Search tasks:** <200ms
- **Get task tree:** <150ms

### Expected Bottlenecks

1. **MCP connection overhead** - Mitigated by connection pooling
2. **Large result sets** - Mitigated by pagination
3. **Complex queries** - Cached when possible

### Scalability

- **Concurrent users:** 10-20 (internal tool)
- **Requests per second:** 50-100
- **Database size:** 1,000-10,000 tasks

More than sufficient for internal developer tool.

---

## Future Enhancements

### Phase 2 (After MVP)

1. **WebSocket Support**
   - Real-time task updates
   - Live collaboration
   - Push notifications

2. **Batch Operations**
   - Bulk create/update/delete
   - Import from CSV/JSON
   - Export to various formats

3. **Advanced Filtering**
   - Complex query builder
   - Saved filters
   - Custom views

### Phase 3 (Production Features)

4. **Authentication**
   - API key or JWT
   - User management
   - Access control

5. **Analytics**
   - Task completion metrics
   - Time tracking
   - Productivity insights

6. **Monitoring**
   - Prometheus metrics
   - Health checks
   - Performance monitoring

---

## Risks & Mitigations

### Risk 1: MCP Connection Instability

**Risk:** MCP server crashes or becomes unresponsive

**Mitigation:**
- Automatic reconnection logic
- Circuit breaker pattern
- Health check endpoint
- Graceful degradation

### Risk 2: Performance Under Load

**Risk:** Slow responses with many concurrent users

**Mitigation:**
- Connection pooling (5 concurrent)
- Request timeouts (30s)
- Pagination (100 items max)
- Caching for read-heavy operations

### Risk 3: Breaking API Changes

**Risk:** task-mcp changes tool signatures

**Mitigation:**
- API versioning (`/api/v1/`)
- Comprehensive tests
- Tool signature validation
- Graceful error handling

---

## Open Questions

### 1. MCP Connection Method

**Question:** Should we connect to task-mcp via:
- A) CLI command (`task-mcp`)
- B) HTTP/SSE if task-mcp runs as server
- C) In-memory for development

**Recommendation:** Start with CLI (A), make configurable for future

### 2. Authentication Timeline

**Question:** When should we add authentication?

**Recommendation:**
- Phase 1: No auth (local only)
- Phase 2: API key if deployed to shared server
- Phase 3: JWT/OAuth2 if needed for production

### 3. Caching Strategy

**Question:** Should we implement caching in Phase 1?

**Recommendation:**
- Phase 1: No caching (YAGNI)
- Phase 2: Add if performance tests show need
- Use in-memory cache (simple, effective)

### 4. Deployment Target

**Question:** Where will this backend run?

**Current:** Local development only
**Future:** Could deploy to:
- Docker container
- Cloud service (Railway, Render, Fly.io)
- VPS

---

## Success Criteria

### MVP Success

1. All core task endpoints working
2. Entity and project endpoints implemented
3. Error handling comprehensive
4. CORS configured for local dev
5. Basic logging in place
6. API documentation generated
7. Integration tests passing

### Production Success (Future)

1. Authentication implemented
2. Performance targets met (<100ms p95)
3. Monitoring/alerting configured
4. Comprehensive test coverage (85%+)
5. Production deployment working
6. User documentation complete

---

## Timeline Estimate

### Week 1: MVP
- Day 1-2: Core setup + MCP client service (8 hours)
- Day 3-4: Task endpoints (10 hours)
- Day 5: Error handling + CORS (4 hours)

**Total:** ~22 hours

### Week 2: Full Features
- Day 1-2: Entity endpoints (6 hours)
- Day 3: Project endpoints (4 hours)
- Day 4-5: Testing + logging (10 hours)

**Total:** ~20 hours

### Week 3: Polish
- Day 1-2: Performance optimization (6 hours)
- Day 3-4: Documentation (6 hours)
- Day 5: Deployment setup (4 hours)

**Total:** ~16 hours

**Grand Total:** ~58 hours (~2 weeks full-time)

---

## Recommendations

### Immediate Next Steps

1. **Review this architecture doc** - Get feedback from team
2. **Create project structure** - Set up directories and files
3. **Implement core MCP service** - Critical foundation
4. **Build task endpoints first** - Highest priority
5. **Add tests early** - TDD approach prevents rework

### Development Approach

1. **Start simple** - Don't over-engineer
2. **Test as you go** - Catch issues early
3. **Document decisions** - Future maintainability
4. **Iterate based on feedback** - Agile development

### Best Practices

1. **Type hints everywhere** - Use Pydantic + mypy
2. **Async/await properly** - Avoid blocking operations
3. **Error handling** - Fail gracefully
4. **Logging** - Debug production issues
5. **Tests** - Prevent regressions

---

## Conclusion

The backend architecture is comprehensive, well-structured, and ready for implementation. Key strengths:

1. **Clean architecture** - Separation of concerns
2. **Type safety** - Pydantic models throughout
3. **Performance** - Async, pooling, timeouts
4. **Extensibility** - Easy to add new endpoints
5. **Error handling** - Consistent, comprehensive
6. **Testing** - Unit + integration tests planned

The architecture provides a solid foundation for a production-quality task viewer API while remaining simple enough for rapid development.

**Status:** Architecture planning complete, ready to begin implementation.

---

## Key Artifacts

1. **Main Document:** `/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp/docs/task-viewer/BACKEND_ARCHITECTURE.md`
2. **This Report:** `/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp/docs/subagent-reports/backend-architecture-planning.md`

---

**Report Generated:** November 2, 2025
**Status:** Complete
**Next Action:** Review architecture and begin implementation
