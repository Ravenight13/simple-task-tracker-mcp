# Task Viewer - Deployment Setup Planning Summary

**Date:** November 2, 2025
**Subagent:** Deployment Planning
**Status:** Complete
**Document Created:** `docs/task-viewer/DEPLOYMENT_SETUP.md`

---

## Overview

Created comprehensive deployment and setup planning document for the Task Viewer web application. The document covers local development deployment, configuration, testing, and future deployment options.

---

## Key Decisions Made

### 1. Architecture Choice
**Decision:** FastAPI + Static HTML/JS frontend
**Rationale:**
- FastAPI provides automatic API documentation (Swagger UI)
- No frontend build step needed (vanilla JavaScript)
- Fast development with hot reload
- Easy to deploy anywhere

### 2. MCP Connection Strategy
**Decision:** Support both STDIO and SSE transports
**Rationale:**
- STDIO for local development (same machine)
- SSE for remote deployment (Railway, etc.)
- Flexible configuration via environment variables

### 3. Dependency Management
**Decision:** Minimal dependencies, no heavy frameworks
**Rationale:**
- FastAPI, uvicorn, MCP client, pydantic (core)
- No React/Vue/Angular (keep it simple)
- Easy to install and maintain

### 4. Development Workflow
**Decision:** Single-command startup with hot reload
**Rationale:**
- `uvicorn main:app --reload` is all you need
- Changes auto-reload (no manual restarts)
- Fast iteration cycle

### 5. Port Configuration
**Decision:** Default to port 8001
**Rationale:**
- Avoids conflict with main MCP server (port 8000)
- Easy to remember (8001 = task viewer)
- Configurable via environment variable

---

## Directory Structure Planned

```
task-viewer/
├── main.py                      # FastAPI app entry point
├── mcp_client.py                # MCP protocol client
├── models.py                    # Pydantic models
├── requirements.txt             # Dependencies
├── .env.example                 # Config template
├── api/
│   └── routes.py               # API endpoints
├── static/
│   ├── index.html              # Task viewer UI
│   ├── css/styles.css          # Styling
│   └── js/app.js               # Frontend logic
├── tests/
│   ├── test_api.py             # API tests
│   └── test_mcp_client.py      # MCP tests
└── scripts/
    ├── start_dev.py            # Dev server launcher
    └── health_check.py         # Health check utility
```

**Total:** ~15 files, ~1,500 lines of code

---

## Environment Variables Specified

### Core Configuration
```bash
VIEWER_HOST=localhost
VIEWER_PORT=8001
VIEWER_RELOAD=true

TASK_MCP_TRANSPORT=stdio        # or 'sse'
TASK_MCP_WORKSPACE=/path/to/workspace

LOG_LEVEL=INFO
```

### MCP Connection (STDIO)
```bash
TASK_MCP_COMMAND=npx
TASK_MCP_ARGS=-y,@cliffclarke/task-mcp
```

### MCP Connection (SSE)
```bash
TASK_MCP_URL=https://task-mcp.example.com/sse
TASK_MCP_API_KEY=your-api-key
```

---

## API Endpoints Planned

### Task Management
- `GET /api/tasks` - List all tasks
- `GET /api/tasks/{id}` - Get single task
- `POST /api/tasks` - Create task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

### Task Queries
- `GET /api/tasks/search?q=...` - Search tasks
- `GET /api/tasks/next` - Next actionable tasks
- `GET /api/tasks/blocked` - Blocked tasks

### Project Management
- `GET /api/projects` - List projects
- `GET /api/projects/{workspace}` - Project info

### Entity Management
- `GET /api/entities` - List entities
- `POST /api/entities` - Create entity
- `GET /api/tasks/{id}/entities` - Get task entities

### System
- `GET /health` - Health check
- `GET /docs` - Swagger documentation
- `GET /` - Serve frontend

---

## Testing Strategy

### Backend Testing
- pytest for API endpoint testing
- pytest-asyncio for async tests
- Coverage reports with pytest-cov

### Frontend Testing (Manual)
- Test checklist provided in documentation
- Browser-based testing workflow
- Integration testing between frontend/backend

### Integration Testing
- Full stack testing (MCP → API → Frontend)
- Test MCP connection modes (STDIO and SSE)

---

## Troubleshooting Guide Included

Documented solutions for common issues:

1. **Port conflicts** - How to find and kill processes
2. **MCP connection failures** - Verify transport mode and workspace
3. **Frontend not loading** - Check static file paths
4. **CORS errors** - Configure CORS middleware
5. **Hot reload not working** - Verify uvicorn flags
6. **Dependency issues** - Activate venv and reinstall
7. **MCP protocol errors** - Debug logging and MCP inspector

Each issue includes:
- Symptom description
- Multiple solution approaches
- Command examples
- Verification steps

---

## Future Deployment Options

### Option 1: Docker
- Dockerfile provided
- Easy containerization
- Consistent environment

### Option 2: Railway
- railway.toml configuration
- One-command deployment
- Auto-scaling

### Option 3: Heroku
- Procfile included
- Git-based deployment
- Free tier available

### Option 4: Team Shared Instance
- Authentication requirements
- HTTPS enforcement
- Security considerations

---

## Security Planning

### Authentication (Future)
- API key middleware planned
- Bearer token authentication
- Endpoint protection pattern

### Rate Limiting
- Simple in-memory rate limiter
- 100 requests/minute per IP
- Configurable limits

### Input Validation
- Pydantic models for all inputs
- Field length constraints
- Pattern validation

### HTTPS Enforcement
- Redirect middleware for production
- Let's Encrypt integration
- Secure cookie settings

---

## Development Best Practices

### Code Organization
- Separate concerns (routes, models, clients)
- Consistent error handling
- Comprehensive documentation

### Git Workflow
- Feature branch development
- Descriptive commit messages
- PR-based reviews

### Logging
- Structured logging with levels
- Request/response logging
- Performance metrics tracking

---

## Dependencies Required

### Core Dependencies
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
mcp>=0.1.0
httpx>=0.25.0
pydantic>=2.5.0
python-dotenv>=1.0.0
aiofiles>=23.2.1
```

### Development Dependencies
```
pytest>=7.4.3
pytest-asyncio>=0.21.1
pytest-cov>=4.1.0
```

**Total:** 10 dependencies (7 core + 3 dev)

---

## Quick Start Commands

### Installation
```bash
cd task-viewer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Development
```bash
uvicorn main:app --reload          # Start server
open http://localhost:8001         # Open in browser
pytest tests/ -v                   # Run tests
```

### Testing
```bash
curl http://localhost:8001/health  # Health check
curl http://localhost:8001/api/tasks  # Test API
```

---

## Performance Optimizations Planned

### Backend
1. **Connection pooling** - Reuse MCP client connections
2. **Caching** - Cache frequently accessed data
3. **Async batch operations** - Parallel task processing

### Frontend
1. **Debounced search** - Reduce API calls while typing
2. **Lazy loading** - Infinite scroll for large lists
3. **Virtual scrolling** - Render only visible items

---

## Monitoring & Logging

### Application Logs
- File-based logging to `logs/app.log`
- Console output for development
- Structured format with timestamps

### Health Monitoring
- `/health` endpoint with MCP connectivity test
- Status indicators (healthy, degraded, unhealthy)
- Version tracking

### Performance Metrics
- Request duration tracking
- Slow request logging (>1 second)
- Endpoint-specific metrics

---

## Documentation Quality

The deployment guide includes:

- **Clear installation steps** - Copy-paste ready commands
- **Environment variable reference** - Complete .env template
- **API endpoint documentation** - All routes with examples
- **Troubleshooting guide** - 7 common issues with solutions
- **Testing instructions** - Backend, frontend, integration
- **Security considerations** - Authentication, rate limiting, validation
- **Future deployment options** - Docker, Railway, Heroku
- **Quick reference commands** - Daily development workflow

**Total Document Length:** 1,200+ lines
**Sections:** 15 major sections
**Code Examples:** 50+ snippets

---

## Questions for Implementation

### MCP Client Implementation
**Question:** Should we use the official MCP Python SDK or create a custom client?
**Recommendation:** Use official SDK (`mcp` package) for compatibility

### Frontend Framework
**Question:** Start with vanilla JS or use a framework?
**Recommendation:** Vanilla JS initially, migrate if complexity grows

### State Management
**Question:** How to manage task state in frontend?
**Recommendation:** Simple class-based approach, no Redux needed

### Real-time Updates
**Question:** Should we support WebSocket for live updates?
**Recommendation:** Defer to Phase 2, use polling initially

---

## Next Steps

1. **Create base files:**
   - `task-viewer/main.py` - FastAPI application
   - `task-viewer/mcp_client.py` - MCP protocol client
   - `task-viewer/models.py` - Pydantic models
   - `task-viewer/requirements.txt` - Dependencies

2. **Implement API routes:**
   - `task-viewer/api/routes.py` - REST endpoints
   - Connect to MCP server via client

3. **Build frontend:**
   - `task-viewer/static/index.html` - UI layout
   - `task-viewer/static/js/app.js` - Frontend logic
   - `task-viewer/static/css/styles.css` - Styling

4. **Add tests:**
   - `task-viewer/tests/test_api.py` - API tests
   - `task-viewer/tests/test_mcp_client.py` - Client tests

5. **Documentation:**
   - `task-viewer/README.md` - Project overview
   - `.env.example` - Configuration template

---

## Success Criteria

The deployment setup is successful if:

1. **Single command startup** - `uvicorn main:app --reload` works
2. **Hot reload works** - File changes auto-reload
3. **MCP connection succeeds** - Can communicate with task-mcp
4. **API endpoints work** - All CRUD operations functional
5. **Frontend loads** - Static files serve correctly
6. **Tests pass** - All pytest tests green
7. **Documentation complete** - Easy for others to set up

---

## Impact & Value

### Developer Experience
- **5-minute setup** - From clone to running server
- **Zero configuration** - Sensible defaults work out of box
- **Fast iteration** - Hot reload enables rapid development

### Maintainability
- **Clear structure** - Easy to find and modify code
- **Well documented** - Inline comments + external docs
- **Test coverage** - Confidence in changes

### Scalability
- **Easy deployment** - Multiple deployment options planned
- **Performance optimized** - Caching and async operations
- **Team ready** - Authentication and security planned

---

## Conclusion

Created comprehensive deployment planning document that covers:
- Complete installation and setup instructions
- Environment configuration with examples
- API endpoint specifications
- Troubleshooting guide for common issues
- Future deployment options
- Security and performance considerations

The plan prioritizes **simplicity and ease of use** for local development while providing a clear path to production deployment.

**Status:** Ready for implementation
**Next:** Create core application files (main.py, mcp_client.py, models.py)

---

**Document Version:** 1.0
**Planning Document:** `docs/task-viewer/DEPLOYMENT_SETUP.md` (1,200+ lines)
**Total Planning Time:** ~2 hours (estimated)
