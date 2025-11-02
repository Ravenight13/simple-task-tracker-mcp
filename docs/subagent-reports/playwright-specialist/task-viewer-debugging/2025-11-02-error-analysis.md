# Task Viewer Frontend Error Analysis
**Date:** 2025-11-02
**Reporter:** Playwright E2E Specialist
**Target:** http://localhost:8001 (task-mcp task viewer)

---

## Executive Summary

**Total Errors Found:** 99
- Console Errors: 2
- Console Warnings: 49
- Page Errors: 47
- Network Errors: 1

**Root Cause:** The `/js/config.js` file returns a 404 error due to incorrect static file serving configuration in FastAPI. This causes Alpine.js to fail initialization because `API_CONFIG` is undefined, resulting in a cascade of 47+ Alpine Expression Errors.

**Impact:** The entire frontend is non-functional. No Alpine.js component data is initialized, no filters work, no tasks can be displayed.

---

## Error Breakdown

### 1. Critical Network Error (Root Cause)

**Error:**
```
GET http://localhost:8001/js/config.js - 404 Not Found
net::ERR_ABORTED
```

**Location:** Line 46 in `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html`

**Problem:**
```html
<!-- Line 46 -->
<script src="js/config.js"></script>
```

The HTML references `js/config.js`, but FastAPI's StaticFiles mount is configured as:
```python
# Line 503 in main.py
app.mount("/static", StaticFiles(directory="static"), name="static")
```

This mounts the `static` directory at `/static`, so files must be accessed via:
- `/static/index.html` ✅
- `/static/js/config.js` ✅
- `/js/config.js` ❌ (current reference)

**Why This Happens:**
When you visit `http://localhost:8001/`, FastAPI serves `static/index.html` from the root (line 507-509 in main.py). However, the HTML file's relative path `js/config.js` resolves to `http://localhost:8001/js/config.js`, NOT `http://localhost:8001/static/js/config.js`.

---

### 2. Alpine.js Initialization Failures (Cascade Effect)

Because `config.js` fails to load, `API_CONFIG` is undefined. This causes the Alpine.js component function `taskViewer()` to throw an error:

**47 Alpine Expression Errors:**
All errors follow the pattern:
```
Alpine Expression Error: [variable] is not defined
Expression: "[some Alpine.js expression]"
```

**Variables Not Defined:**
- `API_CONFIG` (line ~107 in index.html, in taskViewer() function)
- `init` (init() method not available)
- `currentProject`
- `projects`
- `apiKey`
- `statusFilter`
- `statusCounts`
- `searchQuery`
- `priorityFilter`
- `sortBy`
- `filteredTasks`
- `loading`
- `error`
- `showModal`
- `selectedTask`
- `showApiKeyModal`
- `apiKeyInput`

**Alpine Component Data:**
Playwright confirmed that Alpine.js loads successfully, but the component data is empty:
```javascript
Alpine.js loaded: true
Alpine Component Data: {}  // Should contain all state variables
```

This proves that the `x-data="taskViewer()"` expression (around line 113 in index.html) fails to execute because `API_CONFIG` is undefined inside the `taskViewer()` function.

---

### 3. Secondary Issues

**Missing Alpine.js Plugin:**
```
Alpine Warning: You can't use [x-trap] without first installing the "Focus" plugin
```

**Location:** Line ~884 in index.html (modal with `x-trap`)

**Impact:** Minor - modal focus trapping won't work, but doesn't break functionality.

**Fix:** Add Alpine.js Focus plugin:
```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/focus@3.x.x/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

---

## Recommended Fixes

### Option 1: Fix Static File Path in HTML (Simplest)

**File:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html`

**Change Line 46 from:**
```html
<script src="js/config.js"></script>
```

**To:**
```html
<script src="/static/js/config.js"></script>
```

**Pros:**
- Single line change
- No server configuration needed
- Explicit path is clear

**Cons:**
- Requires `/static/` prefix for all static assets

---

### Option 2: Serve Static Files from Root (Better UX)

**File:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/main.py`

**Problem:** The current setup serves `index.html` from root but expects `js/config.js` to be at `/static/js/config.js`.

**Solution:** Mount static files to serve the `js` subdirectory correctly.

**Change Line 503 from:**
```python
app.mount("/static", StaticFiles(directory="static"), name="static")
```

**To:**
```python
# Mount static directory to serve /js, /css, /images from root
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

**WAIT!** This won't work because it conflicts with the API routes at `/api/*`.

**Better Solution - Add separate mount for /js:**
```python
# Line 503 - Keep existing static mount
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add new mount BEFORE the static mount (order matters!)
# This must come AFTER line 502 (after API routes) but BEFORE line 503
from pathlib import Path

# Mount js subdirectory at /js
app.mount("/js", StaticFiles(directory=Path("static/js")), name="js")
```

**Complete Fix (Lines 502-510 in main.py):**
```python
# Mount static files for frontend
# Order matters: Mount subdirectories first, then general static
from pathlib import Path

# Mount js subdirectory at /js (so js/config.js works from root HTML)
app.mount("/js", StaticFiles(directory=Path("static/js")), name="js")

# Mount all static files at /static
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the task viewer frontend HTML."""
    return FileResponse("static/index.html")
```

**Pros:**
- HTML paths work naturally (`js/config.js` instead of `/static/js/config.js`)
- Cleaner frontend code
- Follows common web conventions

**Cons:**
- Adds another mount point (minor complexity)

---

### Option 3: Use Absolute Path with Base Tag (Most Robust)

**File:** `/Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html`

Add after `<head>` tag (around line 3):
```html
<head>
  <base href="/static/">
  <meta charset="UTF-8">
  <!-- ... rest of head ... -->
```

**Then all relative paths will resolve to `/static/`:**
- `js/config.js` → `/static/js/config.js` ✅

**Pros:**
- Single line change in HTML
- All relative paths automatically work
- No server changes needed

**Cons:**
- May affect other relative URLs (links, images) if added later

---

## Line-by-Line Fixes

### Fix 1: Missing config.js (CRITICAL - Choose one option above)

**Option A: Update HTML path**
```diff
File: /Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html
Line: 46

-  <script src="js/config.js"></script>
+  <script src="/static/js/config.js"></script>
```

**Option B: Add /js mount in server**
```diff
File: /Users/cliffclarke/Claude_Code/task-mcp/task-viewer/main.py
Lines: 502-503

+from pathlib import Path
+
+# Mount js subdirectory at /js (so js/config.js works from root HTML)
+app.mount("/js", StaticFiles(directory=Path("static/js")), name="js")
+
 # Mount static files for frontend
 app.mount("/static", StaticFiles(directory="static"), name="static")
```

**Option C: Add base tag**
```diff
File: /Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html
Lines: 2-4

 <html lang="en">
 <head>
+  <base href="/static/">
   <meta charset="UTF-8">
```

---

### Fix 2: Add Alpine.js Focus Plugin (OPTIONAL)

```diff
File: /Users/cliffclarke/Claude_Code/task-mcp/task-viewer/static/index.html
Lines: 42-43

   <!-- Alpine.js -->
+  <script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/focus@3.x.x/dist/cdn.min.js"></script>
   <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

---

## Testing Verification

After applying Fix 1 (any option), verify with:

1. **Browser DevTools Console:**
   ```
   Should see: 0 errors (currently 99 errors)
   ```

2. **Check API_CONFIG:**
   ```javascript
   console.log(API_CONFIG);
   // Should output: { baseUrl: "http://localhost:8001/api", getApiKey: ƒ, ... }
   ```

3. **Check Alpine Component Data:**
   ```javascript
   console.log(Alpine.$data(document.querySelector('[x-data]')));
   // Should output: { currentProject: null, projects: [], tasks: [], ... }
   ```

4. **Functional Tests:**
   - Click "All" filter → Should work
   - Click "To Do" filter → Should work
   - Search box → Should be visible
   - API Key modal → Should open

---

## Playwright Test Results Summary

### What Worked:
- ✅ Page loads successfully (200 OK)
- ✅ Alpine.js library loads from CDN
- ✅ Tailwind CSS loads from CDN

### What Failed:
- ❌ config.js 404 error
- ❌ Alpine component initialization
- ❌ All filter buttons (timeout - no data-testid elements rendered)
- ❌ All task interactions (no tasks rendered due to failed init)

### Screenshots Captured:
1. `01_initial_load.png` - Page with blank state
2. `02_after_alpine_init.png` - Alpine loaded but component data empty
3. `09_final_state.png` - Final state after interaction attempts

All screenshots show empty component state due to initialization failure.

---

## Previous Session Context

**Previous Fix Attempt:**
The previous session added 50+ null checks throughout the HTML to handle undefined variables:
```javascript
// Examples:
currentProject?.friendly_name
(filteredTasks || []).length
statusCounts?.total
```

**Why Null Checks Didn't Work:**
These null checks are defensive programming for **after** initialization succeeds. However, the root problem is that initialization **never runs** because:

1. `API_CONFIG` is undefined (config.js 404)
2. The `taskViewer()` function throws error when it tries to access `API_CONFIG.baseUrl`
3. Alpine.js catches the error and returns empty object `{}`
4. All template expressions try to access undefined variables

**The null checks were treating symptoms, not the disease.**

---

## Root Cause Analysis

### Why This Bug Exists

**FastAPI's StaticFiles behavior:**
```python
app.mount("/static", StaticFiles(directory="static"), name="static")
```

This creates a mount at `/static/*` that serves files from the `static/` directory:
- `/static/index.html` → `static/index.html` ✅
- `/static/js/config.js` → `static/js/config.js` ✅

**But:**
```python
@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")
```

This serves `index.html` from root (`http://localhost:8001/`), so when `index.html` references:
```html
<script src="js/config.js"></script>
```

The browser resolves this relative to the current path:
- Current URL: `http://localhost:8001/`
- Relative path: `js/config.js`
- Resolved to: `http://localhost:8001/js/config.js` ❌
- Should be: `http://localhost:8001/static/js/config.js` ✅

**FastAPI doesn't have a route for `/js/config.js`, only `/static/js/config.js`.**

---

## Recommendations

### Immediate Action (Choose One):

1. **Option B (Add /js mount)** - Recommended for production
   - Most aligned with standard web conventions
   - Clean URLs in frontend code
   - Minimal changes

2. **Option A (Fix HTML path)** - Quickest fix for testing
   - Single line change
   - Immediate testing possible
   - Can refactor later

3. **Option C (Base tag)** - Best for complex sites
   - Future-proof for more static assets
   - Might need adjustments if adding client-side routing

### Long-term Improvements:

1. **Add E2E Tests:**
   ```typescript
   // test/e2e/task-viewer.spec.ts
   import { test, expect } from '@playwright/test'
   import { injectAxe, checkA11y } from '@axe-core/playwright'

   test('task viewer loads without errors', async ({ page }) => {
     const errors: string[] = []
     page.on('pageerror', err => errors.push(err.message))
     page.on('console', msg => {
       if (msg.type() === 'error') errors.push(msg.text())
     })

     await page.goto('http://localhost:8001')
     await page.waitForLoadState('networkidle')

     // Verify no errors
     expect(errors).toHaveLength(0)

     // Verify Alpine initialized
     const hasAlpineData = await page.evaluate(() => {
       const el = document.querySelector('[x-data]')
       return el?._x_dataStack?.[0] && Object.keys(el._x_dataStack[0]).length > 0
     })
     expect(hasAlpineData).toBe(true)

     // Accessibility audit
     await injectAxe(page)
     await checkA11y(page)
   })
   ```

2. **Add Health Check for Static Assets:**
   ```python
   @app.get("/health/frontend")
   async def frontend_health():
       """Verify critical frontend assets are accessible."""
       import os
       config_js_exists = os.path.exists("static/js/config.js")
       index_html_exists = os.path.exists("static/index.html")

       return {
           "status": "healthy" if (config_js_exists and index_html_exists) else "degraded",
           "assets": {
               "config_js": config_js_exists,
               "index_html": index_html_exists
           }
       }
   ```

3. **Build Process for Production:**
   - Bundle JavaScript with Vite/esbuild
   - Minify CSS/JS
   - Add cache busting (hashed filenames)
   - Remove CDN dependencies (bundle Tailwind + Alpine.js)

---

## Appendix: Full Error List

### Console Errors (2):
1. `GET http://localhost:8001/js/config.js - 404 Not Found`
2. `GET http://localhost:8001/favicon.ico - 404 Not Found` (minor, cosmetic)

### Network Errors (1):
1. `GET http://localhost:8001/js/config.js - net::ERR_ABORTED`

### Page Errors (47):
All following the pattern: `[variable] is not defined`
- API_CONFIG
- init
- currentProject (3 instances)
- projects
- apiKey (2 instances)
- statusFilter (10 instances)
- statusCounts (5 instances)
- searchQuery (3 instances)
- priorityFilter (5 instances)
- sortBy (4 instances)
- filteredTasks (3 instances)
- loading (4 instances)
- error (3 instances)
- showModal (2 instances)
- selectedTask (2 instances)
- showApiKeyModal (2 instances)
- apiKeyInput

### Console Warnings (49):
- 1 Tailwind CDN warning (not for production)
- 1 Alpine.js Focus plugin warning
- 47 Alpine Expression Errors (duplicates of page errors)

---

## Conclusion

The task viewer frontend has **99 errors, all caused by a single root issue**: the missing `config.js` file (404 error). This prevents Alpine.js from initializing the component, causing a cascade of 47 "variable not defined" errors.

**Fix:** Apply Option A, B, or C above to correct the static file serving path.

**Expected Outcome After Fix:**
- 0 errors in console
- Alpine.js component initializes with full state
- All filters and interactions work
- Tasks load and display correctly

**Verification:** Re-run Playwright script (`python debug_task_viewer.py`) and confirm 0 errors.

---

**Report Generated:** 2025-11-02
**Generated By:** Playwright E2E Testing Specialist (Automated Debugging)
