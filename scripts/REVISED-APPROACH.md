# REVISED APPROACH: Safe Cross-Project Audit

**Date:** 2025-11-02
**Status:** AUDIT FIRST - DO NOT DELETE YET

---

## Critical Realization

We have **3 projects** using task-mcp, not just 2:
1. Commission-Processing (audit complete)
2. Task-MCP (audit pending)
3. BMCIS-Knowledge-MCP (audit pending)

**Before deleting anything, we need to:**
1. Audit all three projects
2. Create cross-project analysis matrix
3. Identify true task ownership
4. Tag suspicious tasks (not delete)
5. Review complete picture
6. Make informed cleanup decision

---

## What Changed

### ❌ Original Approach (ABANDONED)
- Assumed commission-processing audit was sufficient
- Planned immediate deletion of 21-32 tasks
- Risk: Could delete legitimate tasks
- Risk: Could miss patterns visible only in cross-project view

### ✅ Revised Approach (CURRENT)
- Audit all three projects first
- Compare results across projects
- Tag suspicious tasks for review
- Make cleanup decision with complete information
- Execute soft deletes only after thorough analysis

---

## Findings So Far

### Commission-Processing Audit (Complete)
- **Total visible:** 47 tasks
- **Legitimate:** 27 tasks (#1-16, #26-31, #42, #47, #68)
- **Suspicious:** 21 tasks (#48-67, #69)
- **Tags:** Suspicious tasks all tagged "task-viewer"
- **Report:** `task-mcp-audit-commission.md`

**Key Questions:**
- Why are tasks #16, #26-31, #42, #47 legitimate in commission-processing?
- Are these truly cross-contamination or legitimate shared tasks?
- Do these same tasks appear in task-mcp workspace?

---

## Audit Plan

### Phase 1: Complete All Audits

**✅ Commission-Processing:** DONE
- Report: `task-mcp-audit-commission.md`
- 47 tasks visible
- 21 flagged as suspicious

**⏳ Task-MCP:** PENDING
- Expected: ~24 tasks
- Look for: Framework Modernization tasks (commission-processing)
- Look for: BMCIS tasks
- Compare: Which tasks overlap with commission-processing?

**⏳ BMCIS-Knowledge-MCP:** PENDING
- Expected: Unknown (possibly 0 tasks if fresh project)
- Look for: Task-viewer tasks
- Look for: Commission-processing tasks
- Baseline: Clean workspace or also contaminated?

### Phase 2: Cross-Project Analysis

**Create Task Ownership Matrix:**
```
Task ID | Visible In Projects       | Tags              | File References      | Owner?
--------|---------------------------|-------------------|----------------------|--------
#1      | commission-processing     | framework         | commission files     | commission
#16     | commission-processing     | workflow-mcp      | commission files     | commission
#26     | commission-processing     | task-mcp          | commission files(?)  | ???????
#48     | commission-processing     | task-viewer       | task-viewer files    | task-mcp
#69     | commission-processing     | task-viewer       | task-viewer files    | task-mcp
...     | ...                       | ...               | ...                  | ...
```

**Identify Patterns:**
1. Tasks visible in multiple projects (true contamination)
2. Tasks with mismatched tags vs workspace
3. Tasks with file references pointing to wrong project
4. Tasks created in wrong conversation context

### Phase 3: Tagging Strategy

**Tag Types:**
- `needs-review` - Requires manual review
- `wrong-workspace-suspected` - Likely in wrong workspace
- `cross-project-duplicate` - Exists in multiple projects
- `legitimate-shared` - Intentionally shared across projects (if any)
- `origin-unknown` - Can't determine ownership

**Example:**
```python
# Tag task #48 in commission-processing
mcp__task-mcp__update_task(
  task_id=48,
  tags="feature-enhancement task-viewer needs-review wrong-workspace-suspected"
)
```

### Phase 4: Review & Decision

**After all audits and tagging:**
1. Review task ownership matrix
2. Identify clear cross-contamination
3. Identify ambiguous cases
4. Create cleanup plan with rationale
5. Get buy-in on cleanup approach
6. Execute soft deletes (30-day retention)

---

## Safety Principles

**DO NOT DELETE if:**
- Task visible in only one project (even if suspicious)
- Task ownership ambiguous
- All three audits not complete
- Cross-project analysis not done
- Unsure about file references or context

**SAFE TO DELETE when:**
- Task clearly belongs to Project A
- Task visible in Project B (wrong workspace)
- Tags/files/context confirm Project A ownership
- Cross-project analysis confirms
- Soft delete (30-day retention) available

---

## Current Status

**Phase 1: Audits**
- ✅ Commission-Processing: Complete (47 tasks, 21 suspicious)
- ⏳ Task-MCP: Pending
- ⏳ BMCIS-Knowledge-MCP: Pending

**Phase 2: Analysis**
- ⏳ Cross-project matrix: Waiting for audits
- ⏳ Task ownership attribution: Waiting for audits

**Phase 3: Tagging**
- ⏳ Tag suspicious tasks: Waiting for analysis

**Phase 4: Cleanup**
- ⏳ Cleanup decision: Waiting for review
- ⏳ Execute cleanup: Waiting for decision

---

## Next Immediate Steps

1. **Run task-mcp audit**
   - Navigate to: `/Users/cliffclarke/Claude_Code/task-mcp`
   - Use prompt from: `cross-project-audit-plan.md`
   - Save report: `task-mcp-audit-taskmcp.md`

2. **Run bmcis-knowledge audit**
   - Navigate to: `/Users/cliffclarke/Claude_Code/bmcis-knowledge-mcp`
   - Use prompt from: `cross-project-audit-plan.md`
   - Save report: `task-mcp-audit-bmcis.md`

3. **Create cross-project analysis**
   - Compare all three audit reports
   - Build task ownership matrix
   - Identify true contamination patterns

4. **Tag suspicious tasks**
   - Mark tasks for review (don't delete)
   - Use tagging strategy from audit plan

5. **Review & decide**
   - Look at complete picture
   - Make informed cleanup decision
   - Execute cleanup safely

---

## Files Created

**Audit Plan:**
- `scripts/cross-project-audit-plan.md` - Complete audit strategy

**Audit Reports:**
- `task-mcp-audit-commission.md` - Commission-processing results (DONE)
- `task-mcp-audit-taskmcp.md` - Task-MCP results (PENDING)
- `task-mcp-audit-bmcis.md` - BMCIS-Knowledge results (PENDING)

**Analysis:**
- `scripts/cross-project-analysis.md` - Comparison matrix (PENDING)

**Original Cleanup Tools (ON HOLD):**
- `scripts/cleanup_cross_contamination.py` - Will update with tagging mode
- `scripts/cleanup-cross-contamination.md` - Will update with revised approach

---

## Timeline

**Audit Phase:** 30-40 minutes
- Task-MCP audit: 10-15 minutes
- BMCIS-Knowledge audit: 10-15 minutes
- Cross-project analysis: 20-30 minutes

**Tagging Phase:** 15-20 minutes
- Tag suspicious tasks
- Review tags
- Adjust as needed

**Decision Phase:** 15-30 minutes
- Review complete picture
- Make cleanup decision
- Create execution plan

**Cleanup Phase (if needed):** 20-30 minutes
- Execute soft deletes
- Validate across all projects
- Document results

**Total:** 2-3 hours for thorough, safe approach

---

## Why This Approach Is Better

**Safety:**
- No premature deletions
- Complete information before deciding
- Reversible tagging first

**Thoroughness:**
- All three projects audited
- Cross-project patterns identified
- Complete task ownership attribution

**Confidence:**
- Clear rationale for each deletion
- Risk assessment per task
- Verification across all workspaces

**Documentation:**
- Audit trail preserved
- Decision rationale documented
- Reproducible process

---

**Summary:** Audit first, analyze second, tag third, decide fourth, cleanup last.

**No deletions until all three audits complete and cross-project analysis done.**
