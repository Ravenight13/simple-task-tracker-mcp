 ---
  Workspace Isolation Test Prompt

  Test workspace isolation for this project after terminal reload.

  **Test Objectives:**
  1. Verify workspace filtering is working correctly
  2. Check which tasks are visible in this workspace
  3. Identify any remaining cross-contamination
  4. Validate project picker shows friendly names

  **Run these tests:**

  1. List all projects and show their friendly names:
     - Use: mcp__task-mcp__list_projects
     - Expected: Should see 3 projects with friendly names, not raw paths

  2. List all tasks visible in the current workspace:
     - Use: mcp__task-mcp__list_tasks
     - Show: Total count, task IDs, and task titles
     - Identify: Which tasks belong here vs cross-contaminated tasks

  3. Get project info for current workspace:
     - Use: mcp__task-mcp__get_project_info with current workspace path
     - Show: Task counts by status and priority

  4. Search for specific cross-contamination indicators:
     - Search for "task-viewer" or "refinement" in task titles
     - Search for "enhancement backlog" tasks
     - Check if any tasks #48-67 are visible (these belong to task-mcp only)

  **Expected Results by Project:**

  **For commission-processing-vendor-extractors:**
  - Should see ONLY 15 legitimate tasks:
    - Task #1: Framework Modernization v2.0 (done)
    - Tasks #2-11: Framework Modernization subtasks (all done)
    - Task #13: JSON manifest for vendor golden master (done)
    - Task #14: EPSON single-phase architecture (done)
    - Task #15: LEGRAND single-phase architecture (done)
  - Should NOT see: Tasks #16, #26-31, #42, #47-67 (task-mcp tasks)

  **For bmcis-knowledge-mcp:**
  - Should see only bmcis-knowledge specific tasks
  - Should NOT see any task-viewer or commission-processing tasks

  **Report Format:**
  Please provide:
  1. Current workspace path (use pwd)
  2. Total task count visible
  3. List of all task IDs and titles
  4. Cross-contamination status (CLEAN or CONTAMINATED with details)
  5. Any tasks that don't belong in this workspace
  6. Recommendation for cleanup if contamination detected

  ---