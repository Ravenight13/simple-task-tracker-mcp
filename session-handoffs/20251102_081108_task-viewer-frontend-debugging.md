# Session Handoff: Task Viewer Frontend - Alpine.js Error Debugging

**Date:** November 2, 2025 8:10 AM
**Project:** task-mcp
**Branch:** feat/task-viewer-frontend
**Status:** DEBUGGING - Alpine.js errors still present despite fixes

---

## Current Situation

### What We Built
Complete task viewer web frontend for task-mcp:
- ✅ FastAPI backend (8 GET endpoints) 
- ✅ HTML/Tailwind/Alpine.js frontend
- ✅ API key authentication
- ✅ Static file serving enabled
- ⚠️ Alpine.js errors still occurring (user reports "TONS of uncaught errors")

### Repository Location
**CORRECT PATH:** `/Users/cliffclarke/Claude_Code/task-mcp`
**Branch:** `feat/task-viewer-frontend`

⚠️ **WARNING:** Previous session kept getting reset to wrong path:
- ❌ `/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp` (WRONG)
- ✅ `/Users/cliffclarke/Claude_Code/task-mcp` (CORRECT)

---

## Server Status

**Backend Running:** Port 8001
```bash
cd /Users/cliffclarke/Claude_Code/task-mcp/task-viewer
source ../.venv/bin/activate
python -m uvicorn main:app --reload --port 8001
```

**Health Check:**
```bash
curl http://localhost:8001/health
# Should return: {"status":"healthy","mcp_connected":true,"projects_loaded":4}
```

**API Key:**
```
quJ5dpjJHfhuskKj3CGcTxn5Af6HZ-O9mPkaepvH7fo
```

---

## Known Issue: Alpine.js Errors

### User Report
"there are TONS of uncaught errors and Alpine Expression Errors now"

### What Was Attempted
1. ✅ Debugger subagent added 50+ null checks
2. ✅ Committed fixes (commit c819558 and 38fab7b)
3. ⚠️ User still reports errors after server restart

### Likely Causes
1. **Fixes not fully effective** - May have missed some error sources
2. **Browser cache** - Old version cached in browser
3. **Missing Alpine.js initialization** - Data not fully initialized before render
4. **Async timing issues** - Race conditions with API calls

---

## Next Steps for New Session

### 1. Verify Current Code State
```bash
cd /Users/cliffclarke/Claude_Code/task-mcp
git status
git log --oneline -5
```

### 2. Check What User Sees
Ask user to:
- Open browser DevTools (F12)
- Navigate to http://localhost:8001
- Copy/paste ALL console errors
- Screenshot if helpful

### 3. Common Alpine.js Error Patterns to Check

**Pattern 1: Data accessed before initialization**
```javascript
// BAD
x-text="tasks.length"  // tasks might be undefined

// GOOD  
x-text="tasks?.length || 0"
```

**Pattern 2: Async data race**
```javascript
// BAD
Alpine.data('app', () => ({
  tasks: [],
  async init() {
    this.tasks = await fetchTasks(); // Template renders before this completes
  }
}))

// GOOD
Alpine.data('app', () => ({
  tasks: [],
  loading: true,
  async init() {
    this.loading = true;
    this.tasks = await fetchTasks();
    this.loading = false;
  }
}))
```

**Pattern 3: x-cloak not working**
```html
<!-- Ensure Alpine loads and x-cloak is defined -->
<div x-cloak x-show="loaded">...</div>
```

### 4. Debug Workflow

**Step A: Read actual console errors**
```javascript
// User should provide exact error messages like:
// "Alpine Expression Error: Cannot read property 'length' of undefined"
// "TypeError: Cannot read properties of undefined (reading 'status')"
```

**Step B: Find error location in code**
```bash
cd /Users/cliffclarke/Claude_Code/task-mcp/task-viewer
grep -n "x-text.*tasks.length" static/index.html
grep -n "x-show.*currentProject\." static/index.html
```

**Step C: Add defensive checks**
```html
<!-- Example fix -->
<div x-show="currentProject && currentProject.friendly_name">
  <span x-text="currentProject?.friendly_name || 'Unnamed Project'"></span>
</div>
```

**Step D: Test immediately**
```bash
# Browser should auto-reload (uvicorn --reload)
# Check console - error gone?
```

---

## File Locations

### Main Files
```
/Users/cliffclarke/Claude_Code/task-mcp/
├── task-viewer/
│   ├── main.py                    # FastAPI backend
│   ├── static/index.html          # Frontend (Alpine.js errors HERE)
│   ├── static/js/config.js        # API config
│   ├── .env                       # API key
│   └── server.log                 # Server logs
├── docs/
│   ├── task-viewer/               # Planning docs
│   └── subagent-reports/          # Implementation reports
└── session-handoffs/              # This file
```

### Key Code Section (index.html)
- **Lines 100-300:** Alpine.js x-data initialization
- **Lines 300-600:** Task card templates (likely error source)
- **Lines 600-800:** Modal and filters

---

## Testing Checklist

Once errors fixed, verify:
- [ ] Page loads without console errors
- [ ] Project selector shows 4 projects
- [ ] Tasks load and display
- [ ] Filters work (status/priority)
- [ ] Search works
- [ ] Modal opens on task click
- [ ] API key modal works
- [ ] No Alpine Expression Errors in console

---

## Git Commands Reference

```bash
# Ensure correct directory
cd /Users/cliffclarke/Claude_Code/task-mcp

# Check current branch
git branch --show-current  # Should show: feat/task-viewer-frontend

# Recent commits
git log --oneline -10

# See what changed
git diff HEAD~5..HEAD static/index.html

# Commit a fix
git add static/index.html
git commit -m "fix: resolve Alpine.js expression error in task cards"

# When all working, merge to main
git checkout main
git merge feat/task-viewer-frontend
```

---

## Environment Setup

```bash
# Virtual environment (use bmcis-knowledge-mcp's venv)
source /Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp/.venv/bin/activate

# Or create new one
cd /Users/cliffclarke/Claude_Code/task-mcp/task-viewer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Critical Reminders

1. **ALWAYS cd to /Users/cliffclarke/Claude_Code/task-mcp first**
2. **Get actual console errors from user** - don't guess
3. **Test in browser after each fix** - verify error gone
4. **Server auto-reloads** - just refresh browser
5. **Check browser cache** - hard refresh (Cmd+Shift+R)

---

## Success Criteria

Session complete when:
✅ Zero console errors in browser
✅ All features work smoothly
✅ User confirms no more Alpine errors
✅ Ready to merge to main

---

## Quick Start for New Session

```bash
# 1. Navigate to correct project
cd /Users/cliffclarke/Claude_Code/task-mcp

# 2. Verify server running
curl -s http://localhost:8001/health | python3 -m json.tool

# 3. If not running, start it
cd task-viewer
source ../.venv/bin/activate
python -m uvicorn main:app --reload --port 8001 &

# 4. Ask user for console errors
# "Please open http://localhost:8001, open DevTools (F12), 
#  and paste all console errors here"

# 5. Fix errors in static/index.html

# 6. Test - browser auto-refreshes

# 7. Repeat until zero errors
```

---

**End of Handoff**

Good luck! The frontend is 95% done, just needs the Alpine.js errors debugged by looking at actual console output.
