---
description: Universal session initialization with intelligent context detection and directory setup
allowed-tools: [Read, Write, Bash, Glob]
---

# Universal Workflow Orchestrator - Session Initialization

**Purpose:** Automate session start with context detection, health validation, and directory setup

**Value Proposition:**
- Eliminates 15-25 min of manual setup per session
- Creates required directories automatically (idempotent)
- Validates system health before development
- Generates structured session checklist
- Works for ANY project type

**When to Use:**
- Start of every development session
- Switching to new project or task context
- After git pull (revalidate environment)
- First time using workflow in a project (handles setup automatically)

---

## STEP 1: Invoke Universal Workflow Orchestrator Skill

**Automatically load universal-workflow-orchestrator skill:**

"Apply skill: universal-workflow-orchestrator"

**This activates:**
- Context detection (git branch, directory, task type)
- Workflow principle enforcement (parallel orchestration, micro-commits)
- Health validation preparation

---

## STEP 2: Create Directory Structure (Idempotent)

**Create required directories if they don't exist:**

```bash
# Session handoffs
mkdir -p session-handoffs

# Subagent output directories (create base structure)
mkdir -p docs/subagent-reports
mkdir -p docs/analysis

# Create common agent-type directories
mkdir -p docs/subagent-reports/api-analysis
mkdir -p docs/subagent-reports/architecture-review
mkdir -p docs/subagent-reports/security-analysis
mkdir -p docs/subagent-reports/performance-analysis
mkdir -p docs/subagent-reports/code-review

echo "✅ Directory structure verified"
```

**Note:** This is idempotent (safe to run multiple times). If directories exist, no action taken.

---

## STEP 3: Context Detection

**Run these commands to gather context information:**

```bash
git rev-parse --abbrev-ref HEAD 2>/dev/null
```

```bash
pwd
```

**Then analyze the results:**
- Examine branch name for context hints:
  - Starts with `feat/` → DEVELOPMENT
  - Starts with `test/` → TESTING
  - Starts with `docs/` → DOCUMENTATION
  - Starts with `fix/` → BUGFIX
  - Otherwise → GENERAL
- Check working directory path:
  - Contains `/test/` or `/tests/` → TESTING
  - Contains `/docs/` → DOCUMENTATION
  - Contains `/src/`, `/lib/`, or `/app/` → DEVELOPMENT

**Output the detected context:**
```
📍 Detected Context: {CONTEXT_HINT}
🌿 Branch: {branch_name}
📁 Directory: {working_dir}
```

---

## STEP 4: System Health Validation

**Run health checks using separate bash commands:**

**4.1 Check Git Status**
```bash
git status --short
```
Interpret: If empty → clean working tree, otherwise count lines for uncommitted changes

**4.2 Check Branch Sync Status**
```bash
git rev-list --left-right --count @{u}...HEAD 2>/dev/null || echo "No remote tracking"
```
Interpret: First number = commits behind, second = commits ahead

**4.3 Detect Project Type**

Check for Node.js:
```bash
test -f "package.json" && echo "Node.js project" || echo "No package.json"
```

Check for Python:
```bash
test -f "pyproject.toml" && echo "Python project" || echo "No pyproject.toml"
```

Check for Rust:
```bash
test -f "Cargo.toml" && echo "Rust project" || echo "No Cargo.toml"
```

Check for Go:
```bash
test -f "go.mod" && echo "Go project" || echo "No go.mod"
```

**4.4 Check Quality Tools**

For Python projects:
```bash
command -v ruff && echo "ruff available"
```
```bash
command -v mypy && echo "mypy available"
```
```bash
command -v pytest && echo "pytest available"
```

For Node.js projects:
```bash
command -v npm && npm run 2>&1 | head -20
```
Look for "lint" and "test" in available scripts

**4.5 Count Session Handoffs**
```bash
ls -1 session-handoffs/*.md 2>/dev/null | wc -l
```
```bash
ls -t session-handoffs/*.md 2>/dev/null | head -1
```

**4.6 Count Subagent Reports**
```bash
find docs/subagent-reports -name "*.md" 2>/dev/null | wc -l
```

**Output formatted health summary:**
```
🔍 System Health Checks

✅ Git: {clean | X uncommitted changes}
{branch sync status}

✅ Project type: {Python | Node.js | Rust | Go}
   Quality tools: {available tools list}

📋 Session handoffs: {count} total
   Latest: {filename}

🤖 Subagent reports: {count} total
```

---

## STEP 5: Generate Session Checklist

**Present structured session start checklist:**

```markdown
## ✅ SESSION INITIALIZED - Universal Workflow Orchestrator

**Context**: {CONTEXT_HINT} (detected from branch/directory)
**Branch**: {CURRENT_BRANCH}
**Directory**: {WORKING_DIR}

### 📁 Directory Structure
- ✅ session-handoffs/ (ready)
- ✅ docs/subagent-reports/ (ready)
- ✅ docs/analysis/ (ready)

### 🔍 System Health
- Git: {status from checks above}
- Project type: {detected type}
- Quality tools: {available tools}
- Previous work: {handoff count} handoffs, {report count} subagent reports

### 🎯 Workflow Reminders
- [ ] Use parallel subagents for complex tasks (3+ independent analyses)
- [ ] Subagents MUST write findings to files and micro-commit
- [ ] Commit every 20-50 lines or ≤30 minutes
- [ ] Run quality gates before each commit
- [ ] Create session handoff at end (use /uwo-handoff)

### 📚 Templates Available
- Session handoff: `.claude/skills/universal-workflow-orchestrator/assets/TEMPLATE_SESSION_HANDOFF.md`
- Research report: `.claude/skills/universal-workflow-orchestrator/assets/TEMPLATE_RESEARCH_REPORT.md`

### 🚀 Recommended Next Actions
{Based on context:}
- DEVELOPMENT: Review active feature, plan implementation, run quality checks
- TESTING: Review test coverage, identify gaps, run test suite
- DOCUMENTATION: Review existing docs, identify missing sections, plan updates
- BUGFIX: Reproduce issue, analyze root cause, plan fix
- GENERAL: Review recent commits, check for open PRs, plan today's work

### 💡 Tips
- Read latest session handoff (if exists) for context
- Check for blocked work items or open questions
- Review any recent subagent reports for insights

---

**Ready to begin work!** What would you like to tackle first?
```

---

## STEP 6: Report Summary

**Provide concise summary:**

"Session initialized successfully for {CONTEXT_HINT} work.

System health: {summary of key checks}
Previous work: {handoff count} handoffs, {report count} subagent reports

Use /uwo-checkpoint during work to save progress.
Use /uwo-handoff at end of session for full context transfer.

Ready to begin!"

---

## Success Criteria

- ✅ Universal-workflow-orchestrator skill invoked
- ✅ All directories created (idempotent)
- ✅ Context detected from git/directory
- ✅ Health checks run and reported
- ✅ Session checklist generated
- ✅ Works for any project type (web, data, DevOps, etc.)
- ✅ Safe to run multiple times (no duplication)

---

## Notes

**First-time use:** Creates all directories automatically
**Subsequent use:** Validates directories exist, runs health checks
**Project-agnostic:** No hard-coded context types, detects from environment
**Extensible:** Users can customize quality checks for their tech stack
