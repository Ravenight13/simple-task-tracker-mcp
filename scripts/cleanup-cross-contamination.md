# Cross-Contamination Cleanup Guide

**Purpose:** Remove cross-contaminated tasks from commission-processing workspace

**Background:** Before workspace filtering fix (commit 20332c0), task-mcp tasks were incorrectly created in commission-processing database. These need soft-deletion for clean workspace isolation.

---

## Phase 1: Verification

Run this in the commission-processing workspace to verify cross-contamination:

```bash
cd /Users/cliffclarke/Claude_Code/commission-processing-vendor-extractors
```

### Verification Prompt

```
Verify cross-contamination in commission-processing workspace.

Run these commands:
1. mcp__task-mcp__list_tasks - Get all visible tasks
2. For each task, check if title contains indicators:
   - "task-mcp", "task-viewer", "refinement", "enhancement", "entity viewer"
   - "Remove workflow-mcp"
   - "Fix subtasks"
   - "Validate semantic"

Expected cross-contaminated task IDs: 16, 26-31, 42, 47-67 (32 tasks total)

Expected legitimate task IDs: 1-11, 13-15 (15 tasks total)

Please report:
- Total tasks visible: [COUNT]
- Legitimate tasks (Framework Modernization, vendor tasks): [LIST IDs]
- Cross-contaminated tasks (task-mcp/viewer related): [LIST IDs]
- Confirmation that tasks match expected contamination pattern: YES/NO
```

---

## Phase 2: Cleanup Execution

### Option A: Automated Batch Cleanup (Recommended)

Use this prompt to delete all cross-contaminated tasks in one operation:

```
Execute cross-contamination cleanup for commission-processing workspace.

**Target Tasks to Delete (32 tasks):**
- Task #16
- Tasks #26, #27, #28, #29, #30, #31
- Task #42
- Task #47
- Tasks #48 through #67 (20 tasks)

**Cleanup Steps:**

1. Verify current workspace:
   - Run: pwd
   - Expected: /Users/cliffclarke/Claude_Code/commission-processing-vendor-extractors

2. Create task deletion list:
   - Single tasks: [16, 42, 47]
   - Range 1: [26, 27, 28, 29, 30, 31]
   - Range 2: [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67]

3. Execute soft deletion for each task:
   - Use: mcp__task-mcp__delete_task
   - Parameters: task_id=[ID], cascade=false
   - Workspace auto-detected from cwd

4. For each deletion, report:
   - Task ID
   - Success/failure status
   - Any errors encountered

5. After all deletions complete:
   - Run: mcp__task-mcp__list_tasks
   - Verify: Should see only 15 legitimate tasks (IDs: 1-11, 13-15)
   - Confirm: No task-viewer or enhancement backlog tasks remain

**Success Criteria:**
- 32 tasks soft-deleted successfully
- Only 15 legitimate tasks remain visible
- No errors during deletion
- Workspace isolation confirmed

Please execute this cleanup and report results.
```

### Option B: Manual Step-by-Step Cleanup

If you prefer to delete tasks manually with confirmation at each step:

```
Manual cross-contamination cleanup (step-by-step with confirmation).

**Before Starting:**
- Current workspace: /Users/cliffclarke/Claude_Code/commission-processing-vendor-extractors
- Verify workspace: pwd

**Delete Single Tasks (3 tasks):**

1. Delete Task #16 (Remove workflow-mcp references):
   - Use: mcp__task-mcp__delete_task(task_id=16, cascade=false)
   - Confirm deletion successful

2. Delete Task #42 (Fix subtasks expansion):
   - Use: mcp__task-mcp__delete_task(task_id=42, cascade=false)
   - Confirm deletion successful

3. Delete Task #47 (Validate semantic architecture):
   - Use: mcp__task-mcp__delete_task(task_id=47, cascade=false)
   - Confirm deletion successful

**Delete Task-MCP Integration Tasks (6 tasks: 26-31):**

4. Delete Task #26:
   - Use: mcp__task-mcp__delete_task(task_id=26, cascade=false)

5. Delete Task #27:
   - Use: mcp__task-mcp__delete_task(task_id=27, cascade=false)

6. Delete Task #28:
   - Use: mcp__task-mcp__delete_task(task_id=28, cascade=false)

7. Delete Task #29:
   - Use: mcp__task-mcp__delete_task(task_id=29, cascade=false)

8. Delete Task #30:
   - Use: mcp__task-mcp__delete_task(task_id=30, cascade=false)

9. Delete Task #31:
   - Use: mcp__task-mcp__delete_task(task_id=31, cascade=false)

**Delete Enhancement Backlog Tasks (20 tasks: 48-67):**

10-29. Delete Tasks #48 through #67 (one by one):
   - For each task ID from 48 to 67:
   - Use: mcp__task-mcp__delete_task(task_id=[ID], cascade=false)

**Verification:**
- Run: mcp__task-mcp__list_tasks
- Expected: Only 15 tasks visible (IDs: 1-11, 13-15)
- Confirm: No cross-contaminated tasks remain

After each step, wait for confirmation before proceeding to next deletion.
```

---

## Phase 3: Validation

After cleanup completion, run this validation:

```
Validate cleanup success across all workspaces.

**Test 1: Commission-Processing Workspace**
cd /Users/cliffclarke/Claude_Code/commission-processing-vendor-extractors

1. List all tasks: mcp__task-mcp__list_tasks
   - Expected count: 15 tasks
   - Expected IDs: 1-11, 13-15
   - Should NOT see: 16, 26-31, 42, 47-67

2. Search for contamination indicators:
   - Search: "task-viewer"
   - Search: "enhancement"
   - Search: "refinement"
   - Expected: No results for any search

**Test 2: Task-MCP Workspace (Verify No Impact)**
cd /Users/cliffclarke/Claude_Code/task-mcp

1. List all tasks: mcp__task-mcp__list_tasks
   - Expected: ~24 tasks still visible
   - Should STILL see: 16, 42, 47-67 (unchanged)
   - Verify: Tasks exist in correct workspace

**Test 3: Cross-Workspace Verification**
1. From task-mcp workspace, verify tasks 16, 42, 47-67 still exist:
   - Use: mcp__task-mcp__get_task(task_id=16)
   - Use: mcp__task-mcp__get_task(task_id=48)
   - Expected: Tasks found successfully

2. From commission-processing workspace, verify same tasks are NOT visible:
   - Use: mcp__task-mcp__get_task(task_id=16)
   - Expected: Error (task not found or deleted)

**Success Criteria:**
✅ Commission-processing shows only 15 legitimate tasks
✅ Task-mcp still shows all 24 tasks (no data loss)
✅ No search hits for contamination indicators in commission-processing
✅ Workspace isolation confirmed bidirectionally

Report validation results for all three tests.
```

---

## Safety Notes

**Soft Delete (30-Day Retention):**
- Tasks are soft-deleted (deleted_at timestamp set)
- Tasks retained for 30 days before permanent purge
- Can be recovered if needed within retention period
- Zero risk to task-mcp workspace (tasks remain there)

**No Cascade:**
- Using cascade=false for all deletions
- No subtasks affected (these tasks have none)
- Only marks the specified task as deleted

**Workspace Isolation:**
- Deletions only affect commission-processing database
- Task-mcp database unchanged (tasks still exist there)
- No cross-workspace data loss

**Rollback (If Needed):**
If you need to undo cleanup within 30 days:
- Tasks are still in database with deleted_at timestamp
- Can manually update deleted_at to NULL to restore
- Or wait for 30-day purge to complete

---

## Troubleshooting

**If task not found:**
- Task may already be soft-deleted
- Or task ID doesn't exist in this workspace (good!)
- Continue with next task

**If deletion fails:**
- Check workspace path is correct (pwd)
- Verify MCP server is running
- Check task exists: mcp__task-mcp__get_task(task_id=[ID])
- Report error for investigation

**If wrong task count after cleanup:**
- Verify workspace: pwd
- Re-run list_tasks to get accurate count
- Check if some tasks were already deleted
- Compare against expected 15 legitimate tasks

---

## Expected Timeline

**Verification:** 2-3 minutes
**Automated Cleanup:** 5-10 minutes (32 deletions)
**Manual Cleanup:** 15-20 minutes (with confirmations)
**Validation:** 3-5 minutes

**Total:** 10-30 minutes depending on method chosen

---

## Completion Checklist

After cleanup complete:
- [ ] 32 tasks soft-deleted from commission-processing
- [ ] Only 15 legitimate tasks remain in commission-processing
- [ ] 24 tasks still visible in task-mcp (no data loss)
- [ ] Workspace isolation validated bidirectionally
- [ ] No search hits for contamination indicators
- [ ] Session handoff updated with cleanup results
- [ ] Cleanup documentation committed to repo

---

**Ready to Execute?**

Choose your cleanup method:
- **Option A:** Automated batch cleanup (faster, recommended)
- **Option B:** Manual step-by-step (more control, slower)

Then proceed with Phase 1 verification first to confirm contamination pattern.
