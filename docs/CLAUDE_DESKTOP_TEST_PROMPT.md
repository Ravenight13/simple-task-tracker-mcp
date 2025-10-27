# Claude Desktop Test Prompt

**Purpose:** Verify Task MCP Server integration and cross-client access with Claude Code

**Pre-requisites:**
- ✅ Claude Desktop config updated with task-mcp server
- ✅ Claude Desktop restarted
- ✅ 9 test tasks exist from Claude Code session

---

## Copy & Paste This Prompt into Claude Desktop:

```
I need to test the Task MCP Server integration. Please help me verify:

1. List all available MCP tools - confirm you can see task-mcp tools
2. List all projects using list_projects
3. Get project info for workspace "/Users/cliffclarke/Claude_Code/simple-task-tracker-mcp"
4. List all tasks in this project
5. Show me the task tree for the parent task (should have 3 subtasks)
6. Create a new task titled "Test from Claude Desktop" with description "Testing cross-client access from Desktop" and priority "high"
7. List tasks again to confirm the new task appears
8. Search for tasks containing "Desktop"

After completing these tests, please report:
- How many tasks total you found
- Whether you can see tasks created from Claude Code
- Whether the new task you created has an ID that continues from the existing tasks
- Any errors or issues encountered
```

---

## Expected Results

### 1. MCP Tools
Should see 13 task-mcp tools:
- create_task
- get_task
- update_task
- list_tasks
- search_tasks
- delete_task
- get_task_tree
- get_blocked_tasks
- get_next_tasks
- cleanup_deleted_tasks
- list_projects
- get_project_info
- set_project_name

### 2. List Projects
Should return 3 projects, including:
- Project ID: `9d3c5ef9`
- Friendly name: "Task MCP Production Testing"
- Workspace: `/Users/cliffclarke/Claude_Code/simple-task-tracker-mcp`

### 3. Project Info
```json
{
  "id": "9d3c5ef9",
  "friendly_name": "Task MCP Production Testing",
  "total_tasks": 9,
  "by_status": {"blocked": 1, "done": 2, "todo": 4, "in_progress": 0},
  "by_priority": {"high": 4, "medium": 3, "low": 1}
}
```

### 4. List Tasks
Should return 9 active tasks (1 was soft-deleted):
- Task 2: Parent Task - Feature Implementation
- Task 3: Subtask 1 - Design Phase
- Task 4: Subtask 2 - Implementation Phase
- Task 5: Subtask 3 - Testing Phase
- Task 6: Dependency Test - Foundation Task (done)
- Task 7: Dependency Test - Dependent Task (done)
- Task 8: Blocked Task Test - Waiting for Approval (blocked)
- Task 9: Validation Test - Oversized Description
- Task 10: Test Task for Blocking Without Reason

### 5. Task Tree
For task ID 2, should show:
```
Parent Task - Feature Implementation
├── Subtask 1 - Design Phase (ID: 3)
├── Subtask 2 - Implementation Phase (ID: 4)
└── Subtask 3 - Testing Phase (ID: 5)
```

### 6. Create New Task
Should create task with ID 11 (next sequential ID)

### 7. List Tasks Again
Should now show 10 tasks (9 previous + 1 new)

### 8. Search
Should find task ID 11 containing "Desktop"

---

## Success Criteria

✅ **Cross-Client Access Working** if:
- Claude Desktop can read all 9 tasks created in Claude Code
- New task created in Desktop gets ID 11 (continues sequence)
- Both clients see the same data (same database)
- No errors about locked database or permission issues
- WAL mode allows concurrent access

❌ **Issues to Watch For:**
- "Database is locked" errors → WAL mode not working
- Can't see tasks from Claude Code → Wrong workspace path
- New task gets ID 1 → Using different database
- Permission denied → File permissions issue

---

## Concurrent Access Test (Optional)

After basic tests pass, with both Claude Code and Claude Desktop open:

**In Claude Desktop:**
1. Create task: "Concurrent Test from Desktop"

**In Claude Code:**
2. List tasks - should see the Desktop task

**In Claude Desktop:**
3. List tasks - should see all tasks

This proves WAL mode enables true concurrent access!

---

## Database File Reference

Both clients should use:
- **Database:** `~/.task-mcp/databases/project_9d3c5ef9.db`
- **Master Registry:** `~/.task-mcp/master.db`
- **Workspace Hash:** `9d3c5ef9` (SHA256 of workspace path)

You can verify with:
```bash
ls -la ~/.task-mcp/databases/project_9d3c5ef9.db
sqlite3 ~/.task-mcp/databases/project_9d3c5ef9.db "SELECT COUNT(*) FROM tasks WHERE deleted_at IS NULL;"
```

---

## Troubleshooting

### If tools don't appear:
1. Restart Claude Desktop completely
2. Check config file syntax: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python3 -m json.tool`
3. Check logs in Claude Desktop settings

### If can't see tasks:
1. Verify workspace path in config matches exactly
2. Check database exists: `ls ~/.task-mcp/databases/project_9d3c5ef9.db`
3. Verify environment variable: Check Desktop MCP server status

### If database locked:
1. Check WAL mode: `sqlite3 ~/.task-mcp/databases/project_9d3c5ef9.db "PRAGMA journal_mode;"`
2. Should return `wal` not `delete`

---

**After testing in Claude Desktop, report back with the results!**
