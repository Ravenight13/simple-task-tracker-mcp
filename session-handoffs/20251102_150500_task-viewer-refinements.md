# Session Handoff: Task Viewer Refinements

**Date:** November 2, 2025 3:05 PM
**Project:** task-mcp
**Branch:** feat/task-viewer-refinements
**Status:** READY FOR REFINEMENTS - Core functionality complete, zero errors

---

## Current State

### What's Working ✅
- ✅ Zero console errors (fixed 99 Alpine.js errors)
- ✅ FastAPI backend with 8 GET endpoints
- ✅ Alpine.js + Tailwind CSS frontend
- ✅ API key authentication modal
- ✅ Project selection and task display
- ✅ Status and priority filtering
- ✅ Search functionality
- ✅ Task detail modal
- ✅ Dark mode support
- ✅ Responsive design
- ✅ Focus trapping in modals

### Technical Details
**Backend:** http://localhost:8001
**API Key:** `quJ5dpjJHfhuskKj3CGcTxn5Af6HZ-O9mPkaepvH7fo`
**Main File:** `task-viewer/static/index.html` (842 lines)
**Backend:** `task-viewer/main.py` (522 lines)

### Recent Achievements
- Fixed critical 404 error causing 99 Alpine.js console errors
- Added Alpine.js Focus plugin for accessibility
- Comprehensive Playwright testing suite
- Complete error analysis and verification reports
- Merged to main via PR #6

---

## 🚨 CRITICAL ISSUE DISCOVERED (Must Fix First!)

### Refinement 0: Workspace Filtering Bug ⚠️
**CRITICAL:** Task viewer shows tasks from ALL workspaces instead of filtering to current project!

**Issue:** User reported "I see tasks blended from other projects now"

**Root Cause:**
Backend (task-viewer/main.py) doesn't pass `workspace_path` parameter to MCP tool calls, causing queries across all workspaces instead of filtering to current project.

**Impact:**
- ❌ Tasks from all projects mixed together
- ❌ Cannot track work per project
- ❌ Project isolation completely broken
- ❌ Task IDs may collide between projects

**Solution:**
Add `workspace_path` parameter to all 8 API endpoints in task-viewer/main.py:
1. `/api/projects` - list_projects()
2. `/api/projects/{workspace_hash}/info` - get_project_info(workspace_path)
3. `/api/tasks` - list_tasks(workspace_path, ...)
4. `/api/tasks/{task_id}` - get_task(task_id, workspace_path)
5. `/api/tasks/{task_id}/tree` - get_task_tree(task_id, workspace_path)
6. `/api/tasks/blocked` - get_blocked_tasks(workspace_path)
7. `/api/tasks/next` - get_next_tasks(workspace_path)
8. `/api/tasks/search` - search_tasks(search_term, workspace_path)

**Implementation:**
```python
# Use existing workspace_resolver.py module!
from workspace_resolver import resolve_workspace

WORKSPACE_PATH = resolve_workspace()  # At top of main.py

# In each endpoint, add workspace_path parameter:
tasks = await mcp_client.call_tool("list_tasks", {
    "workspace_path": WORKSPACE_PATH,  # ADD THIS
    "status": status
})
```

**Files to Modify:**
- task-viewer/main.py (all 8 API endpoints)
- task-viewer/.env (add WORKSPACE_PATH config)

**Documentation:** WORKSPACE_FILTERING.md (complete implementation guide)

**Complexity:** Low-Medium (1-2 hours)
**Priority:** CRITICAL - Must fix before other refinements
**Branch:** fix/workspace-filtering (separate branch)
**Task ID:** #38

---

## Refinement Requests (5 Total)

### 1. Refresh Button ⟳
**Request:** "Refresh button that will update the page with the current status of everything"

**Requirements:**
- Manual refresh button in UI (not just browser refresh)
- Fetches latest data from all endpoints
- Updates project list, task counts, and task display
- Visual feedback during refresh (spinner/loading state)
- Handles errors gracefully

**Implementation Approach:**
- Add refresh button to header/toolbar
- Create `refreshAllData()` function in Alpine.js
- Re-fetch projects, tasks, and counts
- Show loading indicator during fetch
- Display success/error toast notification

**Location:** Top-right of header, near dark mode toggle

**Complexity:** Low (1-2 hours)

---

### 2. Task Hierarchy Visualization 🌳
**Request:** "Ability to see the task hierarchy with relationships"

**Requirements:**
- Visualize parent-child relationships between tasks
- Show which tasks are subtasks of others
- Display dependency chains (`depends_on` field)
- Make hierarchy clear and navigable
- Maintain current card-based layout

**Implementation Options:**

**Option A: Tree/Indentation View**
- Indent subtasks under parent tasks
- Expandable/collapsible sections
- Visual connector lines (optional)
- Similar to file explorer UI

**Option B: Visual Graph/Flowchart**
- Interactive node-based visualization
- Shows dependencies with arrows
- Can pan/zoom for large hierarchies
- Requires visualization library (vis.js, cytoscape.js)

**Option C: Hybrid Approach (Recommended)**
- Default: Card view with hierarchy badges
- Alternative: Tree view toggle
- Shows parent task title on subtask cards
- "Show subtasks" expand button on parent cards

**API Support:**
- MCP tools available: `get_task_tree(task_id)` - returns nested subtasks
- Tasks have `parent_task_id` field
- Tasks have `depends_on` JSON array field

**Complexity:** Medium-High (4-8 hours depending on approach)

---

### 3. Blocking Task Indicator 🚫
**Request:** "If something is a 'Blocking' task there should be a red icon on the card indicating it's a blocker for other tasks"

**Requirements:**
- Visual indicator for tasks that block others
- Red icon/badge on task card
- Clear distinction from "blocked" status
- Tooltip/explanation of what it blocks

**Implementation Approach:**

**Backend Logic:**
1. When loading tasks, check each task's dependencies
2. For each task in `depends_on` arrays, mark as "blocker"
3. Return `is_blocker: boolean` and `blocks_tasks: [ids]` in API response

**Frontend Display:**
- Red shield/stop icon in top-right of card
- Badge showing count: "Blocks 3 tasks"
- Hover tooltip: "This task blocks: Task A, Task B, Task C"
- Visual distinction: Red icon for "is blocker", different from yellow/orange "blocked" status

**Color Scheme:**
- 🟥 Red icon = "This task blocks others" (blocker)
- 🟨 Yellow/orange badge = "This task is blocked" (blocked status)

**Location:** Top-right corner of task card, near priority badge

**Complexity:** Low-Medium (2-4 hours)

---

### 4. Task Ordering 📊
**Request:** "I like seeing the order of the tasks - not sure how to handle this one"

**Current Behavior:**
Tasks appear in order returned by API (likely creation order or ID order).

**Clarification Questions:**
- Do you want to **see** the current order (display position number)?
- Do you want to **control** the order (drag-and-drop, manual sorting)?
- Do you want to **persist** a custom order in the database?

**Implementation Options:**

**Option A: Display Position Numbers**
- Show "#1", "#2", "#3" on each card
- Number based on current sort/filter
- No database changes needed
- Read-only visualization

**Option B: Custom Sort Field**
- Add `sort_order` field to tasks table
- Allow manual sorting via drag-and-drop
- Persist order per project
- More complex implementation

**Option C: Multi-Criteria Sorting**
- Sort by: Priority → Status → Creation date
- User can toggle sort criteria
- Visual indicator of current sort
- No drag-and-drop needed

**Recommended (Clarify First):**
Start with **Option A** (display position) plus **Option C** (sort controls) to see if that meets needs before implementing drag-and-drop.

**Complexity:** Low for Option A, Medium for Option C, High for Option B

---

### 5. Expert Suggestions 💡
**Request:** "What suggestions do you have to make this an even better more digestible system?"

**Proposed Enhancements:**

#### A. Visual Improvements
1. **Task Timeline View** - Gantt-chart style view showing task duration/progress
2. **Status Progress Bar** - Visual progress indicator (X/Y tasks done)
3. **Color-Coded Cards** - Different colors for different projects or status
4. **Priority Heat Map** - Visual density map showing high-priority clusters
5. **Task Age Indicator** - Show how long tasks have been in current status

#### B. Data Insights
1. **Task Statistics Dashboard** - Cards showing:
   - Total tasks by status
   - Blocked tasks count
   - Tasks completed this week
   - Average completion time
2. **Dependency Graph Visualization** - Interactive graph showing all task relationships
3. **Bottleneck Detection** - Highlight tasks with most dependencies
4. **Velocity Metrics** - Tasks completed per day/week trend

#### C. Workflow Enhancements
1. **Quick Actions Bar** - Fast buttons for common operations:
   - Mark as done
   - Create subtask
   - Add dependency
   - Change priority
2. **Bulk Operations** - Select multiple tasks for batch updates
3. **Keyboard Shortcuts** - Power-user navigation (j/k for up/down, enter to open)
4. **Task Templates** - Pre-defined task structures for common workflows
5. **Smart Filters** - Saved filter combinations:
   - "My Focus" (high priority + in progress)
   - "Ready to Work" (no blockers + status=todo)
   - "Needs Review" (status=done + no verification)

#### D. Context & Clarity
1. **Breadcrumb Navigation** - Show current filter/view path
2. **Task Preview on Hover** - Quick peek at description without opening modal
3. **Related Tasks Sidebar** - When viewing task, show dependencies and subtasks
4. **Activity Feed** - Recent changes to tasks in current project
5. **Empty State Messages** - Helpful guidance when no tasks match filters

#### E. Advanced Features
1. **Export to CSV/JSON** - Download current filtered task list
2. **Print View** - Optimized layout for printing task reports
3. **URL State** - Shareable URLs that preserve filters/selections
4. **Local Storage** - Remember user preferences (theme, filters, etc.)
5. **Notifications** - Browser notifications for task updates (if API supports WebSocket)

**Recommended Priority (Top 5):**
1. ⭐ **Task Statistics Dashboard** - Quick insights at a glance
2. ⭐ **Quick Actions Bar** - Streamline common operations
3. ⭐ **Keyboard Shortcuts** - Power-user efficiency
4. ⭐ **Smart Filters** - Pre-configured useful views
5. ⭐ **Task Preview on Hover** - Reduce clicks for quick info

---

## Recommended Parallel Subagent Workflow

### Subagent Assignments

**Subagent 1: Refresh Button Specialist**
- **Task:** Implement refresh button with loading states
- **File:** `task-viewer/static/index.html` (add refresh function + button)
- **Output:** Feature implementation + micro-commit
- **Duration:** 1-2 hours

**Subagent 2: Hierarchy Visualization Specialist**
- **Task:** Implement task hierarchy display (tree/indentation view)
- **File:** `task-viewer/static/index.html` (add hierarchy rendering logic)
- **Backend:** Potentially modify `main.py` to add hierarchy metadata
- **Output:** Feature implementation + documentation + micro-commit
- **Duration:** 4-6 hours

**Subagent 3: Blocking Indicator Specialist**
- **Task:** Add blocker detection and red icon indicator
- **File:** `task-viewer/main.py` (backend logic to detect blockers)
- **File:** `task-viewer/static/index.html` (frontend display)
- **Output:** Feature implementation + micro-commit
- **Duration:** 2-3 hours

**Subagent 4: Task Ordering Specialist**
- **Task:** Add position numbers and sort controls
- **File:** `task-viewer/static/index.html` (display + sort UI)
- **Output:** Feature implementation + micro-commit
- **Duration:** 2-3 hours

**Subagent 5: Enhancement Research Specialist**
- **Task:** Research and prototype top 3 suggested enhancements
- **File:** Create prototypes in `task-viewer/prototypes/` directory
- **Output:** Implementation proposals + demos + micro-commit
- **Duration:** 3-4 hours

**Subagent 6: Testing & QA Specialist**
- **Task:** Update Playwright tests for new features
- **File:** `tests/e2e/task-viewer-refinements.spec.ts`
- **Output:** Comprehensive test suite + micro-commit
- **Duration:** 2-3 hours

---

## Execution Strategy

### Phase 1: Independent Features (Parallel)
Run these in parallel as they don't conflict:
- Subagent 1 (Refresh Button)
- Subagent 3 (Blocking Indicator)
- Subagent 4 (Task Ordering)
- Subagent 5 (Enhancement Research)

**Why parallel:** Different parts of codebase, minimal merge conflicts

### Phase 2: Dependent Features (Sequential)
Run after Phase 1 completes:
- Subagent 2 (Hierarchy Visualization) - May need refresh button to work
- Subagent 6 (Testing & QA) - Tests all new features

### Phase 3: Integration
- Merge all feature branches
- Run comprehensive E2E tests
- Fix any integration issues
- Create PR for entire refinements package

---

## Technical Requirements

### For All Subagents

**Must Have:**
- Read existing code first (understand current structure)
- Follow Alpine.js patterns (reactive data, x-directives)
- Maintain Tailwind CSS styling consistency
- Add error handling for all API calls
- Write descriptive commit messages
- Create documentation in comments

**File Writing Protocol:**
- Write implementation to appropriate file
- Test changes work (manual or automated)
- Commit immediately (micro-commit)
- Report back with summary + commit hash

**Testing Checklist:**
- No console errors
- Feature works in light and dark mode
- Responsive on mobile/tablet/desktop
- Keyboard accessible
- Error states handled gracefully

---

## API Reference

### Available MCP Tools

**Task Operations:**
- `list_tasks(workspace_path, status, priority, tags)` - Get filtered tasks
- `get_task(task_id)` - Get single task details
- `get_task_tree(task_id)` - Get task with nested subtasks
- `update_task(task_id, ...)` - Update task fields
- `get_blocked_tasks()` - Get all blocked tasks
- `get_next_tasks()` - Get actionable tasks (no blockers)

**Project Operations:**
- `list_projects()` - Get all projects
- `get_project_info(workspace_path)` - Get project with task counts

**Task Fields:**
- `id`, `title`, `description`, `status`, `priority`
- `parent_task_id` - Parent task ID (for subtasks)
- `depends_on` - JSON array of task IDs this depends on
- `tags`, `blocker_reason`, `file_references`
- `created_at`, `updated_at`, `completed_at`

---

## File Locations

```
task-viewer/
├── main.py                     # FastAPI backend (522 lines)
├── static/
│   ├── index.html             # Frontend (842 lines) - MAIN FILE
│   └── js/
│       └── config.js          # API config
├── mcp_client.py              # MCP tool client
├── models.py                  # Pydantic models
└── requirements.txt           # Python dependencies

tests/
└── e2e/
    ├── task-viewer-real.spec.ts      # Existing E2E tests
    └── task-viewer-refinements.spec.ts  # New tests (to be created)

docs/
└── task-viewer/
    ├── FRONTEND_ARCHITECTURE.md
    ├── BACKEND_ARCHITECTURE.md
    └── API_SPECIFICATION.md
```

---

## Code Patterns to Follow

### Alpine.js Pattern
```javascript
Alpine.data('taskViewer', () => ({
  // State
  tasks: [],
  loading: false,

  // Init
  async init() {
    await this.loadTasks();
  },

  // Methods
  async loadTasks() {
    this.loading = true;
    try {
      const response = await fetch('/api/tasks');
      this.tasks = await response.json();
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      this.loading = false;
    }
  }
}));
```

### Tailwind Styling
```html
<!-- Consistent with existing styles -->
<button class="px-3 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg
               hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors">
  Refresh
</button>
```

### Error Handling
```javascript
try {
  const response = await fetch('/api/endpoint');
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  // Handle success
} catch (error) {
  this.error = error.message;
  console.error('API Error:', error);
}
```

---

## Success Criteria

### For Each Refinement

**Refinement 1 (Refresh Button):**
- ✅ Button visible in header
- ✅ Fetches latest data on click
- ✅ Shows loading indicator
- ✅ Displays success/error feedback

**Refinement 2 (Task Hierarchy):**
- ✅ Parent-child relationships visible
- ✅ Subtasks clearly indicated
- ✅ Dependencies shown
- ✅ Navigable and intuitive

**Refinement 3 (Blocking Indicator):**
- ✅ Red icon on blocker tasks
- ✅ Shows count of blocked tasks
- ✅ Tooltip with details
- ✅ Distinct from "blocked" status

**Refinement 4 (Task Ordering):**
- ✅ Position numbers displayed
- ✅ Sort controls functional
- ✅ Current order clear to user

**Refinement 5 (Enhancements):**
- ✅ Top 3 suggestions prototyped
- ✅ Implementation proposals documented
- ✅ User feedback gathered

---

## Git Workflow

### Subagent Commit Pattern

```bash
# Each subagent commits their work independently

# Example: Refresh Button Subagent
git add task-viewer/static/index.html
git commit -m "feat(refresh): add manual refresh button with loading state

- Add refresh button to header (top-right)
- Implement refreshAllData() function
- Show spinner during data fetch
- Display toast notification on completion
- Error handling with user feedback

Implements refinement request #1"

# Example: Blocking Indicator Subagent
git add task-viewer/main.py task-viewer/static/index.html
git commit -m "feat(blocker): add visual indicator for blocking tasks

Backend:
- Add blocker detection logic in /api/tasks endpoint
- Return is_blocker and blocks_tasks fields

Frontend:
- Add red shield icon to blocker task cards
- Show count badge 'Blocks X tasks'
- Tooltip with list of blocked tasks

Implements refinement request #3"
```

### Integration Workflow

```bash
# After all subagents complete
git status  # Check all commits are made
git log --oneline -10  # Verify all feature commits

# Push to refinements branch
git push -u origin feat/task-viewer-refinements

# Create PR when all refinements complete
gh pr create --title "Task Viewer Refinements - 5 UX Improvements" \
             --body "..." \
             --base main \
             --head feat/task-viewer-refinements
```

---

## Next Session Start Commands

```bash
# 1. Navigate to project
cd /Users/cliffclarke/Claude_Code/task-mcp

# 2. Ensure on refinements branch
git branch --show-current  # Should show: feat/task-viewer-refinements

# 3. Check server is running
curl -s http://localhost:8001/health | python3 -m json.tool

# 4. If server not running:
cd task-viewer
source ../.venv/bin/activate  # or appropriate venv
python -m uvicorn main:app --reload --port 8001

# 5. Open browser for testing
# http://localhost:8001

# 6. Launch parallel subagents for Phase 1
# (Use Task tool with multiple agents in single message)
```

---

## Questions to Clarify

Before starting refinement #4 (Task Ordering):

1. **Display only or control?**
   - Option A: Just show current order (position numbers)
   - Option B: Allow reordering (drag-and-drop)

2. **Persistence needed?**
   - Should custom order be saved to database?
   - Or just visual within session?

3. **Ordering criteria priority:**
   - Priority → Status → Date?
   - User-configurable?
   - Per-project or global?

---

## Resources

**Documentation:**
- Alpine.js: https://alpinejs.dev/
- Tailwind CSS: https://tailwindcss.com/
- FastAPI: https://fastapi.tiangolo.com/

**Existing Reports:**
- Error Analysis: `docs/subagent-reports/playwright-specialist/task-viewer-debugging/2025-11-02-error-analysis.md`
- E2E Test Results: `docs/subagent-reports/playwright-specialist/task-viewer-debugging/2025-11-02-e2e-test-results.md`
- Architecture Docs: `docs/task-viewer/`

---

## Final Notes

**Current branch:** `feat/task-viewer-refinements`
**Base:** `main` (all previous work merged)
**Status:** Ready for parallel development

**Estimated Total Time:** 15-25 hours for all 5 refinements

**Recommended First Step:**
1. Clarify refinement #4 (ordering) requirements
2. Launch Phase 1 subagents in parallel (4 subagents)
3. Monitor progress and handle conflicts
4. Phase 2 sequential work
5. Integration and testing

---

**End of Handoff**

Ready to begin refinements with parallel subagent workflow! 🚀
