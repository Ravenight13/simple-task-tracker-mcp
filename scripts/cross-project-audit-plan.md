# Cross-Project Audit Plan

**Purpose:** Safely identify cross-contamination across all three projects before any cleanup

**Critical Insight:** We have 3 projects sharing task-mcp. We need to audit ALL projects before deleting anything to understand what's truly cross-contaminated vs. what might be legitimate workspace filtering issues.

---

## Phase 1: Audit All Projects

### ✅ Project 1: Commission-Processing (COMPLETED)

**Location:** `/Users/cliffclarke/Claude_Code/commission-processing-vendor-extractors`

**Results:**
- Total tasks visible: 47 tasks
- Legitimate tasks: 27 tasks (#1-16, #26-31, #42, #47, #68)
- Potentially contaminated: 21 tasks (#48-67, #69)
- Tags: All contaminated tasks tagged "task-viewer"
- Report: `task-mcp-audit-commission.md`

---

### ⏳ Project 2: Task-MCP (PENDING)

**Location:** `/Users/cliffclarke/Claude_Code/task-mcp`

**Audit Prompt:**
```
Run workspace isolation audit for task-mcp project.

**Current Workspace:** /Users/cliffclarke/Claude_Code/task-mcp

**Tests to Run:**

1. List all projects:
   - Use: mcp__task-mcp__list_projects
   - Expected: 3 projects with friendly names

2. Get project info:
   - Use: mcp__task-mcp__get_project_info
   - Report: Total tasks, status breakdown, priority breakdown

3. List all tasks:
   - Use: mcp__task-mcp__list_tasks
   - Report: Total count, all task IDs and titles
   - Expected: ~24 tasks (task-mcp specific)

4. Search for potential contamination:
   - Search: "Framework Modernization" (commission-processing indicator)
   - Search: "vendor" (commission-processing indicator)
   - Search: "EPSON" or "LEGRAND" (commission-processing vendors)
   - Search: "bmcis" or "knowledge" (bmcis-knowledge indicator)

5. Analyze task tags:
   - Group tasks by tags
   - Identify which tags indicate which project
   - Report: Tag distribution

6. Check task creation context:
   - Sample 5-10 tasks
   - Check created_by conversation IDs
   - Check file_references fields
   - Identify workspace context

**Expected Results:**
- Should see task-viewer refinement tasks (#32-42)
- Should see enhancement backlog tasks (#48-69)
- Should see task-mcp infrastructure tasks
- Should NOT see commission-processing vendor tasks
- Should NOT see bmcis-knowledge tasks

**Report Format:**
- Total tasks visible
- Tasks by category (infrastructure, task-viewer, enhancements)
- Any cross-contamination detected (tasks from other projects)
- File references analysis
- Tag analysis
- Recommendation: KEEP, REVIEW, or DELETE for each category

**Save report to:** task-mcp-audit-taskmcp.md
```

---

### ⏳ Project 3: BMCIS-Knowledge-MCP (PENDING)

**Location:** `/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp`

**Audit Prompt:**
```
Run workspace isolation audit for bmcis-knowledge-mcp project.

**Current Workspace:** /Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp

**Tests to Run:**

1. List all projects:
   - Use: mcp__task-mcp__list_projects
   - Expected: 3 projects with friendly names

2. Get project info:
   - Use: mcp__task-mcp__get_project_info
   - Report: Total tasks, status breakdown, priority breakdown

3. List all tasks:
   - Use: mcp__task-mcp__list_tasks
   - Report: Total count, all task IDs and titles
   - Expected: Only bmcis-knowledge specific tasks

4. Search for potential contamination:
   - Search: "task-viewer" (task-mcp indicator)
   - Search: "enhancement" (task-mcp indicator)
   - Search: "Framework Modernization" (commission-processing indicator)
   - Search: "vendor" or "commission" (commission-processing indicator)

5. Analyze task tags:
   - Group tasks by tags
   - Identify which tags indicate which project
   - Report: Tag distribution

6. Check task creation context:
   - Sample 5-10 tasks
   - Check created_by conversation IDs
   - Check file_references fields
   - Identify workspace context

**Expected Results:**
- Should see bmcis-knowledge specific tasks only
- Should NOT see task-viewer tasks
- Should NOT see commission-processing tasks
- Should NOT see enhancement backlog tasks

**Report Format:**
- Total tasks visible
- Tasks by category (if applicable)
- Any cross-contamination detected (tasks from other projects)
- File references analysis
- Tag analysis
- Recommendation: KEEP, REVIEW, or DELETE for each category

**Save report to:** task-mcp-audit-bmcis.md
```

---

## Phase 2: Cross-Project Analysis

After all three audits complete, create a comprehensive comparison matrix.

### Analysis Framework

**Create file:** `scripts/cross-project-analysis.md`

**Contents:**

1. **Task Ownership Matrix**
   - List ALL unique task IDs across all projects
   - For each task ID, show which projects can "see" it
   - Identify tasks visible in multiple projects (true contamination)
   - Identify tasks visible in only one project (correct isolation)

2. **Tag-Based Project Attribution**
   - `task-viewer` tag → task-mcp project
   - `vendor`, `commission`, `framework-modernization` → commission-processing
   - `bmcis`, `knowledge` → bmcis-knowledge-mcp
   - Identify tasks with mismatched tags vs visibility

3. **File Reference Analysis**
   - Tasks with `task-viewer/` references → should only be in task-mcp
   - Tasks with `commission-processing/` references → should only be in commission-processing
   - Tasks with `bmcis-knowledge/` references → should only be in bmcis-knowledge-mcp
   - Flag tasks with file references not matching their visible workspace

4. **Conversation ID Tracking**
   - Group tasks by created_by conversation ID
   - Identify which conversations created tasks in which projects
   - Spot patterns: did one conversation create tasks across multiple projects?

5. **Decision Matrix**
   - For each task ID: KEEP in Project X, DELETE from Project Y
   - Rationale for each decision
   - Risk assessment (low/medium/high)

---

## Phase 3: Tagging (Not Deletion)

Instead of deleting, we'll tag tasks for review.

### Tagging Strategy

**Add custom tags to mark tasks:**
- `needs-review` - Task needs manual review
- `wrong-workspace-suspected` - Task likely in wrong workspace
- `cross-project-duplicate` - Task exists in multiple projects
- `origin-unknown` - Can't determine which project task belongs to

**Tagging commands:**
```bash
# Example: Tag task #48 for review in commission-processing
mcp__task-mcp__update_task(
  task_id=48,
  tags="feature-enhancement task-viewer needs-review wrong-workspace-suspected"
)
```

### Benefits of Tagging First
1. **Reversible** - Can remove tags if we're wrong
2. **Visible** - Tagged tasks stand out in queries
3. **Safe** - No data loss
4. **Informative** - Helps with analysis across sessions
5. **Auditable** - Can track which tasks were flagged

---

## Phase 4: Cleanup Decision

**Only after all three audits complete and cross-project analysis is done:**

1. **Identify True Cross-Contamination**
   - Task visible in Project A
   - Task clearly belongs to Project B (based on tags, files, context)
   - Task has no legitimate reason to be in Project A

2. **Create Cleanup Plan**
   - List of tasks to delete from each project
   - Rationale for each deletion
   - Risk assessment
   - Rollback plan

3. **Execute Cleanup (Soft Delete)**
   - Delete from incorrect workspace(s)
   - Verify task still exists in correct workspace
   - Confirm 30-day retention active

4. **Post-Cleanup Validation**
   - Re-run audits on all three projects
   - Verify cross-contamination resolved
   - Check no legitimate tasks lost
   - Confirm workspace isolation working

---

## Safety Principles

**Before any deletion:**
1. ✅ Audit all three projects completely
2. ✅ Create cross-project analysis matrix
3. ✅ Identify true ownership of each task
4. ✅ Tag suspicious tasks first
5. ✅ Review tags with fresh perspective
6. ✅ Get consensus on cleanup plan
7. ✅ Execute soft deletes only
8. ✅ Verify in all projects post-cleanup

**Never delete:**
- Tasks without clear attribution to another project
- Tasks visible in only one project (even if suspicious)
- Tasks without confirmation from cross-project analysis
- Tasks with ambiguous ownership

---

## Audit Timeline

**Phase 1: Audits**
- ✅ Commission-Processing: Complete
- ⏳ Task-MCP: 10-15 minutes
- ⏳ BMCIS-Knowledge-MCP: 10-15 minutes

**Phase 2: Analysis**
- ⏳ Cross-project matrix: 20-30 minutes
- ⏳ Decision matrix: 15-20 minutes

**Phase 3: Tagging**
- ⏳ Tag suspicious tasks: 10-15 minutes
- ⏳ Review tagged tasks: 10 minutes

**Phase 4: Cleanup (if needed)**
- ⏳ Create cleanup plan: 15 minutes
- ⏳ Execute cleanup: 10-15 minutes
- ⏳ Validation: 15 minutes

**Total: ~2 hours (safe, thorough approach)**

---

## Next Immediate Actions

1. **Run task-mcp audit** - Use prompt above in task-mcp workspace
2. **Run bmcis-knowledge audit** - Use prompt above in bmcis-knowledge workspace
3. **Create cross-project analysis** - Wait for all audits
4. **Tag suspicious tasks** - Mark for review, don't delete yet
5. **Review with fresh eyes** - Look at the complete picture
6. **Make cleanup decision** - Based on complete data

---

## Success Criteria

**Good audit when:**
- All three projects audited completely
- Task ownership clearly attributed
- Cross-contamination patterns identified
- Safe cleanup plan created
- No ambiguous cases remain

**Good cleanup when:**
- Only true cross-contamination removed
- All legitimate tasks preserved
- Workspace isolation verified
- 30-day retention confirmed
- No data loss

---

**Status:** Phase 1 - Audit remaining projects (task-mcp, bmcis-knowledge-mcp)

**Next:** Run audit prompts in the other two workspaces
