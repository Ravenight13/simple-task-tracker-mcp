# MCP Path Diagnosis After Folder Rename

**Date:** 2025-11-01
**Issue:** MCP server not working after renaming project folder
**Status:** RESOLVED

## Problem Summary

The task-mcp server stopped working in Claude Desktop after the project folder was renamed from `simple-task-tracker-mcp` to `task-mcp`. Claude Desktop's MCP configuration file contains a hardcoded absolute path to the old folder location, causing the MCP server to fail to start.

## Root Cause Analysis

### Primary Issue
The Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json`) contains a hardcoded path to the old virtual environment:

```json
"task-mcp": {
  "command": "/Users/cliffclarke/Claude_Code/simple-task-tracker-mcp/.venv/bin/task-mcp"
}
```

This path no longer exists after the folder rename. The old directory `simple-task-tracker-mcp` was renamed to `task-mcp`.

### Why This Happened
MCP server configurations in Claude Desktop use absolute paths to Python virtual environments for reliable server startup across different contexts. When the project folder was renamed:
1. The folder path changed from `.../simple-task-tracker-mcp` to `.../task-mcp`
2. The virtual environment path changed accordingly
3. Claude Desktop configuration still pointed to the old path
4. MCP server failed to start (binary not found)

### Verification
Testing showed:
- Old path: `/Users/cliffclarke/Claude_Code/simple-task-tracker-mcp/.venv/bin/task-mcp` (NOT FOUND)
- New path: `/Users/cliffclarke/Claude_Code/task-mcp/.venv/bin/task-mcp` (EXISTS)
- Manual server start with `uv run task-mcp` works correctly (shows warning about VIRTUAL_ENV mismatch but runs)

## Files/Paths Affected

### Configuration File (MUST UPDATE)
**File:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Line 60:** Current incorrect path
```json
"command": "/Users/cliffclarke/Claude_Code/simple-task-tracker-mcp/.venv/bin/task-mcp"
```

**Should be:** Corrected path
```json
"command": "/Users/cliffclarke/Claude_Code/task-mcp/.venv/bin/task-mcp"
```

### Project Files (NO CHANGES NEEDED)
The following files are correctly configured and do NOT need changes:
- `pyproject.toml`: Uses relative paths and project name (correct)
- `src/task_mcp/`: All Python source files use relative imports (correct)
- `.venv/`: Virtual environment recreated at new path automatically

## Step-by-Step Fix Instructions

### Method 1: Direct Configuration Edit (RECOMMENDED)

1. **Open Claude Desktop configuration file:**
   ```bash
   open -a TextEdit ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Locate the task-mcp entry (around line 59-61):**
   ```json
   "task-mcp": {
     "command": "/Users/cliffclarke/Claude_Code/simple-task-tracker-mcp/.venv/bin/task-mcp"
   }
   ```

3. **Change `simple-task-tracker-mcp` to `task-mcp`:**
   ```json
   "task-mcp": {
     "command": "/Users/cliffclarke/Claude_Code/task-mcp/.venv/bin/task-mcp"
   }
   ```

4. **Save the file and close the editor**

5. **Restart Claude Desktop:**
   - Quit Claude Desktop completely (Cmd+Q)
   - Relaunch Claude Desktop
   - Wait 5-10 seconds for MCP servers to initialize

### Method 2: Using uv (ALTERNATIVE)

If you prefer using `uv` to launch the server (more flexible for development):

1. **Edit the configuration file:**
   ```bash
   open -a TextEdit ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Replace the task-mcp entry with:**
   ```json
   "task-mcp": {
     "command": "uv",
     "args": ["run", "task-mcp"],
     "cwd": "/Users/cliffclarke/Claude_Code/task-mcp"
   }
   ```

3. **Save and restart Claude Desktop**

**Advantages of Method 2:**
- No need to update path if folder renamed again
- Uses `uv run` which auto-manages virtual environments
- More resilient to project structure changes

**Disadvantages:**
- Requires `uv` to be in PATH
- Slightly slower startup (builds package each time)

## Testing Verification Steps

### 1. Verify Configuration Syntax
After editing the JSON file, validate it's still valid JSON:
```bash
python3 -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON - fix syntax errors"
```

### 2. Check Binary Exists
Verify the path in the configuration actually exists:
```bash
ls -l /Users/cliffclarke/Claude_Code/task-mcp/.venv/bin/task-mcp
```
Expected output: Should show file permissions and file size (not "No such file")

### 3. Test Manual Server Start
Test the MCP server starts correctly from command line:
```bash
cd /Users/cliffclarke/Claude_Code/task-mcp
uv run task-mcp
```
Expected output: Should show FastMCP banner with "Server name: Task Tracker"

### 4. Verify in Claude Desktop
After restarting Claude Desktop:

1. **Open Claude Desktop Developer Tools:**
   - macOS: View > Toggle Developer Tools (or Cmd+Option+I)

2. **Check Console for MCP initialization:**
   - Look for "task-mcp" initialization messages
   - Should NOT see "Failed to start MCP server: task-mcp"
   - Should see successful connection messages

3. **Test MCP functionality in conversation:**
   Type in a new conversation:
   ```
   List all task-mcp tools available
   ```
   Expected: Should see list of tools (create_task, list_tasks, etc.)

4. **Test basic operation:**
   ```
   Create a test task with title "MCP Path Fix Verification"
   ```
   Expected: Should successfully create task and return task ID

### 5. Check MCP Server Logs (if issues persist)
If the server still doesn't work, check logs:
```bash
# Claude Desktop logs location (macOS)
tail -f ~/Library/Logs/Claude/mcp*.log
```

## Summary

**Root Cause:** Claude Desktop configuration contains hardcoded path to old folder name

**Fix Required:** Update single line in `claude_desktop_config.json` changing `simple-task-tracker-mcp` to `task-mcp`

**Restart Required:** Yes, must quit and relaunch Claude Desktop after configuration change

**Risk Level:** LOW (simple path update, easily reversible)

**Time to Fix:** < 2 minutes

## Prevention for Future Renames

If renaming project folders frequently, consider:

1. **Use uv-based configuration** (Method 2 above) instead of direct binary paths
2. **Create symbolic link** from old name to new name (temporary during transition)
3. **Document MCP configuration location** in project README for quick updates
4. **Use environment variables** in configuration (if Claude Desktop supports them)

## Related Files

- Configuration: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Binary location: `/Users/cliffclarke/Claude_Code/task-mcp/.venv/bin/task-mcp`
- Project root: `/Users/cliffclarke/Claude_Code/task-mcp`
- Entry point: `pyproject.toml` line 38 (`task-mcp = "task_mcp.server:main"`)
