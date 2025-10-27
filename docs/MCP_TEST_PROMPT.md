 Test task-mcp workspace isolation and v0.2.0 features:

  1. Create test task with full features:
  mcp__task-mcp__create_task(
      title="[TEST] Workspace isolation verification",
      description="Testing v0.2.0 auto-capture and workspace detection",
      priority="high",
      tags="test isolation"
  )

  2. Create child task (use ID from step 1):
  mcp__task-mcp__create_task(
      title="[TEST] Subtask verification",
      parent_task_id=<ID_FROM_STEP_1>,
      tags="test"
  )

  3. Verify workspace and features:
  mcp__task-mcp__get_project_info()

  4. Test partial update (v0.2.0):
  mcp__task-mcp__update_task(
      task_id=<ID_FROM_STEP_1>,
      status="done"
  )

  5. Get task tree:
  mcp__task-mcp__get_task_tree(task_id=<ID_FROM_STEP_1>)

  6. List all tasks to verify isolation:
  mcp__task-mcp__list_tasks()

  Expected results:
  ✅ workspace_path matches current project directory
  ✅ created_by field populated with session ID
  ✅ created_at/updated_at use ISO 8601 format (YYYY-MM-DDTHH:MM:SS.microseconds)
  ✅ Partial update worked (only status changed)
  ✅ Parent-child relationship preserved
  ✅ Task count isolated to this project only

  Report:
  - Workspace path: <actual path>
  - Test task IDs created: <list IDs>
  - All checks passed: YES/NO

  ---
  After all projects pass, use this cleanup prompt:

  Clean up all test tasks created during isolation testing:

  1. List all tasks with "[TEST]" tag:
  mcp__task-mcp__search_tasks(search_term="[TEST]")

  2. Delete each test task (use IDs from step 1):
  mcp__task-mcp__delete_task(task_id=<ID>, cascade=True)

  Repeat for each test task ID found.

  3. Verify cleanup:
  mcp__task-mcp__list_tasks()

  4. Check that test tasks are soft-deleted:
  Run: sqlite3 ~/.task-mcp/databases/project_*.db "SELECT id, title, deleted_at FROM tasks WHERE title LIKE '[TEST]%';"

  Expected: All [TEST] tasks should have deleted_at timestamp set (soft delete).

  ---
  Pro tip: Add the project name to test task titles for easier tracking:

  title="[TEST - commission-processing] Workspace isolation verification"
  title="[TEST - task-mcp] Workspace isolation verification"

  This way you can easily identify which project each test task belongs to when cleaning up.