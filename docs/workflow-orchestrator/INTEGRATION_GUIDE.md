# Universal Workflow Orchestrator - Integration & Customization Guide

**Version**: 1.0.0
**Last updated**: 2025-10-27

This guide helps you adopt the universal workflow orchestrator skill in your project. Follow the quick start for basic setup (15 minutes), then customize for your specific workflow needs.

---

## 1. Quick Start (15 Minutes)

### Step 1: Copy Skill Files (5 minutes)

**Create directory structure**:
```bash
mkdir -p .claude/skills/universal-workflow-orchestrator/references
mkdir -p .claude/skills/universal-workflow-orchestrator/assets
```

**Copy files**:
```bash
# Main skill file
cp /path/to/universal-workflow-orchestrator/SKILL.md \
   .claude/skills/universal-workflow-orchestrator/

# Reference files (optional, lazy-loaded)
cp /path/to/universal-workflow-orchestrator/references/*.md \
   .claude/skills/universal-workflow-orchestrator/references/

# Assets (optional)
cp /path/to/universal-workflow-orchestrator/assets/*.md \
   .claude/skills/universal-workflow-orchestrator/assets/
```

### Step 2: Test Invocation (5 minutes)

**Start new Claude Code session**:
```
User: "Initialize workflow orchestrator for this session"
```

**Expected response**:
```
✅ SESSION INITIALIZED - Universal Workflow Orchestrator

**Context**: {DETECTED_CONTEXT} ({CONFIDENCE})
**Branch**: {current_branch}
**Skills Loaded**: universal-workflow-orchestrator (1,200 tokens)

**Workflow Enforcement**:
- Parallel orchestration: ENABLED
- Testing discipline: ENFORCED
- Micro-commit tracking: ACTIVE (≤30 min intervals)

**System Health**:
- Git: ✅ {status}
- Quality gates: {status}
...
```

### Step 3: Verify Activation (5 minutes)

**Checklist**:
- [ ] Skill activates when you say "initialize workflow" or "start session"
- [ ] Context detection identifies your work type
- [ ] Health checks run automatically
- [ ] Session checklist generated

**If skill doesn't activate**: Check `.claude/skills/universal-workflow-orchestrator/SKILL.md` description field. Keywords should match your session start phrases.

---

## 2. Essential Customizations

### Context Types (REQUIRED)

**Default contexts** (from universal skill):
- DEVELOPMENT: General software development
- TESTING: Test implementation and quality assurance
- DOCUMENTATION: Writing docs, guides, specifications
- MAINTENANCE: Bug fixes, refactoring, dependency updates

**How to customize for your project**:

#### Option A: Software Development Project
```markdown
**Context Types**:
- BACKEND_DEV: Backend API development (backend/src/api/)
- FRONTEND_DEV: Frontend UI development (frontend/src/)
- DATABASE: Database schema changes (migrations/, models/)
- INFRASTRUCTURE: DevOps, CI/CD, deployment (infra/, .github/)
```

#### Option B: Data Science Project
```markdown
**Context Types**:
- DATA_PREP: Data cleaning and preparation (data/, notebooks/preprocessing/)
- MODEL_TRAINING: Model development (notebooks/training/, src/models/)
- EVALUATION: Model evaluation and validation (notebooks/evaluation/)
- DEPLOYMENT: Model deployment (deploy/, api/)
```

#### Option C: DevOps/Infrastructure Project
```markdown
**Context Types**:
- INFRASTRUCTURE: IaC changes (terraform/, cloudformation/)
- PIPELINE: CI/CD pipeline development (.github/, .gitlab-ci.yml)
- MONITORING: Observability setup (monitoring/, dashboards/)
- INCIDENT_RESPONSE: On-call incident handling
```

#### Option D: Documentation Project
```markdown
**Context Types**:
- USER_DOCS: User-facing documentation (docs/user-guide/)
- API_DOCS: API reference documentation (docs/api/)
- INTERNAL: Internal engineering docs (docs/internal/)
- TUTORIALS: Step-by-step tutorials (docs/tutorials/)
```

**Implementation**:

Edit `.claude/skills/universal-workflow-orchestrator/SKILL.md`:

```markdown
### 1. Task Context Detection

**Context Types**:
- **BACKEND_DEV**: Backend API development (backend/src/api/)
- **FRONTEND_DEV**: Frontend UI development (frontend/src/)
- **DATABASE**: Database schema changes (migrations/, models/)
- **INFRASTRUCTURE**: DevOps, CI/CD, deployment (infra/, .github/)

**Detection Algorithm**:
1. Parse git branch name (e.g., `feat/api-auth` → BACKEND_DEV)
2. Check current working directory path
   - `backend/src/api/` → BACKEND_DEV
   - `frontend/src/` → FRONTEND_DEV
   - `migrations/` → DATABASE
   - `infra/` OR `.github/` → INFRASTRUCTURE
3. Fallback to user confirmation if ambiguous
```

### Quality Gates (OPTIONAL)

**Purpose**: Enforce code quality before commits

**Default configuration** (customize for your stack):

```markdown
**Quality Gates**:
```bash
# Python projects
ruff check . && mypy .

# JavaScript/TypeScript projects
npm run lint && npm run type-check

# Go projects
go fmt ./... && go vet ./... && golangci-lint run

# Rust projects
cargo fmt --check && cargo clippy

# Multiple languages (run all)
./scripts/check-all.sh
```

**Implementation**:

1. **Create quality gate script** (recommended):
```bash
#!/bin/bash
# scripts/check-all.sh

set -e

echo "Running linter..."
npm run lint

echo "Running type checker..."
npm run type-check

echo "Running tests..."
npm test

echo "✅ All quality gates passed"
```

2. **Update skill SKILL.md**:
```markdown
**2. Quality Gates**:
```bash
./scripts/check-all.sh
# Verify: Code quality tools available and passing
```

3. **Add to session checklist**:
```markdown
**Workflow Reminders**:
- [ ] Run ./scripts/check-all.sh before each commit
```

### Team Structure (REQUIRED)

**Solo developer** (simplified handoffs):
```markdown
**Session Handoff Template**:
- Completed work (brief bullet points)
- Next priority (1-2 items max)
- Blockers (if any)
```

**Team of 2-5** (moderate detail):
```markdown
**Session Handoff Template**:
- Context: What problem you're solving
- Completed work: Specific accomplishments
- In-progress: What's partially done
- Next priorities: Ordered list (1-3 items)
- Blockers: Dependencies, questions, issues
- Related PRs: Links to open PRs
```

**Large team / Async collaboration** (comprehensive):
```markdown
**Session Handoff Template**:
- Executive summary (2-3 sentences)
- Context: Problem statement, background
- Completed work: Detailed accomplishments with evidence
- In-progress: Status of partial work
- Next priorities: Ordered list with time estimates
- Blockers: Dependencies, questions, issues, who can help
- Technical decisions: Architecture choices, trade-offs
- Related PRs: Links with review status
- Knowledge transfer: Key learnings, gotchas
```

**Implementation**:

Edit `.claude/skills/universal-workflow-orchestrator/assets/session-checklist.md` to match your team size and communication style.

---

## 3. File Structure Setup

### Minimal Setup (Solo Developer)

```
project-root/
├── .claude/
│   └── skills/
│       └── universal-workflow-orchestrator/
│           ├── SKILL.md                  # Main skill file
│           └── assets/
│               └── session-checklist.md  # Session template
├── session-handoffs/                     # Create this directory
└── .git/
```

### Standard Setup (Team)

```
project-root/
├── .claude/
│   └── skills/
│       └── universal-workflow-orchestrator/
│           ├── SKILL.md
│           ├── references/               # Lazy-loaded docs
│           │   ├── parallel-orchestration.md
│           │   ├── micro-commit-discipline.md
│           │   └── context-definitions.md
│           └── assets/
│               └── session-checklist.md
├── session-handoffs/
│   └── README.md                        # Handoff usage guide
├── docs/
│   ├── project-guides/                  # Project-specific docs
│   └── workflows/                       # Workflow documentation
├── scripts/
│   └── check-all.sh                     # Quality gates script
└── .git/
```

### Advanced Setup (Large Project)

```
project-root/
├── .claude/
│   ├── skills/
│   │   ├── universal-workflow-orchestrator/
│   │   └── project-specific-skill/      # Custom skills
│   └── commands/                        # Slash commands
│       ├── ready.md                     # /ready command
│       └── checkpoint.md                # /checkpoint command
├── session-handoffs/
│   ├── 2025-10/                         # Monthly organization
│   └── README.md
├── docs/
│   ├── architecture/                    # Architecture docs
│   ├── workflows/                       # Workflow guides
│   └── templates/                       # Doc templates
├── scripts/
│   ├── check-all.sh
│   └── validate.sh
└── .git/
```

**Create directories**:
```bash
mkdir -p .claude/skills/universal-workflow-orchestrator/{references,assets}
mkdir -p session-handoffs
mkdir -p docs/workflows
mkdir -p scripts
```

---

## 4. Workflow Integration

### Git Workflow

**Feature branch workflow**:
```bash
# Session start
git checkout main
git pull --ff-only
git checkout -b feat/your-feature

# Activate orchestrator
Claude: "Initialize workflow orchestrator"

# Development cycle
# ... make changes ...
./scripts/check-all.sh    # Quality gates
git add .
git commit -m "feat: implement feature"  # Micro-commit

# Session end
Claude: "Create session handoff"
git push -u origin feat/your-feature
```

**Trunk-based development**:
```bash
# Session start
git checkout main
git pull --ff-only

# Activate orchestrator
Claude: "Initialize workflow orchestrator"

# Development cycle (short-lived)
# ... make changes ...
./scripts/check-all.sh
git add .
git commit -m "feat: small change"
git push origin main
```

### Session Start Ritual

**Recommended invocation phrases**:
- "Initialize workflow orchestrator"
- "Start new session for [context]"
- "Begin work session"
- "Set up workflow for [feature]"

**What the orchestrator does**:
1. Detects context from branch/directory
2. Loads relevant skills (if configured)
3. Runs health checks (git, quality gates, dependencies)
4. Generates session checklist
5. Sets workflow expectations (parallel orchestration, micro-commits)

### Mid-Session: Micro-Commits

**Trigger points** (commit when you hit ANY of these):
- Every 20-50 lines of code
- After completing a logical milestone
- Every 30 minutes of work
- Before switching contexts
- Before running complex refactoring

**Example workflow**:
```bash
# After 30 minutes of work
./scripts/check-all.sh
git add .
git commit -m "feat(api): add user authentication endpoint"

# Continue working
# ... 40 lines later ...
./scripts/check-all.sh
git add .
git commit -m "feat(api): add input validation for auth"
```

**Benefits**:
- 80-90% reduction in work loss risk
- Clear progress tracking
- Easy rollback if needed
- Better PR reviews (atomic commits)

### Session End: Handoff Creation

**Manual handoff creation**:
```markdown
# session-handoffs/2025-10-27-1600-feature-implementation.md

## Session Handoff - Feature Implementation

**Date**: 2025-10-27 16:00
**Context**: BACKEND_DEV
**Branch**: feat/user-auth

### Completed Work
- ✅ User authentication endpoint implemented
- ✅ Input validation added
- ✅ Unit tests passing (12/12)

### In Progress
- ⏳ Integration tests (3/5 complete)

### Next Priorities
1. Complete integration tests
2. Add error handling for edge cases
3. Update API documentation

### Blockers
- None

### Notes
- Used JWT for token generation
- Password hashing uses bcrypt (cost factor 12)
```

**Automated handoff** (if using slash commands):
```bash
# If you've created a /handoff command
Claude: "/handoff Feature implementation complete"
```

### Health Checks

**Run health checks**:
- At session start (automatic)
- Before major refactoring
- After dependency updates
- When troubleshooting issues

**What gets checked**:
1. **Git status**: Branch, uncommitted files, sync status
2. **Quality gates**: Linter, type checker, tests
3. **Dependencies**: Missing packages, version conflicts
4. **File structure**: Required directories exist
5. **Tools**: Required CLI tools available

**Example health report**:
```
**System Health**:
- Git: ✅ feat/user-auth (3 uncommitted files)
- Quality gates: ✅ Passing (lint, types, tests)
- Dependencies: ✅ All installed
- Tools: ✅ node, npm, git available
```

---

## 5. Advanced Customizations (Optional)

### Skill Composition

**Example: Integrate with testing skill**:

Edit `SKILL.md`:
```markdown
### 2. Intelligent Skill Composition

**TESTING Context**:
```markdown
testing-best-practices skill (model-invoked when test context detected)
# Provides: Test patterns, coverage requirements, mocking strategies
# When: Writing tests, debugging test failures
# Activation: Claude detects "test", "spec", "coverage" keywords
```
```

**Benefit**: When you work in `tests/` directory, both workflow orchestrator AND testing skill activate automatically.

### MCP Integration

**Example: workflow-mcp for work item tracking**:

1. **Install MCP server** (if available):
```json
// claude_desktop_config.json
{
  "mcpServers": {
    "workflow-mcp": {
      "command": "uvx",
      "args": ["workflow-mcp"]
    }
  }
}
```

2. **Update skill to use MCP**:

Edit `SKILL.md`:
```markdown
**6. Project Status**:
- Primary: Query workflow-mcp database
- Fallback: Read .project-status.md file
- Extract: Active work, blockers
```

3. **Create project in MCP**:
```bash
# In Claude Code session
mcp__workflow-mcp__create_project name="your-project"
mcp__workflow-mcp__set_working_directory directory="/path/to/project"
```

### Slash Command Integration

**Example: Create /ready command**:

1. **Create `.claude/commands/ready.md`**:
```markdown
# Ready Command

Run comprehensive project setup:
1. Check git status
2. Run quality gates
3. Verify dependencies
4. Load workflow orchestrator
5. Generate session checklist

This command combines health checks with session initialization.
```

2. **Usage**:
```
User: "/ready"
Claude: [Runs all checks, loads orchestrator, provides checklist]
```

### Tool-Specific Adaptations

**Python Projects** (add to quality gates):
```markdown
**Quality Gates**:
```bash
# Formatting
black --check .

# Linting
ruff check .

# Type checking
mypy .

# Security
bandit -r src/

# Tests
pytest --cov=src tests/
```

**JavaScript/TypeScript Projects**:
```markdown
**Quality Gates**:
```bash
# Formatting
prettier --check .

# Linting
eslint .

# Type checking
tsc --noEmit

# Tests
jest --coverage
```

**Go Projects**:
```markdown
**Quality Gates**:
```bash
# Formatting
go fmt ./...

# Linting
go vet ./...
golangci-lint run

# Tests
go test -v -cover ./...
```

---

## 6. Validation Checklist

### Initial Setup
- [ ] `.claude/skills/universal-workflow-orchestrator/SKILL.md` exists
- [ ] `session-handoffs/` directory created
- [ ] Context types customized for project
- [ ] Quality gates configured (if applicable)
- [ ] Team structure template chosen

### Functional Testing
- [ ] Skill activates with "Initialize workflow orchestrator"
- [ ] Context detection identifies correct work type
- [ ] Health checks run without errors
- [ ] Session checklist generates successfully
- [ ] Quality gates execute (if configured)

### Workflow Integration
- [ ] Micro-commit discipline understood by team
- [ ] Session handoff format agreed upon
- [ ] Git workflow compatible with orchestrator
- [ ] Parallel orchestration philosophy adopted

### Optional Features
- [ ] Skill composition configured (if using multiple skills)
- [ ] MCP integration working (if applicable)
- [ ] Slash commands created (if desired)
- [ ] Tool-specific customizations applied

---

## 7. Examples by Project Type

### Software Development (Full-Stack Web App)

**Contexts**:
```markdown
- BACKEND_DEV: API development (backend/src/)
- FRONTEND_DEV: UI development (frontend/src/)
- DATABASE: Schema changes (migrations/)
- INFRASTRUCTURE: DevOps (infra/, .github/)
```

**Tools**:
```bash
# Backend (Python)
ruff check backend/ && mypy backend/

# Frontend (TypeScript)
cd frontend && npm run lint && npm run type-check

# Combined
./scripts/check-all.sh
```

**Example session**:
```
User: "Initialize workflow orchestrator"

Claude:
✅ SESSION INITIALIZED

**Context**: BACKEND_DEV (HIGH confidence)
**Branch**: feat/user-auth
**Directory**: backend/src/api/

**System Health**:
- Git: ✅ Clean working tree
- Backend quality: ✅ ruff + mypy passing
- Frontend quality: ✅ eslint + tsc passing

**Next Steps**:
1. Implement authentication endpoint
2. Add input validation
3. Write unit tests
4. Micro-commit every 30 minutes

Ready to begin. What feature are we implementing?
```

### Data Science (ML Pipeline)

**Contexts**:
```markdown
- DATA_PREP: Data cleaning (notebooks/preprocessing/)
- MODEL_TRAINING: Model development (src/models/)
- EVALUATION: Model validation (notebooks/evaluation/)
- DEPLOYMENT: Model deployment (deploy/)
```

**Tools**:
```bash
# Code quality
black --check src/ && mypy src/

# Notebook validation
nbqa black notebooks/
nbqa mypy notebooks/

# Tests
pytest tests/ --cov=src
```

**Example session**:
```
User: "Start new session for model training"

Claude:
✅ SESSION INITIALIZED

**Context**: MODEL_TRAINING (MEDIUM confidence)
**Branch**: exp/transformer-baseline
**Directory**: notebooks/training/

**System Health**:
- Git: ✅ exp/transformer-baseline (2 uncommitted notebooks)
- Code quality: ✅ black + mypy passing
- Dependencies: ✅ torch, transformers, datasets installed

**Workflow Reminders**:
- Save checkpoints frequently (every epoch)
- Log metrics to wandb/tensorboard
- Commit after each experiment run
- Document hyperparameters in notebook

Ready to train. What model architecture?
```

### DevOps/Infrastructure (Terraform)

**Contexts**:
```markdown
- INFRASTRUCTURE: IaC changes (terraform/)
- PIPELINE: CI/CD (. github/workflows/)
- MONITORING: Observability (monitoring/)
- INCIDENT_RESPONSE: On-call work
```

**Tools**:
```bash
# Terraform validation
terraform fmt -check -recursive
terraform validate
tflint

# YAML linting (CI/CD)
yamllint .github/workflows/
```

**Example session**:
```
User: "Initialize workflow for infrastructure changes"

Claude:
✅ SESSION INITIALIZED

**Context**: INFRASTRUCTURE (HIGH confidence)
**Branch**: infra/add-database
**Directory**: terraform/

**System Health**:
- Git: ✅ infra/add-database (clean)
- Terraform: ✅ fmt + validate passing
- AWS credentials: ✅ Configured

**Safety Reminders**:
- Run terraform plan before apply
- Review plan output carefully
- Use workspaces for environments
- Commit state file changes
- Micro-commit each resource addition

Ready to provision. What infrastructure are we adding?
```

### Documentation Project (Technical Writing)

**Contexts**:
```markdown
- USER_DOCS: User guides (docs/user/)
- API_DOCS: API reference (docs/api/)
- INTERNAL: Engineering docs (docs/internal/)
- TUTORIALS: Step-by-step guides (docs/tutorials/)
```

**Tools** (simplified for docs):
```bash
# Markdown linting
markdownlint docs/

# Spell checking
cspell "docs/**/*.md"

# Link validation
markdown-link-check docs/**/*.md
```

**Example session**:
```
User: "Start documentation session"

Claude:
✅ SESSION INITIALIZED

**Context**: USER_DOCS (HIGH confidence)
**Branch**: docs/authentication-guide
**Directory**: docs/user/

**System Health**:
- Git: ✅ docs/authentication-guide (1 uncommitted file)
- Markdown: ✅ No linting errors
- Spelling: ✅ No typos detected
- Links: ✅ All links valid

**Writing Workflow**:
- Outline first (commit outline)
- Write section-by-section (commit each section)
- Add examples (commit examples)
- Review and polish (commit final)

Ready to write. What guide are we creating?
```

---

## 8. Troubleshooting

### Skill Not Activating

**Symptom**: Saying "Initialize workflow orchestrator" doesn't load the skill

**Causes**:
1. **Missing SKILL.md**: Verify `.claude/skills/universal-workflow-orchestrator/SKILL.md` exists
2. **Wrong keywords**: Skill description doesn't match your invocation phrase
3. **Skill disabled**: Check if skill is enabled in Claude Code

**Solutions**:
```bash
# Verify file exists
ls -la .claude/skills/universal-workflow-orchestrator/SKILL.md

# Check description field matches keywords
# Edit SKILL.md, ensure description contains:
# "workflow orchestrator", "session initialization", "session setup"

# Try different invocation phrases
"Start workflow session"
"Initialize session orchestrator"
"Begin workflow setup"
```

### Context Detection Wrong

**Symptom**: Orchestrator detects wrong context (e.g., TESTING instead of BACKEND_DEV)

**Causes**:
1. **Ambiguous directory**: You're in a directory that matches multiple contexts
2. **Generic branch name**: Branch like `feat/update` doesn't indicate context
3. **Detection heuristics need tuning**: Default rules don't fit your project

**Solutions**:

Edit `SKILL.md` detection algorithm:
```markdown
**Detection Algorithm**:
1. Parse git branch name (PRIORITY 1)
   - `feat/api-*` → BACKEND_DEV
   - `feat/ui-*` → FRONTEND_DEV
   - `test/*` → TESTING
2. Check current working directory (PRIORITY 2)
   - Exact match: `backend/src/api/` → BACKEND_DEV
   - Partial match: `backend/tests/` → TESTING
3. Ask user if confidence < HIGH
```

**Immediate workaround**:
```
User: "Initialize workflow orchestrator for BACKEND_DEV context"
```

### Quality Gates Failing

**Symptom**: Quality gates fail at session start

**Causes**:
1. **Tools not installed**: Linter/type checker missing
2. **Configuration missing**: Tool config files not present
3. **Existing violations**: Code has pre-existing quality issues

**Solutions**:

**Install missing tools**:
```bash
# Python
pip install ruff mypy

# JavaScript
npm install --save-dev eslint @types/node typescript

# Go
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
```

**Add configuration files**:
```bash
# Python: pyproject.toml
[tool.ruff]
line-length = 100

[tool.mypy]
strict = true

# JavaScript: .eslintrc.js
module.exports = {
  extends: ['eslint:recommended'],
  rules: {}
};
```

**Fix existing violations**:
```bash
# Auto-fix what's possible
ruff check --fix .
black .

# Review remaining issues
ruff check .
```

**Temporary workaround** (not recommended):
```markdown
# Edit SKILL.md, comment out quality gates temporarily
# **2. Quality Gates**:
# ```bash
# # checkall  # TEMPORARILY DISABLED
# ```
```

### Token Budget Concerns

**Symptom**: Skill consumes too many tokens, hits context limits

**Causes**:
1. **Loading all references**: References should be lazy-loaded
2. **Large assets**: Session checklist template is too verbose
3. **Multiple skills active**: Skill composition using too many tokens

**Solutions**:

**Verify progressive disclosure**:
```markdown
# SKILL.md should only load core content (~1,200 tokens)
# References should be in separate files:
# - references/parallel-orchestration.md (900 tokens)
# - references/micro-commit-discipline.md (700 tokens)
#
# Only load references when needed:
# "Load references/parallel-orchestration.md for orchestration patterns"
```

**Simplify session checklist**:
```markdown
# Instead of 50-line checklist:
## Session Checklist

**Context**: {context}
**Branch**: {branch}
**Health**: {status}

**Reminders**:
- Parallel orchestration for complex tasks
- Micro-commits every 30 min
- Quality gates before commits

**Next**: {next_action}
```

**Use skill composition sparingly**:
- Only load 2-3 skills per session
- Unload skills when context changes
- Prefer slash commands for one-time operations

---

## Summary

### Quick Setup Checklist
1. ✅ Copy skill files to `.claude/skills/universal-workflow-orchestrator/`
2. ✅ Create `session-handoffs/` directory
3. ✅ Test invocation: "Initialize workflow orchestrator"
4. ✅ Customize context types for your project
5. ✅ Configure quality gates (if applicable)
6. ✅ Choose team structure template
7. ✅ Integrate with git workflow
8. ✅ Validate all functionality works

### Key Success Factors
- **Context detection**: Customize for your directory structure
- **Quality gates**: Match your tech stack and tools
- **Team communication**: Handoff detail matches team size
- **Workflow integration**: Fits your existing git/PR process
- **Progressive disclosure**: Only load what you need

### Next Steps
1. Run through quick start (15 minutes)
2. Customize 2-3 essential settings (contexts, quality gates, team structure)
3. Use for one full session
4. Gather feedback from team
5. Iterate on customizations
6. Document project-specific adaptations

### Getting Help
- **Skill not working**: Check troubleshooting section
- **Customization questions**: Review examples by project type
- **Advanced features**: See advanced customizations section
- **Token budget**: Use progressive disclosure, lazy-load references

---

**Ready to integrate?** Start with the Quick Start section and customize as you go. The orchestrator adapts to your workflow, not the other way around.
