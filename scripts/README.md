# Scripts Directory

Utility scripts for task-mcp maintenance and operations.

---

## Cross-Contamination Cleanup

### Overview

Before workspace filtering fix (commit 20332c0), tasks from task-mcp were incorrectly created in the commission-processing database. These scripts help identify and clean up cross-contaminated tasks.

### Files

- **`cleanup-cross-contamination.md`** - Comprehensive cleanup guide with prompts for Claude Code
- **`cleanup_cross_contamination.py`** - Automated Python script for batch cleanup

---

## Usage

### Option 1: Automated Python Script (Recommended)

**1. Dry Run (Preview):**
```bash
cd /Users/cliffclarke/Claude_Code/task-mcp/scripts
python cleanup_cross_contamination.py --dry-run
```

Shows:
- Current task count
- Which tasks will be deleted
- Which tasks will remain
- Expected results

**2. Execute Cleanup:**
```bash
python cleanup_cross_contamination.py --execute
```

Prompts for confirmation before deleting 32 cross-contaminated tasks.

**3. Verify Results:**
```bash
python cleanup_cross_contamination.py --verify
```

Checks:
- Contamination status
- Legitimate task count (should be 15)
- Remaining tasks list

### Option 2: Claude Code with MCP Tools

Use the prompts in `cleanup-cross-contamination.md`:

1. **Phase 1: Verification** - Confirm cross-contamination exists
2. **Phase 2: Cleanup** - Execute via MCP tools (automated or manual)
3. **Phase 3: Validation** - Verify cleanup success

---

## What Gets Deleted

**Total: 32 cross-contaminated tasks**

From commission-processing workspace:
- Task #16 - Remove workflow-mcp references
- Tasks #26-31 - Task-MCP integration tasks (6 tasks)
- Task #42 - Fix subtasks expansion
- Task #47 - Validate semantic architecture
- Tasks #48-67 - Enhancement backlog (20 tasks)

**What Remains: 15 legitimate tasks**
- Task #1 - Framework Modernization v2.0
- Tasks #2-11 - Framework Modernization subtasks (10 tasks)
- Task #13 - JSON manifest for vendor golden master
- Task #14 - EPSON single-phase architecture
- Task #15 - LEGRAND single-phase architecture

---

## Safety Features

**Soft Delete:**
- Tasks marked with `deleted_at` timestamp
- 30-day retention before permanent purge
- Can be recovered if needed

**No Data Loss:**
- Tasks remain in task-mcp workspace (correct location)
- Only removes from commission-processing database
- Zero risk to primary task data

**Verification:**
- Dry run preview before execution
- Post-cleanup verification built-in
- Bidirectional workspace isolation testing

---

## Troubleshooting

**Script says "Database not found":**
- Verify workspace path is correct
- Check `~/.task-mcp/databases/` directory exists
- Ensure MCP server has created project database

**Task count doesn't match expected:**
- Some tasks may already be soft-deleted
- Run verification to see current state
- Check if cleanup was partially executed

**Tasks still visible after cleanup:**
- Terminal reload required for MCP server restart
- Close and reopen terminal
- Reconnect Claude Code to MCP server

---

## Alternative: Custom Workspace

To clean up a different workspace:

```bash
python cleanup_cross_contamination.py --dry-run \
  --workspace /path/to/other/workspace

python cleanup_cross_contamination.py --execute \
  --workspace /path/to/other/workspace
```

---

## Post-Cleanup

After cleanup completes:

1. **Verify commission-processing workspace:**
   ```bash
   cd /Users/cliffclarke/Claude_Code/commission-processing-vendor-extractors
   # Use Claude Code: mcp__task-mcp__list_tasks
   # Expected: 15 tasks only
   ```

2. **Verify task-mcp workspace (no impact):**
   ```bash
   cd /Users/cliffclarke/Claude_Code/task-mcp
   # Use Claude Code: mcp__task-mcp__list_tasks
   # Expected: ~24 tasks (unchanged)
   ```

3. **Update session handoff:**
   - Document cleanup completion
   - Record final task counts
   - Confirm workspace isolation

---

## Timeline

- **Dry Run:** 1-2 minutes
- **Execution:** 2-5 minutes (32 deletions)
- **Verification:** 1-2 minutes
- **Total:** ~5-10 minutes

---

## When to Use

**Use this cleanup when:**
- Cross-contamination confirmed via testing
- Terminal reload completed (MCP server restarted)
- Workspace filtering fix verified working
- Ready to enforce strict workspace isolation

**Skip this cleanup if:**
- Workspace isolation testing not completed
- Terminal not reloaded (fix not active)
- Unsure about contamination scope
- Want to preserve current state for analysis

---

## Questions?

See `cleanup-cross-contamination.md` for detailed documentation, testing procedures, and rollback instructions.
