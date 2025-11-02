# CRITICAL: Workspace Filtering Requirement

**Date:** November 2, 2025
**Issue:** Tasks from multiple projects blending together in task viewer

---

## Problem

Task-mcp supports multi-workspace isolation, but the task viewer frontend currently shows ALL tasks from ALL workspaces without proper filtering.

**User Report:** "I see tasks blended from other projects now"

---

## Root Cause

The task viewer backend (`task-viewer/main.py`) calls MCP tools without explicitly passing `workspace_path` parameter. This causes it to query across all workspaces instead of filtering to the current project.

---

## Solution Required

### Backend Changes (task-viewer/main.py)

**Current (BROKEN):**
```python
# Gets tasks from ALL workspaces
tasks = await mcp_client.call_tool("list_tasks", {
    "status": status_filter,
    "priority": priority_filter
})
```

**Fixed (CORRECT):**
```python
# Gets tasks ONLY from current workspace
tasks = await mcp_client.call_tool("list_tasks", {
    "workspace_path": WORKSPACE_PATH,  # MUST INCLUDE
    "status": status_filter,
    "priority": priority_filter
})
```

### All API Endpoints That Need workspace_path

1. `/api/projects` - list_projects()
2. `/api/projects/{workspace_hash}/info` - get_project_info(workspace_path)
3. `/api/tasks` - list_tasks(workspace_path, ...)
4. `/api/tasks/{task_id}` - get_task(task_id, workspace_path)
5. `/api/tasks/{task_id}/tree` - get_task_tree(task_id, workspace_path)
6. `/api/tasks/blocked` - get_blocked_tasks(workspace_path)
7. `/api/tasks/next` - get_next_tasks(workspace_path)
8. `/api/tasks/search` - search_tasks(search_term, workspace_path)

---

## Workspace Detection Strategy

**Option 1: Configuration (Recommended)**
```python
# task-viewer/.env
WORKSPACE_PATH=/Users/cliffclarke/Claude_Code/task-mcp

# task-viewer/main.py
WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", os.getcwd())
```

**Option 2: URL Parameter**
```python
# Allow user to switch workspaces via URL param
@app.get("/api/tasks")
async def get_tasks(
    workspace_path: Optional[str] = None,
    status: Optional[str] = None
):
    ws = workspace_path or WORKSPACE_PATH
    tasks = await mcp_client.call_tool("list_tasks", {
        "workspace_path": ws,
        "status": status
    })
```

**Option 3: Project Dropdown (Frontend)**
```javascript
// Let user select workspace from dropdown
Alpine.data('taskViewer', () => ({
  currentWorkspace: '/Users/cliffclarke/Claude_Code/task-mcp',
  workspaces: [],

  async switchWorkspace(path) {
    this.currentWorkspace = path;
    await this.loadTasks();
  }
}))
```

---

## Implementation Priority

**HIGH - This breaks multi-project isolation!**

### Quick Fix (1 hour)
1. Add `WORKSPACE_PATH` to task-viewer/.env
2. Add `workspace_path` parameter to all 8 MCP tool calls in main.py
3. Test with multiple workspaces to verify filtering

### Complete Fix (2-3 hours)
1. Quick fix above
2. Add workspace selector dropdown in frontend
3. Allow user to switch between workspaces
4. Display current workspace in UI

---

## Testing Checklist

After fix:
- [ ] Task viewer only shows tasks from selected workspace
- [ ] Switching projects shows different tasks
- [ ] No task ID collisions between workspaces
- [ ] Project selector dropdown shows correct workspace list
- [ ] All 8 API endpoints respect workspace filtering

---

## Related Files

- `task-viewer/main.py` - ALL API endpoints need workspace_path
- `task-viewer/.env` - Add WORKSPACE_PATH config
- `task-viewer/workspace_resolver.py` - Already exists! Use this!
- `session-handoffs/20251102_150500_task-viewer-refinements.md` - Add as refinement

---

## Example Fix

```python
# task-viewer/main.py

from workspace_resolver import resolve_workspace

# At top of file
WORKSPACE_PATH = resolve_workspace()  # Uses existing resolver!

# In each endpoint
@app.get("/api/tasks")
async def get_tasks(status: Optional[str] = None):
    tasks = await mcp_client.call_tool("list_tasks", {
        "workspace_path": WORKSPACE_PATH,  # ADD THIS
        "status": status
    })
    return tasks
```

---

## Critical Note

**EVERY MCP tool call MUST include workspace_path** to maintain project isolation. This is not optional - it's a core feature of task-mcp's multi-workspace support.

Without workspace filtering:
- ❌ Tasks from all projects mixed together
- ❌ Cannot track work per project
- ❌ Task IDs may collide
- ❌ Project selector broken

With workspace filtering:
- ✅ Clean project separation
- ✅ Each workspace has its own task list
- ✅ Can switch between projects easily
- ✅ No cross-contamination

---

**Action Required:** Add workspace filtering as Refinement #6 (HIGH PRIORITY)
