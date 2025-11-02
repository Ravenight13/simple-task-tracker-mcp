# Task Viewer - Deployment & Setup Guide

**Version:** 1.0
**Last Updated:** November 2, 2025
**Status:** Planning Document
**Purpose:** Local development deployment for internal task management tool

---

## Overview

The Task Viewer is a web-based frontend for visualizing and managing tasks from the task-mcp MCP server. It consists of:

- **Backend:** FastAPI server that connects to task-mcp via MCP protocol
- **Frontend:** Static HTML/CSS/JavaScript served by FastAPI
- **Deployment:** Local development environment (developer machine)
- **Future:** Optional Docker/Railway deployment for team sharing

---

## Architecture

```
Developer Machine
  ↓
Task Viewer (FastAPI Server)
  Port: 8001 (default)
  ↓
Task-MCP Server (MCP Protocol)
  Database: SQLite (local workspace)
  ↓
SQLite Database (.task-mcp/tasks.db)
```

**Key Design Principles:**
- Simple local deployment (no Docker required initially)
- Single command to start
- Hot reload for development
- Minimal dependencies
- Easy to share with team later

---

## Directory Structure

```
task-viewer/
├── README.md                    # Project overview and quick start
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── .gitignore                   # Git ignore patterns
│
├── main.py                      # FastAPI app entry point
├── mcp_client.py                # MCP protocol client for task-mcp
├── models.py                    # Pydantic models for API responses
├── api/
│   ├── __init__.py
│   └── routes.py                # API route definitions
│
├── static/
│   ├── index.html               # Main task viewer UI
│   ├── css/
│   │   └── styles.css          # Custom styles
│   └── js/
│       └── app.js              # Frontend JavaScript
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py              # API endpoint tests
│   └── test_mcp_client.py       # MCP client tests
│
└── scripts/
    ├── start_dev.py             # Development server launcher
    └── health_check.py          # Server health check utility
```

**Total Files:** ~15 files
**Total Lines:** ~1,500 lines of code (estimated)

---

## Dependencies

### Python Requirements (`requirements.txt`)

```txt
# Web Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6

# MCP Client
mcp>=0.1.0                       # MCP protocol client
httpx>=0.25.0                    # Async HTTP client

# Data Validation
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Environment Variables
python-dotenv>=1.0.0

# Static File Serving
aiofiles>=23.2.1

# Development Tools (optional)
pytest>=7.4.3
pytest-asyncio>=0.21.1
```

**Dependency Notes:**
- FastAPI for REST API endpoints
- MCP protocol client for task-mcp communication
- Minimal frontend dependencies (vanilla JavaScript)
- Development dependencies optional for production

---

## Installation

### Prerequisites

- Python 3.11 or higher
- Task-MCP server running (or available to connect to)
- pip (Python package manager)
- Git (for version control)

### Step 1: Clone/Create Directory

```bash
# Navigate to project root
cd /Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp

# Create task-viewer directory
mkdir -p task-viewer
cd task-viewer
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows
```

### Step 3: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
pip list | grep mcp
```

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env  # or use your preferred editor
```

**Required Environment Variables (`.env`):**

```bash
# Task Viewer Configuration
VIEWER_HOST=localhost
VIEWER_PORT=8001
VIEWER_RELOAD=true                # Enable hot reload for development

# Task-MCP Connection
TASK_MCP_HOST=localhost
TASK_MCP_PORT=3000                # Default MCP server port
TASK_MCP_TRANSPORT=stdio          # or 'sse' for remote
TASK_MCP_WORKSPACE=/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp

# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=detailed               # simple or detailed

# CORS (if needed for external access)
CORS_ORIGINS=http://localhost:8001,http://127.0.0.1:8001
```

---

## Running Locally

### Option 1: Direct Launch (Recommended for Development)

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Start the FastAPI server
uvicorn main:app --host localhost --port 8001 --reload

# Server starts at: http://localhost:8001
```

**Expected Output:**
```
INFO:     Uvicorn running on http://localhost:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Option 2: Development Script (Convenience Wrapper)

```bash
# Run development startup script
python scripts/start_dev.py

# Includes health checks and auto-restart
```

### Option 3: Production Mode (No Hot Reload)

```bash
# Production mode with Gunicorn (if needed)
gunicorn main:app --workers 2 --bind localhost:8001 --worker-class uvicorn.workers.UvicornWorker
```

### Accessing the Application

1. **Open Browser:** http://localhost:8001
2. **API Documentation:** http://localhost:8001/docs (Swagger UI)
3. **Health Check:** http://localhost:8001/health

---

## MCP Connection Setup

### Connecting to Task-MCP Server

The task viewer connects to the task-mcp server using the MCP protocol. There are two transport modes:

#### Mode 1: STDIO Transport (Local Development)

Used when task-mcp runs as a subprocess on the same machine.

**Configuration (`.env`):**
```bash
TASK_MCP_TRANSPORT=stdio
TASK_MCP_COMMAND=npx
TASK_MCP_ARGS=-y,@cliffclarke/task-mcp
TASK_MCP_WORKSPACE=/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp
```

**MCP Client Code (`mcp_client.py`):**
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def connect_to_task_mcp():
    """Connect to task-mcp via STDIO transport."""
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@cliffclarke/task-mcp"],
        env={"WORKSPACE_PATH": os.getenv("TASK_MCP_WORKSPACE")}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return session
```

#### Mode 2: SSE Transport (Remote Server)

Used when task-mcp is deployed remotely (Railway, etc.).

**Configuration (`.env`):**
```bash
TASK_MCP_TRANSPORT=sse
TASK_MCP_URL=https://task-mcp.example.com/sse
TASK_MCP_API_KEY=your-api-key-here
```

**MCP Client Code:**
```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async def connect_to_task_mcp():
    """Connect to task-mcp via SSE transport."""
    async with sse_client(os.getenv("TASK_MCP_URL")) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return session
```

---

## API Endpoints

The task viewer exposes the following REST API endpoints:

### Task Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List all tasks (with filters) |
| GET | `/api/tasks/{task_id}` | Get single task details |
| POST | `/api/tasks` | Create new task |
| PUT | `/api/tasks/{task_id}` | Update existing task |
| DELETE | `/api/tasks/{task_id}` | Delete task (soft delete) |
| GET | `/api/tasks/{task_id}/tree` | Get task with subtasks |

### Task Queries

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks/search` | Search tasks by text |
| GET | `/api/tasks/next` | Get next actionable tasks |
| GET | `/api/tasks/blocked` | Get all blocked tasks |

### Project Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | List all projects |
| GET | `/api/projects/{workspace}` | Get project info |
| PUT | `/api/projects/{workspace}/name` | Set project name |

### Entity Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/entities` | List all entities |
| GET | `/api/entities/{entity_id}` | Get entity details |
| POST | `/api/entities` | Create new entity |
| PUT | `/api/entities/{entity_id}` | Update entity |
| DELETE | `/api/entities/{entity_id}` | Delete entity |
| GET | `/api/entities/{entity_id}/tasks` | Get tasks for entity |

### Entity-Task Links

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tasks/{task_id}/entities` | Link entity to task |
| GET | `/api/tasks/{task_id}/entities` | Get task entities |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| GET | `/docs` | Swagger API documentation |
| GET | `/` | Serve task viewer frontend |

---

## Frontend Development

### Technology Stack

- **HTML5** - Semantic markup
- **CSS3** - Modern styling with CSS Grid/Flexbox
- **Vanilla JavaScript** - No frameworks (lightweight)
- **Fetch API** - AJAX requests to backend

### Frontend Structure

```javascript
// static/js/app.js

class TaskViewerApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8001/api';
        this.tasks = [];
        this.entities = [];
        this.currentFilter = 'all';
    }

    async initialize() {
        await this.loadTasks();
        this.setupEventListeners();
        this.renderTaskList();
    }

    async loadTasks(filter = {}) {
        const params = new URLSearchParams(filter);
        const response = await fetch(`${this.apiBaseUrl}/tasks?${params}`);
        this.tasks = await response.json();
    }

    // ... more methods
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const app = new TaskViewerApp();
    app.initialize();
});
```

### Hot Reload for Frontend

When using `uvicorn --reload`, changes to static files are automatically detected:

```bash
# Start with hot reload
uvicorn main:app --reload

# Edit static/index.html or static/js/app.js
# Refresh browser to see changes (no server restart needed)
```

### CSS Framework Decision

**Option A: Vanilla CSS** (Recommended)
- Zero dependencies
- Full control over styling
- Lightweight (~5KB)
- Good for internal tool

**Option B: TailwindCSS**
- Utility-first approach
- Faster development
- Larger bundle (~50KB)
- Requires build step

**Decision:** Start with vanilla CSS, migrate to Tailwind if UI complexity grows.

---

## Development Workflow

### 1. Daily Development Cycle

```bash
# Morning: Start development server
cd task-viewer
source .venv/bin/activate
uvicorn main:app --reload

# During day: Edit files
# - Backend changes: main.py, api/routes.py, mcp_client.py
# - Frontend changes: static/index.html, static/js/app.js

# Files auto-reload on save (no restart needed)

# Evening: Commit changes
git add .
git commit -m "feat: add task filtering UI"
git push
```

### 2. Testing Changes

```bash
# Run backend tests
pytest tests/test_api.py -v

# Run MCP client tests
pytest tests/test_mcp_client.py -v

# Manual testing in browser
open http://localhost:8001
```

### 3. Adding New Features

**Example: Adding a new API endpoint**

1. **Define route** (`api/routes.py`):
```python
@router.get("/tasks/priority/{priority}")
async def get_tasks_by_priority(priority: str):
    """Get tasks filtered by priority level."""
    tasks = await mcp_client.list_tasks(priority=priority)
    return tasks
```

2. **Update frontend** (`static/js/app.js`):
```javascript
async filterByPriority(priority) {
    const response = await fetch(
        `${this.apiBaseUrl}/tasks/priority/${priority}`
    );
    this.tasks = await response.json();
    this.renderTaskList();
}
```

3. **Test endpoint**:
```bash
curl http://localhost:8001/api/tasks/priority/high
```

4. **Commit changes**:
```bash
git add api/routes.py static/js/app.js
git commit -m "feat: add priority filtering"
```

---

## Environment Variables Reference

### Complete `.env` File

```bash
# =============================================================================
# Task Viewer Configuration
# =============================================================================

# Server Settings
VIEWER_HOST=localhost
VIEWER_PORT=8001
VIEWER_RELOAD=true                # Enable hot reload (development only)

# Task-MCP Connection
TASK_MCP_HOST=localhost
TASK_MCP_PORT=3000                # Not used for stdio transport
TASK_MCP_TRANSPORT=stdio          # stdio or sse
TASK_MCP_WORKSPACE=/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp

# For SSE Transport (Remote MCP Server)
# TASK_MCP_URL=https://task-mcp.example.com/sse
# TASK_MCP_API_KEY=your-api-key-here

# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=detailed               # simple or detailed

# CORS (Cross-Origin Resource Sharing)
CORS_ORIGINS=http://localhost:8001,http://127.0.0.1:8001
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# Database (if caching locally)
# CACHE_ENABLED=false
# CACHE_DB_PATH=.cache/viewer.db

# Security (for future deployment)
# SECRET_KEY=generate-with-openssl-rand-hex-32
# API_KEY_REQUIRED=false

# Performance
REQUEST_TIMEOUT=30                # API request timeout (seconds)
MAX_CONCURRENT_REQUESTS=10        # Max concurrent MCP calls
```

---

## Troubleshooting

### Issue 1: Server Won't Start

**Symptom:**
```
ERROR: Address already in use
```

**Solution:**
```bash
# Check what's using port 8001
lsof -i :8001

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn main:app --port 8002
```

### Issue 2: Can't Connect to Task-MCP

**Symptom:**
```
ERROR: Failed to connect to task-mcp server
ConnectionRefusedError: [Errno 61] Connection refused
```

**Solutions:**

1. **Check task-mcp is running:**
```bash
# Test task-mcp directly
npx -y @cliffclarke/task-mcp

# Check if process is running
ps aux | grep task-mcp
```

2. **Verify workspace path:**
```bash
# Ensure TASK_MCP_WORKSPACE is correct
echo $TASK_MCP_WORKSPACE
ls -la $TASK_MCP_WORKSPACE/.task-mcp/
```

3. **Check transport mode:**
```bash
# Verify .env settings
cat .env | grep TASK_MCP
```

### Issue 3: Frontend Not Loading

**Symptom:**
- Browser shows 404 for static files
- Styles not applied

**Solutions:**

1. **Check static file serving:**
```bash
# Verify static directory exists
ls -la static/

# Check FastAPI static mount
curl http://localhost:8001/static/index.html
```

2. **Verify file paths in HTML:**
```html
<!-- Correct: relative paths -->
<link rel="stylesheet" href="/static/css/styles.css">
<script src="/static/js/app.js"></script>

<!-- Incorrect: absolute paths -->
<link rel="stylesheet" href="http://localhost:8001/static/css/styles.css">
```

### Issue 4: API Calls Failing (CORS)

**Symptom:**
```
Access to fetch at 'http://localhost:8001/api/tasks' from origin
'http://localhost:8001' has been blocked by CORS policy
```

**Solution:**

Add CORS middleware in `main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 5: Hot Reload Not Working

**Symptom:**
- Changes to Python files don't reload server
- Frontend changes not reflected

**Solutions:**

1. **Backend reload:**
```bash
# Ensure --reload flag is set
uvicorn main:app --reload

# Check uvicorn logs for "Reloading..." message
```

2. **Frontend reload:**
```bash
# Hard refresh browser
Cmd+Shift+R (macOS) or Ctrl+Shift+R (Windows)

# Clear browser cache
# Or use incognito/private window
```

### Issue 6: Python Dependencies Missing

**Symptom:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Verify activation (should show task-viewer venv)
which python

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### Issue 7: MCP Protocol Errors

**Symptom:**
```
ERROR: Invalid MCP response format
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Solutions:**

1. **Check MCP server logs:**
```bash
# Enable debug logging
LOG_LEVEL=DEBUG uvicorn main:app --reload
```

2. **Test MCP connection manually:**
```bash
# Use MCP inspector
npx @modelcontextprotocol/inspector npx @cliffclarke/task-mcp
```

3. **Verify MCP protocol version:**
```python
# Check compatibility in mcp_client.py
print(f"MCP Client Version: {mcp.__version__}")
```

---

## Testing

### Backend Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Frontend Testing (Manual)

**Test Checklist:**

- [ ] Page loads without errors
- [ ] Task list displays correctly
- [ ] Create new task works
- [ ] Update task works
- [ ] Delete task works (with confirmation)
- [ ] Search/filter works
- [ ] Task details modal opens
- [ ] Entity linking works
- [ ] Error messages display properly
- [ ] Loading states show during API calls

### Integration Testing

```bash
# Start both servers
# Terminal 1: Task-MCP
npx -y @cliffclarke/task-mcp

# Terminal 2: Task Viewer
uvicorn main:app --reload

# Terminal 3: Run integration tests
pytest tests/test_integration.py -v
```

---

## Performance Optimization

### Backend Optimization

1. **Connection Pooling:**
```python
# Reuse MCP client connections
from contextlib import asynccontextmanager

@asynccontextmanager
async def mcp_client_pool():
    """Manage MCP client connection pool."""
    client = await connect_to_task_mcp()
    try:
        yield client
    finally:
        await client.close()
```

2. **Caching:**
```python
# Cache frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=100)
def get_project_info(workspace: str):
    """Cached project info lookup."""
    return mcp_client.get_project_info(workspace)
```

3. **Async Batch Operations:**
```python
# Process multiple tasks concurrently
import asyncio

async def batch_update_tasks(updates):
    """Update multiple tasks in parallel."""
    tasks = [update_task(task_id, data) for task_id, data in updates]
    return await asyncio.gather(*tasks)
```

### Frontend Optimization

1. **Debounced Search:**
```javascript
// Delay search until user stops typing
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

const debouncedSearch = debounce(searchTasks, 300);
```

2. **Lazy Loading:**
```javascript
// Load tasks on scroll (infinite scroll)
window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
        loadMoreTasks();
    }
});
```

3. **Virtual Scrolling:**
```javascript
// Render only visible tasks (for large lists)
function renderVisibleTasks() {
    const scrollTop = window.scrollY;
    const visibleRange = calculateVisibleRange(scrollTop);
    renderTaskRange(visibleRange.start, visibleRange.end);
}
```

---

## Future Deployment Options

### Option 1: Docker Container

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Usage:**
```bash
# Build image
docker build -t task-viewer:latest .

# Run container
docker run -p 8001:8001 --env-file .env task-viewer:latest
```

### Option 2: Railway Deployment

**railway.toml:**
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
restartPolicyType = "on_failure"
```

**Deployment:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway up
```

### Option 3: Heroku Deployment

**Procfile:**
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Deployment:**
```bash
# Create Heroku app
heroku create task-viewer

# Deploy
git push heroku master

# Set environment variables
heroku config:set TASK_MCP_URL=https://...
```

### Option 4: Team Shared Instance

**Setup for team access:**

1. **Deploy to shared server** (Railway/Heroku)
2. **Add authentication** (API keys or OAuth)
3. **Enable HTTPS** (Let's Encrypt certificate)
4. **Share URL** with team

**Security considerations:**
- Require API key for all requests
- Use HTTPS only
- Rate limiting (prevent abuse)
- Audit logging (track who does what)

---

## Monitoring & Logging

### Application Logs

```python
# main.py
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log requests
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

### Health Monitoring

```python
# Health check endpoint
@app.get("/health")
async def health_check():
    """Server health check with MCP connectivity test."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "mcp_connected": False
    }

    try:
        # Test MCP connection
        async with get_mcp_client() as client:
            await client.ping()
            health_status["mcp_connected"] = True
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["error"] = str(e)

    return health_status
```

### Performance Metrics

```python
# Track API response times
import time
from collections import defaultdict

metrics = defaultdict(list)

@app.middleware("http")
async def track_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    metrics[request.url.path].append(duration)

    # Log slow requests
    if duration > 1.0:
        logger.warning(f"Slow request: {request.url.path} took {duration:.2f}s")

    return response
```

---

## Security Considerations

### 1. API Key Authentication (Future)

```python
# Middleware for API key validation
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Verify API key from request header."""
    if credentials.credentials != os.getenv("VIEWER_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# Protect endpoints
@app.get("/api/tasks", dependencies=[Depends(verify_api_key)])
async def get_tasks():
    ...
```

### 2. Rate Limiting

```python
# Simple rate limiting
from fastapi import Request
from collections import defaultdict
import time

rate_limit_storage = defaultdict(list)

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    """Limit to 100 requests per minute per IP."""
    client_ip = request.client.host
    now = time.time()

    # Clean old entries
    rate_limit_storage[client_ip] = [
        t for t in rate_limit_storage[client_ip]
        if now - t < 60
    ]

    # Check limit
    if len(rate_limit_storage[client_ip]) >= 100:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded"}
        )

    rate_limit_storage[client_ip].append(now)
    return await call_next(request)
```

### 3. Input Validation

```python
# Strict input validation
from pydantic import BaseModel, Field, validator

class TaskCreate(BaseModel):
    """Validated task creation model."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=10000)
    priority: str = Field("medium", pattern="^(low|medium|high)$")

    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
```

### 4. HTTPS Only (Production)

```python
# Redirect HTTP to HTTPS
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

---

## Development Best Practices

### 1. Code Organization

```
api/
  routes.py       # API endpoints only
  dependencies.py # Shared dependencies (auth, db)

core/
  config.py       # Configuration management
  logging.py      # Logging setup

clients/
  mcp_client.py   # MCP protocol client

models/
  tasks.py        # Task models
  entities.py     # Entity models
  responses.py    # API response models
```

### 2. Error Handling

```python
# Consistent error handling
from fastapi import HTTPException

class TaskNotFoundError(HTTPException):
    def __init__(self, task_id: int):
        super().__init__(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )
```

### 3. Git Workflow

```bash
# Feature branch workflow
git checkout -b feat/add-priority-filter
# ... make changes ...
git add .
git commit -m "feat: add priority filter to task list"
git push origin feat/add-priority-filter

# Create PR, review, merge to main
```

### 4. Documentation

```python
# Document all endpoints
@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int) -> TaskResponse:
    """Get a single task by ID.

    Args:
        task_id: Unique task identifier

    Returns:
        TaskResponse: Task details including title, status, priority

    Raises:
        HTTPException: 404 if task not found

    Example:
        GET /api/tasks/42
        Response: {
            "id": 42,
            "title": "Implement search",
            "status": "in_progress",
            ...
        }
    """
    ...
```

---

## Quick Reference Commands

### Development

```bash
# Start server (hot reload)
uvicorn main:app --reload

# Start server (specific port)
uvicorn main:app --port 8002 --reload

# Start with debug logging
LOG_LEVEL=DEBUG uvicorn main:app --reload

# Check server status
curl http://localhost:8001/health
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Test specific endpoint
curl http://localhost:8001/api/tasks
```

### Maintenance

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Check for security issues
pip audit

# Format code
black .
isort .

# Lint code
flake8 .
mypy .
```

---

## Support & Resources

### Documentation

- **FastAPI:** https://fastapi.tiangolo.com/
- **MCP Protocol:** https://modelcontextprotocol.io/
- **Task-MCP:** See task-mcp README

### Project Resources

- **Task Viewer README:** `task-viewer/README.md`
- **API Documentation:** http://localhost:8001/docs
- **MCP Server:** See main project CLAUDE.md

### Getting Help

1. **Check logs:** `logs/app.log`
2. **Review troubleshooting section** (above)
3. **Test MCP connection** manually
4. **Check GitHub issues** (if public repo)

---

## Summary

The Task Viewer is designed for simple local deployment with minimal setup:

1. **Install dependencies:** `pip install -r requirements.txt`
2. **Configure environment:** Copy `.env.example` to `.env`
3. **Start server:** `uvicorn main:app --reload`
4. **Open browser:** http://localhost:8001

**Key Features:**
- FastAPI backend with automatic API docs
- Static HTML/JS frontend (no build step)
- MCP protocol client for task-mcp integration
- Hot reload for rapid development
- Easy to test and deploy

**Future Enhancements:**
- Docker container for consistent deployment
- Railway/Heroku deployment for team sharing
- Authentication and authorization
- WebSocket support for real-time updates
- Advanced filtering and search

---

**Document Version:** 1.0
**Last Updated:** November 2, 2025
**Status:** Planning Complete - Ready for Implementation
**Next Steps:** Implement core files (main.py, mcp_client.py, models.py)
