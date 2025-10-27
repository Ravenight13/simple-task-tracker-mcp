# Universal Workflow Orchestrator Skill - Architecture Design

**Design Date**: 2025-10-27
**Status**: Architecture Complete
**Target Token Budget**: <4,000 tokens total (~1,500 core + ~2,500 references)

---

## Executive Summary

This document defines the architecture for a **domain-agnostic workflow orchestrator skill** that can be customized for any project. Unlike `commission-workflow-orchestrator` (domain-specific), this universal version provides a customizable framework for session initialization, context detection, workflow enforcement, and health validation across arbitrary project types.

**Key Design Principles**:
- **Universal**: Works for any project (commission processing, web apps, games, data science, etc.)
- **Customizable**: Clear configuration points for project-specific adaptation
- **Efficient**: 3-tier progressive disclosure (metadata → core → references)
- **Composable**: Integrates with project-specific skills and tools

---

## 1. Skill Metadata Design

### Name
`universal-workflow-orchestrator`

### Description (Model-Invocation Matching)
```yaml
description: >
  This skill should be used when starting work sessions to automate initialization,
  detect task context, enforce workflow principles (parallel orchestration, commit
  discipline, quality gates), and validate system health. Activates at session start
  to provide structured checklists and ensure project-specific compliance. Adaptable
  to any project domain through configuration.
```

### When to Use
- **Session start** (primary use case)
- Beginning new task or feature
- Switching between work contexts
- Need consistent workflow setup
- Onboarding new team members

### Frequency
- **Every session**: Universal benefit across all work types
- Estimated: 20-50 sessions/year (varies by project velocity)

### Token Budget Allocation

```
Total Budget: 3,800 tokens

Core SKILL.md:               1,500 tokens (always loaded)
  ├─ Metadata/Overview:        200 tokens
  ├─ Core Capabilities:        600 tokens
  ├─ Usage Workflow:           400 tokens
  └─ Integration Points:       300 tokens

References (lazy-loaded):    2,300 tokens
  ├─ parallel-orchestration-guide.md:     800 tokens
  ├─ commit-workflow.md:                  700 tokens
  ├─ session-handoff-template.md:         600 tokens
  └─ context-detection-patterns.md:       800 tokens

Assets (templates):            ~500 tokens
  └─ session-checklist-template.md:       500 tokens
```

**Progressive Disclosure**: 60% token reduction (load core only, references on-demand)

---

## 2. File Structure

```
.claude/skills/universal-workflow-orchestrator/
├── SKILL.md                                    # Core skill (1,500 tokens)
│                                               # - Overview & when to use
│                                               # - Core capabilities (6 sections)
│                                               # - Usage workflow (6 steps)
│                                               # - Integration architecture
│
├── CONFIG.yaml                                 # ⭐ NEW: Project customization
│                                               # - Context types
│                                               # - Tool mappings
│                                               # - Quality gates
│                                               # - Workflow principles
│
├── references/                                 # Lazy-loaded guidance
│   ├── parallel-orchestration-guide.md         # 800 tokens
│   │                                           # - Orchestration philosophy
│   │                                           # - When to use subagents
│   │                                           # - How to orchestrate
│   │                                           # - Real-world examples
│   │
│   ├── commit-workflow.md                      # 700 tokens
│   │                                           # - Commit discipline principles
│   │                                           # - Frequency guidelines
│   │                                           # - Milestone detection
│   │                                           # - Anti-patterns
│   │
│   ├── session-handoff-template.md             # 600 tokens
│   │                                           # - Handoff structure
│   │                                           # - What to capture
│   │                                           # - When to create
│   │                                           # - Examples
│   │
│   └── context-detection-patterns.md           # 800 tokens
│                                               # - Detection algorithms
│                                               # - Context type definitions
│                                               # - Confidence scoring
│                                               # - Ambiguity resolution
│
└── assets/                                     # Templates & examples
    ├── session-checklist-template.md           # 500 tokens (core template)
    ├── CONFIG-examples/                        # ⭐ NEW: Example configs
    │   ├── web-app-config.yaml                 # Web app project example
    │   ├── data-science-config.yaml            # Data science project example
    │   ├── game-dev-config.yaml                # Game development example
    │   └── commission-processing-config.yaml   # Real-world reference
    │
    └── customization-guide.md                  # 1,200 tokens (detailed guide)
```

**Total Files**: 12 files (1 core + 1 config + 4 references + 6 assets)

---

## 3. Progressive Disclosure Strategy

### Tier 1: Metadata (Always Loaded, ~200 tokens)
**Location**: SKILL.md header (lines 1-50)

**Contents**:
- Skill name, description
- Overview paragraph
- When to use (bullet list)
- Core capabilities (summary list)
- Token budget summary

**Purpose**: Claude can quickly assess relevance without loading full skill.

### Tier 2: Core SKILL.md (Model-Invoked, ~1,500 tokens)
**Location**: SKILL.md main body

**Contents**:
1. **Core Capabilities** (600 tokens):
   - Context detection
   - Skill composition
   - Workflow enforcement
   - Health validation
   - Session checklist generation
   - Integration architecture

2. **Usage Workflow** (400 tokens):
   - 6-step session start process
   - Examples for each step
   - Decision points

3. **Integration Points** (300 tokens):
   - Git integration
   - Tool integration (customizable)
   - Skill composition patterns

**Purpose**: Provide complete workflow guidance without reference bloat.

### Tier 3: References (Lazy-Loaded, ~2,300 tokens)
**Location**: `references/` directory

**Loading Triggers**:
- `parallel-orchestration-guide.md`: When complex orchestration needed
- `commit-workflow.md`: When establishing commit discipline
- `session-handoff-template.md`: When creating session handoffs
- `context-detection-patterns.md`: When context detection ambiguous

**Purpose**: Deep-dive guidance for specific scenarios.

---

## 4. Customization Points

### Primary Configuration: CONFIG.yaml

```yaml
# ============================================================
# Universal Workflow Orchestrator - Project Configuration
# ============================================================

project:
  name: "My Project"                              # Display name
  domain: "web-app"                               # Domain identifier
  primary_language: "Python"                      # Main language

# ============================================================
# Context Types (Customizable)
# ============================================================
# Define task contexts for your project. The orchestrator
# detects which context applies based on git branch, directory,
# and file patterns.
# ============================================================

contexts:
  - id: BACKEND_API
    name: "Backend API Development"
    description: "API endpoint implementation and database logic"
    detection_patterns:
      branches: ["feat/api-*", "fix/api-*"]
      directories: ["backend/src/api/", "backend/src/models/"]
      files: ["**/routes/*.py", "**/schemas/*.py"]

  - id: FRONTEND_UI
    name: "Frontend UI Development"
    description: "User interface components and state management"
    detection_patterns:
      branches: ["feat/ui-*", "fix/ui-*"]
      directories: ["frontend/src/", "src/components/"]
      files: ["**/*.vue", "**/*.tsx", "**/*.jsx"]

  - id: DATA_PROCESSING
    name: "Data Processing"
    description: "ETL pipelines and data transformation"
    detection_patterns:
      branches: ["feat/pipeline-*", "feat/etl-*"]
      directories: ["pipelines/", "data/processors/"]
      files: ["**/transformers/*.py", "**/loaders/*.py"]

  - id: TESTING
    name: "Testing"
    description: "Test implementation and quality assurance"
    detection_patterns:
      branches: ["test/*", "qa/*"]
      directories: ["tests/", "**/__tests__/"]
      files: ["test_*.py", "*.test.ts", "*.spec.js"]

# ============================================================
# Skills Composition (Context-Specific)
# ============================================================
# Map contexts to skills that should be suggested when
# that context is detected. Skills are model-invoked based
# on description matching.
# ============================================================

skills_by_context:
  BACKEND_API:
    - skill_name: "api-design-patterns"
      when: "Designing REST/GraphQL endpoints"
    - skill_name: "database-optimization"
      when: "Database queries or schema changes"

  FRONTEND_UI:
    - skill_name: "component-patterns"
      when: "Building UI components"
    - skill_name: "state-management-guide"
      when: "Managing application state"

  DATA_PROCESSING:
    - skill_name: "etl-best-practices"
      when: "Building data pipelines"

  TESTING:
    - skill_name: "test-automation-guide"
      when: "Writing or debugging tests"

# ============================================================
# Workflow Principles (Project-Specific)
# ============================================================
# Define workflow norms enforced during session initialization.
# These are instructional (not executable behavior).
# ============================================================

workflow_principles:
  parallel_orchestration:
    enabled: true
    description: "Main chat orchestrates, subagents execute complex tasks"
    threshold: "3+ independent tasks or 10+ file reads"

  commit_discipline:
    enabled: true
    interval_minutes: 30
    description: "Commit every 20-50 lines or ≤30 minutes"
    auto_checkpoint_tools: ["/project-checkpoint"]  # Project-specific checkpoint commands

  quality_gates:
    enabled: true
    pre_commit_checks:
      - command: "ruff check ."
        language: "Python"
      - command: "mypy ."
        language: "Python"
      - command: "npm run lint"
        language: "TypeScript"
    description: "Run quality checks before each commit"

  file_naming:
    enabled: true
    timestamp_format: "YYYY-MM-DD-HHMM"
    description: "Use timestamps in documentation filenames"
    applies_to: ["session-handoffs/", "docs/reports/", "research/"]

# ============================================================
# Tools & Integrations (Project-Specific)
# ============================================================
# Define project-specific tools, MCP servers, and slash commands
# that the orchestrator should validate during health checks.
# ============================================================

integrations:
  version_control:
    system: "git"
    main_branch: "main"
    feature_prefix: "feat/"
    fix_prefix: "fix/"

  mcp_servers:
    - name: "codebase-mcp"
      purpose: "Semantic code search"
      required: false
    - name: "project-db-mcp"
      purpose: "Project database queries"
      required: false

  slash_commands:
    - command: "/ready"
      purpose: "Research-first context loading"
      when: "Session start"
    - command: "/comply"
      purpose: "Check project standards compliance"
      when: "Pre-commit validation"
    - command: "/checkpoint"
      purpose: "Save session state"
      when: "Research milestones"

# ============================================================
# Health Validation Checks
# ============================================================
# Define what the orchestrator validates during session start.
# ============================================================

health_checks:
  git_status:
    enabled: true
    warn_if_dirty: true

  quality_gates:
    enabled: true
    run_on_start: false  # Run manually if needed

  mcp_availability:
    enabled: true
    graceful_degradation: true  # Continue if MCP offline

  project_status:
    enabled: true
    primary_source: "/status"  # Slash command or MCP tool
    fallback_source: ".project-status.json"

# ============================================================
# Session Checklist Template
# ============================================================
# Customize sections shown in session start checklist.
# ============================================================

session_checklist:
  sections:
    - id: "context"
      title: "Context Information"
      enabled: true
    - id: "skills"
      title: "Skills Loaded"
      enabled: true
    - id: "workflow"
      title: "Workflow Reminders"
      enabled: true
    - id: "health"
      title: "System Health Status"
      enabled: true
    - id: "resources"
      title: "Context-Specific Resources"
      enabled: true
    - id: "next_actions"
      title: "Recommended Next Actions"
      enabled: true
```

### Secondary Customization: SKILL.md Annotations

**Customization Markers** (inline comments in SKILL.md):
```markdown
## Context Detection

**Detection Algorithm**: {CUSTOMIZE: Define context types in CONFIG.yaml}

1. Parse git branch name (e.g., `feat/api-users` → BACKEND_API)
2. Check current working directory path
   - {CUSTOMIZE: Add directory patterns in CONFIG.yaml}
3. Read project status file
   - {CUSTOMIZE: Define status source in CONFIG.yaml}
4. Fallback to user confirmation if ambiguous

**Context Types**: {LOADED FROM CONFIG.yaml contexts section}
```

### Tertiary Customization: CONFIG-examples/

**Purpose**: Provide complete example configurations for common project types.

**Examples**:
1. **web-app-config.yaml**: Full-stack web application
   - Contexts: BACKEND_API, FRONTEND_UI, DATABASE, TESTING
   - Tools: npm, pytest, docker
   - Skills: api-patterns, component-library, database-guide

2. **data-science-config.yaml**: Data science/ML project
   - Contexts: DATA_PROCESSING, MODEL_TRAINING, ANALYSIS, EXPERIMENTATION
   - Tools: jupyter, pytest, black, mypy
   - Skills: etl-patterns, ml-workflow, visualization-guide

3. **game-dev-config.yaml**: Game development
   - Contexts: GAMEPLAY, ENGINE, ASSETS, MULTIPLAYER
   - Tools: unity-test, godot, git-lfs
   - Skills: game-patterns, performance-optimization

4. **commission-processing-config.yaml**: Real-world reference
   - Exact CONFIG.yaml from commission-processing project
   - Shows production-tested configuration

---

## 5. Integration Architecture

### Git Integration (Universal)

```
┌─────────────────────────────────────────────────────────┐
│ Universal Git Integration (No Customization Needed)     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Health Check:  git status --short --branch            │
│  Validation:    ✅ Check branch name                    │
│                 ✅ Check uncommitted files              │
│                 ✅ Check sync status                     │
│                                                         │
│  Commit Discipline: Configured in CONFIG.yaml           │
│    - interval_minutes: 30                              │
│    - auto_checkpoint_tools: ["/checkpoint"]            │
│                                                         │
│  Branch Detection: Uses CONFIG.yaml patterns            │
│    - feat/* → Feature context                          │
│    - fix/* → Bug fix context                           │
│    - test/* → Testing context                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Tool Integration (Customizable via CONFIG.yaml)

```
┌────────────────────────────────────────────────────────────┐
│ Tool Integration Architecture                              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Quality Gates (CONFIG.yaml: quality_gates)                │
│  ┌────────────────────────────────────────────────┐       │
│  │ Python:     ruff check . && mypy .              │       │
│  │ JavaScript: npm run lint && npm run typecheck   │       │
│  │ Rust:       cargo clippy && cargo test          │       │
│  │ Go:         golangci-lint run && go test ./...  │       │
│  └────────────────────────────────────────────────┘       │
│                                                            │
│  MCP Servers (CONFIG.yaml: mcp_servers)                    │
│  ┌────────────────────────────────────────────────┐       │
│  │ codebase-mcp:     Semantic search (optional)    │       │
│  │ project-db-mcp:   Project data (optional)       │       │
│  │ workflow-mcp:     Work tracking (optional)      │       │
│  └────────────────────────────────────────────────┘       │
│                                                            │
│  Slash Commands (CONFIG.yaml: slash_commands)              │
│  ┌────────────────────────────────────────────────┐       │
│  │ /ready:       Context loading                   │       │
│  │ /comply:      Compliance check                  │       │
│  │ /checkpoint:  State saving                      │       │
│  └────────────────────────────────────────────────┘       │
│                                                            │
│  Graceful Degradation: All tools optional                  │
│    - Warns if unavailable                                  │
│    - Continues session initialization                      │
│    - Documents missing tools in checklist                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Skill Composition (Tool-Agnostic Design)

```
┌──────────────────────────────────────────────────────────────┐
│ Skill Composition Architecture (Model-Invoked)               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Session Start                                               │
│       ↓                                                      │
│  universal-workflow-orchestrator (model-invoked, 1,500 tok)  │
│       ↓                                                      │
│  Context Detection (from CONFIG.yaml)                        │
│       ↓                                                      │
│  ┌─────────────────────────────────────────────────┐        │
│  │ Context-Specific Skills (model-invoked)          │        │
│  ├─────────────────────────────────────────────────┤        │
│  │                                                  │        │
│  │ IF BACKEND_API:                                  │        │
│  │   → api-design-patterns (when API work)          │        │
│  │   → database-optimization (when DB queries)      │        │
│  │                                                  │        │
│  │ IF FRONTEND_UI:                                  │        │
│  │   → component-patterns (when UI components)      │        │
│  │   → state-management-guide (when state work)     │        │
│  │                                                  │        │
│  │ IF DATA_PROCESSING:                              │        │
│  │   → etl-best-practices (when pipelines)          │        │
│  │                                                  │        │
│  │ IF TESTING:                                      │        │
│  │   → test-automation-guide (when tests)           │        │
│  │                                                  │        │
│  └─────────────────────────────────────────────────┘        │
│       ↓                                                      │
│  Workflow Enforcement (from CONFIG.yaml)                     │
│       ↓                                                      │
│  Health Validation (using CONFIG.yaml integrations)          │
│       ↓                                                      │
│  Session Checklist Generated                                 │
│                                                              │
│  ⚠️ Model-Invoked Architecture:                              │
│  - Skills activate via description matching                  │
│  - No programmatic invocation exists                         │
│  - Claude determines relevance based on context              │
│  - CONFIG.yaml provides hints, not execution                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Team Structure Awareness (Optional)

```yaml
# CONFIG.yaml extension for team structure

team_structure:
  enabled: true
  team_size: "5-10"           # small, medium, large
  workflow_style: "agile"      # agile, waterfall, hybrid

  code_review:
    required: true
    min_reviewers: 1

  documentation:
    required: true
    locations: ["docs/", "README.md"]

  testing:
    required: false            # Not mandatory
    encouraged: true           # But encouraged
```

**Integration**: Orchestrator includes team reminders in checklist:
```markdown
**Team Reminders**:
- [ ] PR requires 1+ reviewers (team policy)
- [ ] Update documentation if API changes
- [ ] Tests encouraged for critical paths
```

---

## 6. Customization vs Universal Trade-offs

### Decision Matrix

| Feature | Universal (✅) | Customizable (🔧) | Notes |
|---------|---------------|-------------------|-------|
| Git integration | ✅ | - | Works universally |
| Context detection | - | 🔧 | Project-specific contexts |
| Skill composition | - | 🔧 | Project-specific skills |
| Workflow principles | ✅ | 🔧 | Common principles + custom |
| Quality gates | - | 🔧 | Language/tool-specific |
| MCP servers | - | 🔧 | Optional integrations |
| Health checks | ✅ | 🔧 | Core checks + custom |
| Session checklist | ✅ | 🔧 | Standard structure + custom |

### Customization Effort Levels

**Minimal Customization** (1-2 hours):
- Define 3-5 context types
- List quality gate commands
- Specify MCP servers (if any)
- Enable/disable workflow principles

**Moderate Customization** (3-5 hours):
- Define context detection patterns
- Map skills to contexts
- Customize session checklist sections
- Add team structure policies

**Extensive Customization** (6-10 hours):
- Create custom reference files
- Write project-specific examples
- Integrate with custom MCP servers
- Build domain-specific health checks

---

## 7. Token Optimization Techniques

### Technique 1: Configuration File (Not in Token Context)
**Savings**: ~500-800 tokens

**Rationale**: CONFIG.yaml is READ at runtime, not loaded into context.

```markdown
# SKILL.md references config
**Context Types**: {LOADED FROM CONFIG.yaml}

# Claude reads config file when needed
# Config contents not counted against token budget
```

### Technique 2: Lazy Reference Loading
**Savings**: 60% (2,300 tokens available, ~800 typical usage)

**Pattern**:
```markdown
**For detailed orchestration guidance**, load `references/parallel-orchestration-guide.md` (800 tokens)
```

### Technique 3: Asset Templates (External)
**Savings**: ~500 tokens

**Pattern**: Session checklist template stored in `assets/`, not in SKILL.md.

### Technique 4: Example Configs (Not Loaded)
**Savings**: ~1,000+ tokens

**Pattern**: `CONFIG-examples/` directory provides complete examples but is NEVER loaded into context.

### Technique 5: Conditional Sections
**Savings**: ~200-400 tokens per context

**Pattern**:
```markdown
{IF BACKEND_API:}
### Backend API Patterns Available
- REST endpoint design
- Database query optimization
- Authentication patterns

{IF FRONTEND_UI:}
### Frontend Patterns Available
- Component composition
- State management
- Responsive design
```

**Total Optimization**: ~3,000-4,000 tokens saved vs full inline documentation

---

## 8. Success Criteria

### Architecture Quality Metrics

✅ **Universal Applicability**:
- Works for web apps, data science, game dev, commission processing
- No hard-coded domain assumptions
- Clear customization boundaries

✅ **Token Efficiency**:
- Core SKILL.md: ≤1,500 tokens
- Total budget: ≤4,000 tokens
- 60% reduction via progressive disclosure

✅ **Customization Clarity**:
- CONFIG.yaml is primary customization point
- {CUSTOMIZE} markers in SKILL.md for secondary customization
- Example configs for common domains

✅ **Integration Architecture**:
- Git: Universal (no customization)
- Tools: Fully customizable (CONFIG.yaml)
- Skills: Model-invoked composition
- Team: Optional awareness

✅ **Documentation Completeness**:
- Clear separation: universal vs customizable
- File tree structure
- Progressive disclosure explanation
- Real-world examples

---

## 9. Implementation Roadmap

### Phase 1: Core Structure (2-3 hours)
- [ ] Create file structure
- [ ] Write SKILL.md core (1,500 tokens)
- [ ] Create CONFIG.yaml template
- [ ] Write session-checklist-template.md

### Phase 2: References (2-3 hours)
- [ ] Write parallel-orchestration-guide.md (800 tokens)
- [ ] Write commit-workflow.md (700 tokens)
- [ ] Write session-handoff-template.md (600 tokens)
- [ ] Write context-detection-patterns.md (800 tokens)

### Phase 3: Examples (1-2 hours)
- [ ] Create web-app-config.yaml example
- [ ] Create data-science-config.yaml example
- [ ] Create game-dev-config.yaml example
- [ ] Create commission-processing-config.yaml (real-world reference)

### Phase 4: Documentation (1 hour)
- [ ] Write customization-guide.md
- [ ] Add inline {CUSTOMIZE} markers to SKILL.md
- [ ] Validate token counts
- [ ] Test with multiple project types

**Total Estimated Effort**: 6-9 hours

---

## 10. Real-World Validation Strategy

### Validation 1: Port Commission Processing
**Goal**: Prove existing commission-workflow-orchestrator can be represented in universal architecture

**Test**: Create `commission-processing-config.yaml` that replicates current behavior

**Success**: Identical functionality with universal skill + custom config

### Validation 2: Apply to Web App
**Goal**: Prove universal skill works for different domain

**Test**: Create `web-app-config.yaml` for hypothetical React + FastAPI project

**Success**: Session initialization provides relevant context (API patterns, React components)

### Validation 3: Apply to Data Science
**Goal**: Prove universal skill adapts to non-web domains

**Test**: Create `data-science-config.yaml` for Jupyter + ML project

**Success**: Session initialization detects notebook context, suggests ETL patterns

### Validation 4: Token Budget Compliance
**Goal**: Prove progressive disclosure achieves 60% reduction

**Test**: Load core SKILL.md only, measure token count

**Success**: ≤1,500 tokens core, ≤4,000 total with all references

---

## 11. Comparison: Universal vs Domain-Specific

### commission-workflow-orchestrator (Domain-Specific)

**Strengths**:
- ✅ Tightly integrated with commission processing domain
- ✅ References specific tools (checkall, /cc-ready)
- ✅ Knows about Pattern Library Guide
- ✅ Production-tested with real workflows

**Limitations**:
- ❌ Only works for commission processing
- ❌ Hard-coded context types (VENDOR/FRONTEND/API/TESTING)
- ❌ Can't adapt to other projects

### universal-workflow-orchestrator (Universal)

**Strengths**:
- ✅ Works for any project domain
- ✅ Customizable contexts via CONFIG.yaml
- ✅ Tool-agnostic integration architecture
- ✅ Reusable across portfolio

**Limitations**:
- ❌ Requires upfront configuration
- ❌ Less opinionated (needs project-specific decisions)
- ❌ Not production-tested (yet)

### Recommended Usage

**Use domain-specific** when:
- Single project with stable domain
- Want opinionated guidance
- Don't need reusability

**Use universal** when:
- Multiple projects or portfolio
- Want flexibility
- Expect domain evolution

---

## 12. Key Architectural Innovations

### Innovation 1: CONFIG.yaml Separation
**What**: Project configuration lives in YAML, not SKILL.md
**Why**: Zero token cost (read at runtime, not loaded into context)
**Impact**: ~500-800 token savings

### Innovation 2: Model-Invoked Skill Composition
**What**: Skills activate via description matching, orchestrated by CONFIG.yaml hints
**Why**: No programmatic invocation exists in Claude Code
**Impact**: Clear mental model, correct expectations

### Innovation 3: 3-Tier Progressive Disclosure
**What**: Metadata → Core → References
**Why**: Load only what's needed for current task
**Impact**: 60% token reduction (vs full inline documentation)

### Innovation 4: Example Configs as Documentation
**What**: Complete CONFIG.yaml examples for common domains
**Why**: Easier to customize by example than from scratch
**Impact**: 2-3x faster customization

### Innovation 5: Graceful Tool Degradation
**What**: All tools optional, warns if unavailable
**Why**: Skill works even if MCP servers offline
**Impact**: Robust across environments

---

## 13. Open Questions & Future Extensions

### Question 1: Multi-Project Workspaces
**Scenario**: Developer works on 3 projects simultaneously
**Challenge**: How does orchestrator detect which project?
**Possible Solution**: Read `.universal-workflow/` in project root

### Question 2: Dynamic Context Switching
**Scenario**: Work on backend API, then switch to frontend UI in same session
**Challenge**: Update context mid-session
**Possible Solution**: `/switch-context {context_id}` command

### Question 3: Context Hierarchy
**Scenario**: BACKEND_API → AUTHENTICATION (sub-context)
**Challenge**: Nested contexts with inheritance
**Possible Solution**: CONFIG.yaml supports parent/child relationships

### Future Extension 1: AI-Generated Configs
**Idea**: Analyze project structure, auto-generate CONFIG.yaml
**Value**: Zero-effort customization
**Implementation**: Subagent analyzes repo, writes config

### Future Extension 2: Team Templates
**Idea**: Pre-built configs for common stacks (MERN, Django, Rails, etc.)
**Value**: Instant setup for standard architectures
**Implementation**: Community-contributed configs

### Future Extension 3: Session Analytics
**Idea**: Track which contexts used most, workflow compliance
**Value**: Data-driven workflow optimization
**Implementation**: MCP server for session metrics

---

## 14. Appendix: ASCII Architecture Diagrams

### Session Start Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     SESSION START                               │
│                          ↓                                       │
│              universal-workflow-orchestrator                     │
│                     (model-invoked)                             │
│                          ↓                                       │
│         ┌────────────────┴────────────────┐                     │
│         ↓                                  ↓                     │
│   Read CONFIG.yaml              Detect git context              │
│         ↓                                  ↓                     │
│   Load context types            Parse branch name               │
│         ↓                                  ↓                     │
│   Load quality gates            Check directory path            │
│         ↓                                  ↓                     │
│   Load workflow rules           Read status file                │
│         └──────────────┬──────────────────┘                     │
│                        ↓                                         │
│              Context Identified (e.g., BACKEND_API)             │
│                        ↓                                         │
│         ┌──────────────┴──────────────┐                         │
│         ↓                              ↓                         │
│   Suggest Skills              Enforce Workflow                  │
│   (from CONFIG.yaml)          (from CONFIG.yaml)                │
│         ↓                              ↓                         │
│   api-design-patterns         Parallel orchestration: ON        │
│   database-optimization       Commit discipline: 30 min         │
│         ↓                              ↓                         │
│         └──────────────┬──────────────┘                         │
│                        ↓                                         │
│              Validate System Health                             │
│                        ↓                                         │
│         ┌──────────────┴──────────────┐                         │
│         ↓              ↓               ↓                         │
│      Git OK       Quality Gates    MCP Servers                  │
│         ✅             ✅               ⚠️ (optional)             │
│         └──────────────┬──────────────┘                         │
│                        ↓                                         │
│              Generate Session Checklist                         │
│                        ↓                                         │
│              Present to User                                    │
│                        ↓                                         │
│              Ready to Begin Work                                │
└─────────────────────────────────────────────────────────────────┘
```

### Context Detection Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│                  CONTEXT DETECTION ALGORITHM                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Parse Git Branch                                       │
│  ┌─────────────────────────────────────────────────┐           │
│  │ Branch: feat/api-users                           │           │
│  │   ↓                                              │           │
│  │ Match CONFIG.yaml patterns:                      │           │
│  │   feat/api-* → BACKEND_API (HIGH confidence)     │           │
│  └─────────────────────────────────────────────────┘           │
│                        ↓                                         │
│  Step 2: Check Working Directory                                │
│  ┌─────────────────────────────────────────────────┐           │
│  │ CWD: /project/backend/src/api/                   │           │
│  │   ↓                                              │           │
│  │ Match CONFIG.yaml patterns:                      │           │
│  │   backend/src/api/ → BACKEND_API (HIGH)          │           │
│  └─────────────────────────────────────────────────┘           │
│                        ↓                                         │
│  Step 3: Read Status File (optional)                            │
│  ┌─────────────────────────────────────────────────┐           │
│  │ Source: /status or .project-status.json          │           │
│  │   ↓                                              │           │
│  │ Active Work: "Implementing user authentication" │           │
│  │   ↓                                              │           │
│  │ Keywords: "authentication" → BACKEND_API         │           │
│  └─────────────────────────────────────────────────┘           │
│                        ↓                                         │
│  Step 4: Confidence Scoring                                     │
│  ┌─────────────────────────────────────────────────┐           │
│  │ Branch match:    HIGH    (50 points)            │           │
│  │ Directory match: HIGH    (40 points)            │           │
│  │ Status match:    MEDIUM  (10 points)            │           │
│  │ Total:           100 points → HIGH confidence   │           │
│  └─────────────────────────────────────────────────┘           │
│                        ↓                                         │
│  Step 5: Fallback (if ambiguous)                                │
│  ┌─────────────────────────────────────────────────┐           │
│  │ If confidence < MEDIUM:                          │           │
│  │   Ask user: "Which context applies?"             │           │
│  │   Options: {contexts from CONFIG.yaml}           │           │
│  └─────────────────────────────────────────────────┘           │
│                        ↓                                         │
│                Context: BACKEND_API                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Token Budget Breakdown

```
┌─────────────────────────────────────────────────────────────────┐
│                  TOKEN BUDGET BREAKDOWN                         │
│                    (3,800 total tokens)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SKILL.md (Core, Always Loaded)                1,500 tokens     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Metadata/Overview                200 tokens              │  │
│  │ Core Capabilities (6 sections)   600 tokens              │  │
│  │ Usage Workflow (6 steps)         400 tokens              │  │
│  │ Integration Points               300 tokens              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  CONFIG.yaml (Not in Token Budget)               0 tokens      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Read at runtime, not loaded into context                 │  │
│  │ Contains: contexts, skills, workflow, integrations       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  References (Lazy-Loaded)                       2,300 tokens    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ parallel-orchestration-guide.md    800 tokens            │  │
│  │ commit-workflow.md                 700 tokens            │  │
│  │ session-handoff-template.md        600 tokens            │  │
│  │ context-detection-patterns.md      800 tokens            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Assets (External Templates)                      0 tokens      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ session-checklist-template.md      (stored externally)   │  │
│  │ CONFIG-examples/                   (never loaded)        │  │
│  │ customization-guide.md             (on-demand only)      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Typical Session Load                           1,500 tokens    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Core SKILL.md only                                        │  │
│  │ References loaded ~40% of sessions                        │  │
│  │ Average: 1,500 + (2,300 × 0.4) = ~2,400 tokens           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Token Efficiency: 60% reduction vs full inline (6,000 tokens) │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 15. Summary

### Architecture Highlights

✅ **Universal Design**: Works for any project domain
✅ **CONFIG.yaml Customization**: Primary customization point (zero token cost)
✅ **3-Tier Progressive Disclosure**: Metadata → Core (1,500) → References (2,300)
✅ **Token Efficient**: <4,000 total, ~2,400 typical usage (60% reduction)
✅ **Tool-Agnostic**: Integrates with any git, quality gates, MCP servers
✅ **Model-Invoked Composition**: Skills activate via description matching
✅ **Graceful Degradation**: All integrations optional, robust if offline
✅ **Example-Driven**: CONFIG-examples for web, data science, games, commission

### Customization Levels

- **Minimal** (1-2 hours): Define contexts, quality gates, MCP servers
- **Moderate** (3-5 hours): Detection patterns, skill mappings, team policies
- **Extensive** (6-10 hours): Custom references, domain examples, MCP integrations

### Implementation Next Steps

1. Create file structure (12 files)
2. Write SKILL.md core (1,500 tokens)
3. Write CONFIG.yaml template
4. Write 4 reference files (2,300 tokens)
5. Create 4 example configs
6. Validate with real projects (commission, web app, data science)

**Total Effort**: 6-9 hours
**Reuse Value**: Infinite (applies to all future projects)

---

**END OF ARCHITECTURE DESIGN**
