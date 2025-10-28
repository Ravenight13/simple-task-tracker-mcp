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

**Detect current work context:**

```bash
# Get current git branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "none")

# Get working directory
WORKING_DIR=$(pwd)

# Detect context from branch name (single-line safe)
CONTEXT_HINT="GENERAL"
if echo "$CURRENT_BRANCH" | grep -q "^feat"; then CONTEXT_HINT="DEVELOPMENT"; fi
if echo "$CURRENT_BRANCH" | grep -q "^test"; then CONTEXT_HINT="TESTING"; fi
if echo "$CURRENT_BRANCH" | grep -q "^docs"; then CONTEXT_HINT="DOCUMENTATION"; fi
if echo "$CURRENT_BRANCH" | grep -q "^fix"; then CONTEXT_HINT="BUGFIX"; fi

# Override with directory detection if applicable (single-line safe)
if echo "$WORKING_DIR" | grep -q "/tests\?/"; then CONTEXT_HINT="TESTING"; fi
if echo "$WORKING_DIR" | grep -q "/docs/"; then CONTEXT_HINT="DOCUMENTATION"; fi
if echo "$WORKING_DIR" | grep -q -E "/src/|/lib/|/app/"; then CONTEXT_HINT="DEVELOPMENT"; fi

echo "📍 Detected Context: $CONTEXT_HINT"
echo "🌿 Branch: $CURRENT_BRANCH"
echo "📁 Directory: $WORKING_DIR"
```

---

## STEP 4: System Health Validation

**Run comprehensive health checks:**

```bash
echo "🔍 Running system health checks..."

# Git Status
GIT_STATUS=$(git status --short 2>/dev/null)
if [ -z "$GIT_STATUS" ]; then
    echo "✅ Git: Clean working tree"
else
    echo "⚠️  Git: $(echo "$GIT_STATUS" | wc -l) uncommitted changes"
fi

# Check if branch is synced
AHEAD_BEHIND=$(git rev-list --left-right --count @{u}...HEAD 2>/dev/null || echo "0 0")
BEHIND=$(echo "$AHEAD_BEHIND" | cut -f1)
AHEAD=$(echo "$AHEAD_BEHIND" | cut -f2)

if [ "$BEHIND" -gt 0 ]; then
    echo "⚠️  Git: $BEHIND commits behind remote (consider git pull)"
fi
if [ "$AHEAD" -gt 0 ]; then
    echo "📤 Git: $AHEAD commits ahead of remote"
fi

# Check for quality tools (language-agnostic detection)
if command -v npm &> /dev/null && [ -f "package.json" ]; then
    echo "✅ Node.js project detected"
    if npm run --silent 2>&1 | grep -q "lint"; then
        echo "   - npm run lint available"
    fi
    if npm run --silent 2>&1 | grep -q "test"; then
        echo "   - npm run test available"
    fi
fi

if command -v python3 &> /dev/null && [ -f "pyproject.toml" ]; then
    echo "✅ Python project detected"
    if command -v ruff &> /dev/null; then
        echo "   - ruff (linter) available"
    fi
    if command -v mypy &> /dev/null; then
        echo "   - mypy (type checker) available"
    fi
fi

if command -v cargo &> /dev/null && [ -f "Cargo.toml" ]; then
    echo "✅ Rust project detected"
    echo "   - cargo clippy available"
    echo "   - cargo test available"
fi

if command -v go &> /dev/null && [ -f "go.mod" ]; then
    echo "✅ Go project detected"
    echo "   - go vet available"
    echo "   - go test available"
fi

# Check for session handoffs
HANDOFF_COUNT=$(ls -1 session-handoffs/*.md 2>/dev/null | wc -l)
if [ "$HANDOFF_COUNT" -gt 0 ]; then
    LATEST_HANDOFF=$(ls -t session-handoffs/*.md 2>/dev/null | head -1)
    echo "📋 Session handoffs: $HANDOFF_COUNT total"
    echo "   Latest: $(basename "$LATEST_HANDOFF")"
else
    echo "📋 No previous session handoffs found"
fi

# Check for subagent reports
REPORT_COUNT=$(find docs/subagent-reports -name "*.md" 2>/dev/null | wc -l)
if [ "$REPORT_COUNT" -gt 0 ]; then
    echo "🤖 Subagent reports: $REPORT_COUNT total"
else
    echo "🤖 No subagent reports yet"
fi
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
