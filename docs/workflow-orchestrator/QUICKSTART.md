# Quick Start - Universal Workflow Orchestrator for simple-task-tracker-mcp

**Installation Date**: 2025-10-27
**Status**: ✅ Installed and Ready to Use

---

## 🚀 Try It Now (2 Minutes)

### Step 1: Start New Session in This Project

Open a new Claude Code session in the simple-task-tracker-mcp project.

### Step 2: Invoke the Skill

Say one of these phrases:
```
"Initialize workflow orchestrator"
"Start new session"
"Begin work session"
```

### Step 3: Expected Response

You should see:
```
✅ SESSION INITIALIZED - Universal Workflow Orchestrator

**Context**: {DETECTED_CONTEXT} (confidence: HIGH/MEDIUM/LOW)
**Branch**: {your-branch}
**Skills Loaded**: universal-workflow-orchestrator (1,640 tokens)

**Workflow Enforcement**:
- Parallel orchestration: ENABLED
- Micro-commit tracking: ACTIVE (≤30 min intervals)
- Quality gates: [to be configured]

**System Health**:
- Git: ✅ {status}
...

Ready to begin work. What would you like to tackle first?
```

---

## ⚙️ Essential Customization for This Project (15 Minutes)

### 1. Define Context Types

**Recommended for simple-task-tracker-mcp** (MCP server project):

Edit `.claude/skills/universal-workflow-orchestrator/SKILL.md`, find Section 2 and replace with:

```markdown
### 2. Context Detection (Generic)

**Context Types (Customizable)**:
- **MCP_SERVER_DEV**: MCP server implementation (src/, server/)
- **TESTING**: Test implementation (tests/)
- **DOCUMENTATION**: Technical docs (docs/, README.md)
- **INFRASTRUCTURE**: Deployment and tooling (scripts/, docker/)

**Detection Algorithm**:
1. Parse git branch name:
   - `feat/server-*`, `feat/mcp-*` → MCP_SERVER_DEV
   - `test/*` → TESTING
   - `docs/*` → DOCUMENTATION
   - `infra/*`, `deploy/*` → INFRASTRUCTURE
2. Check current working directory:
   - `src/`, `server/` → MCP_SERVER_DEV
   - `tests/` → TESTING
   - `docs/` → DOCUMENTATION
   - `scripts/`, `docker/` → INFRASTRUCTURE
3. Fallback to user confirmation if ambiguous
```

### 2. Configure Quality Gates

Since this is a Python MCP server project, add these quality gates:

Edit `.claude/skills/universal-workflow-orchestrator/SKILL.md`, find Section 3 and update:

```markdown
**3. Quality Gates Before Commit**:
```bash
# Python MCP Server
ruff check . && mypy .      # Linting + type checking
pytest tests/ -v             # Run tests (if available)
```
```

### 3. Create Quality Gate Script (Optional but Recommended)

```bash
# Create scripts directory
mkdir -p scripts

# Create check script
cat > scripts/check-all.sh << 'SCRIPT'
#!/bin/bash
set -e

echo "🔍 Running quality checks for simple-task-tracker-mcp..."

echo "📝 Linting with ruff..."
ruff check .

echo "🔍 Type checking with mypy..."
mypy .

echo "🧪 Running tests..."
if [ -d "tests" ]; then
    pytest tests/ -v
else
    echo "No tests directory found, skipping tests"
fi

echo "✅ All quality gates passed!"
SCRIPT

# Make executable
chmod +x scripts/check-all.sh
```

---

## 📋 Typical Workflow for This Project

### Session Start
```bash
# Terminal
cd /Users/cliffclarke/Claude_Code/simple-task-tracker-mcp
git status

# Claude Code
User: "Initialize workflow orchestrator"
```

### Development Cycle
```bash
# Make changes to MCP server code...
# After 30 minutes or 20-50 lines:

./scripts/check-all.sh      # Run quality gates
git add .
git commit -m "feat(mcp): implement task listing endpoint"

# Continue work...
```

### Session End
```bash
# Create session handoff (manual)
cat > session-handoffs/2025-10-27-1600-mcp-implementation.md << 'EOF'
# Session Handoff - MCP Server Implementation

**Date**: 2025-10-27 16:00
**Context**: MCP_SERVER_DEV
**Branch**: feat/mcp-list-tasks

## Completed Work
- ✅ Implemented list_tasks MCP tool
- ✅ Added type annotations with Pydantic v2
- ✅ Unit tests passing (5/5)

## Next Priorities
1. Add filtering support (priority, status)
2. Implement pagination
3. Update API documentation

## Blockers
- None
EOF
```

---

## 🎯 Project-Specific Tips

### For MCP Server Development
- **Context Focus**: Most work will be in MCP_SERVER_DEV context
- **Testing**: Use production MCP tools for testing (no wrappers)
- **Micro-commits**: Commit after each tool/endpoint implementation
- **Documentation**: Update README.md with each new tool

### Quality Gates for Python MCP
```bash
# Comprehensive check
ruff check .                 # Fast linting
mypy .                       # Type safety
pytest tests/ -v --cov=src   # Tests with coverage
```

### Parallel Orchestration Examples
When you need to:
- Analyze multiple MCP tool implementations → Spawn 1 agent per tool
- Review documentation across multiple files → Parallel document review
- Implement multiple related features → 1 agent per feature in parallel

---

## 📚 Next Steps

1. **Try It Now**: Test the skill with "Initialize workflow orchestrator"
2. **Customize**: Apply the 3 essential customizations above (15 minutes)
3. **Use for One Session**: Develop for 1-2 hours using the orchestrator
4. **Iterate**: Adjust context types and quality gates based on experience
5. **Refer to Docs**: Use `docs/workflow-orchestrator/INTEGRATION_GUIDE.md` for detailed guidance

---

## 🔗 Quick Reference

- **Main Skill**: `.claude/skills/universal-workflow-orchestrator/SKILL.md`
- **Complete Guide**: `docs/workflow-orchestrator/INTEGRATION_GUIDE.md`
- **Patterns Reference**: `docs/workflow-orchestrator/WORKFLOW_PATTERNS.md`
- **Architecture**: `docs/workflow-orchestrator/ARCHITECTURE.md`
- **Session Handoffs**: `session-handoffs/` (create files here)

---

## 🆘 Troubleshooting

**Skill not activating?**
- Check `.claude/skills/universal-workflow-orchestrator/SKILL.md` exists
- Try "Start workflow session" or "Initialize session orchestrator"
- Ensure you're in the simple-task-tracker-mcp directory

**Context detection wrong?**
- Manually specify: "Initialize workflow orchestrator for MCP_SERVER_DEV context"
- Customize detection algorithm in SKILL.md Section 2

**Quality gates failing?**
- Install tools: `pip install ruff mypy pytest`
- Create pyproject.toml with tool configurations
- Run `./scripts/check-all.sh` to test

---

**Ready to start?** Open a new Claude Code session and say "Initialize workflow orchestrator"!
