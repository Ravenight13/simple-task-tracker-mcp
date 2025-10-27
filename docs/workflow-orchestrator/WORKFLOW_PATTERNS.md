# Universal Workflow Patterns for Software Projects

**Version:** 1.0.0
**Extracted From:** commission-workflow-orchestrator skill (commission-processing project)
**Domain:** Language-agnostic software development workflows
**Token Budget:** ~2,800 tokens

---

## Overview

This document extracts universal workflow patterns that apply to ANY software project, regardless of domain, language, or technology stack. These patterns emerged from production use in a financial data processing system but are designed to be completely domain-agnostic.

**Core Philosophy:** Structure workflows around context detection, parallel execution, quality gates, and work preservation through micro-commits.

---

## 1. Core Workflow Principles

### 1.1 Parallel Task Orchestration

**Principle:** Decompose complex work into independent parallel tasks rather than sequential execution.

**Universal Pattern:**
```
Main Chat/Session = Orchestration Layer
    ↓
Spawn parallel specialist agents/tasks for:
    - Independent research tasks
    - Multiple file analyses
    - Component reviews
    - Documentation generation
    - Test suites
```

**Benefits:**
- **Speed:** 3-15x faster completion (N tasks in parallel vs sequential)
- **Expertise:** Specialized focus per task
- **Token efficiency:** Isolated contexts prevent bloat
- **Clarity:** Clear separation of orchestration vs execution

**When to Apply:**
- Multiple independent tasks (>3 tasks)
- Complex research requiring diverse expertise
- Multi-component analysis (architecture, security, performance)
- Bulk operations (analyzing 10+ files, generating reports)

**When NOT to Apply:**
- Single straightforward task
- Sequential dependencies (Task B needs Task A output)
- Trivial operations (<5 minutes)

**Example Application Across Domains:**

**Web Development:**
```
Frontend Feature → Parallel Tasks:
    - Component architecture design
    - API integration strategy
    - Accessibility audit
    - Performance optimization plan
```

**Data Science:**
```
Model Development → Parallel Tasks:
    - Data exploration analysis
    - Feature engineering research
    - Model selection evaluation
    - Hyperparameter tuning strategy
```

**DevOps:**
```
Infrastructure Change → Parallel Tasks:
    - Security impact analysis
    - Performance impact modeling
    - Cost estimation
    - Rollback procedure design
```

---

### 1.2 Micro-Commit Discipline

**Principle:** Commit frequently (every 20-50 lines OR ≤30 minutes) to prevent work loss and create recoverable milestones.

**Universal Pattern:**
```
Development Loop:
1. Write 20-50 lines or reach logical milestone
2. Run quality gates (linters, type checkers, tests)
3. Commit if gates pass
4. Repeat
```

**Risk Reduction:** 80-90% reduction in work loss during crashes/disconnects

**Target Frequency:** ≤30 minutes between commits
- Research phase: Auto-commit at milestones
- Implementation phase: Every 20-50 lines or logical unit

**Logical Milestones (Language-Agnostic):**
- Helper function completion (15-30 lines)
- Single component/module implementation (40-60 lines)
- Test suite for one feature (20-40 lines)
- Configuration file updates (any size)
- Documentation section completion

**Example Across Languages:**

**Python:**
```python
# Commit 1: Helper function
def parse_configuration(config_path: str) -> dict:
    """Parse config file."""
    # 20-30 lines
    return config

# COMMIT: "feat(config): add configuration parser helper"

# Commit 2: Validation logic
def validate_configuration(config: dict) -> bool:
    """Validate parsed config."""
    # 25-35 lines
    return is_valid

# COMMIT: "feat(config): add configuration validation"
```

**JavaScript/TypeScript:**
```typescript
// Commit 1: Component structure
export const UserProfile: React.FC<Props> = ({ userId }) => {
    // 40-50 lines of component logic
    return <ProfileCard />;
};

// COMMIT: "feat(ui): add UserProfile component"

// Commit 2: Unit tests
describe('UserProfile', () => {
    // 30-40 lines of tests
});

// COMMIT: "test(ui): add UserProfile component tests"
```

**Go:**
```go
// Commit 1: Service interface
type DataService interface {
    Fetch(id string) (*Data, error)
    Store(data *Data) error
}

// COMMIT: "feat(service): define data service interface"

// Commit 2: Implementation
type dataServiceImpl struct { /* ... */ }
func (s *dataServiceImpl) Fetch(id string) (*Data, error) {
    // 30-40 lines
}

// COMMIT: "feat(service): implement data service fetch method"
```

**Integration with Quality Gates:**
```bash
# NEVER commit without passing checks
make lint        # Language-specific linter
make typecheck   # Type safety validation (if applicable)
make test        # Unit tests (if available)

# Only commit if all pass
git add {files}
git commit -m "{type}({scope}): {message}"
```

---

### 1.3 Session Handoff Structure

**Principle:** Transfer session state between work periods through structured documentation.

**Universal Pattern:**
```markdown
# Session Handoff: {Work Description}

**Date:** YYYY-MM-DD
**Time:** HH:MM
**Context:** {Project area, feature, bugfix}
**Status:** {In Progress, Blocked, Complete}

## Executive Summary
- What was accomplished
- Current state
- Blockers (if any)

## Completed Work
- Detailed breakdown of completed tasks
- Key decisions made
- Files changed

## Next Priorities
1. Immediate actions (today/next session)
2. Short-term actions (this week)
3. Medium-term actions (this sprint/month)

## Context for Next Session
- Files to read first
- Key decisions to remember
- Technical details (branches, configs, etc.)
```

**File Naming Convention:** `YYYY-MM-DD-HHMM-description.md`
- Examples:
  - `2025-10-26-1430-api-authentication-refactor.md`
  - `2025-10-26-0900-database-migration-complete.md`

**Benefits:**
- 15-25 minute session startup reduction
- Clear context restoration
- Prevents duplicate work
- Tracks decision rationale

**Example Usage Across Domains:**

**Web Development Handoff:**
```markdown
# Session Handoff: Frontend Authentication Flow

**Date:** 2025-10-26
**Time:** 14:30
**Context:** User authentication refactor (OAuth2 → JWT)
**Status:** 60% Complete

## Completed Work
- ✅ JWT token generation service
- ✅ Refresh token rotation logic
- ✅ Integration tests for auth endpoints

## Next Priorities
1. Frontend token storage strategy (today)
2. Implement logout flow (tomorrow)
3. Update API documentation (this week)

## Context for Next Session
- Read: `src/auth/jwt-service.ts` (new implementation)
- Decision: Chose 15-min access token expiry (security vs UX tradeoff)
- Branch: `feat/jwt-authentication`
```

**Data Science Handoff:**
```markdown
# Session Handoff: Model Feature Engineering

**Date:** 2025-10-26
**Time:** 09:00
**Context:** Customer churn prediction model
**Status:** Feature engineering complete, tuning next

## Completed Work
- ✅ Created 12 new features (engagement scores, usage patterns)
- ✅ Feature importance analysis (top 5 identified)
- ✅ Train/test split with stratification

## Next Priorities
1. Hyperparameter tuning (GridSearchCV) - 2-3 hours
2. Cross-validation with new features - 1 hour
3. Model evaluation report - 1 hour

## Context for Next Session
- Read: `notebooks/feature-engineering-v3.ipynb`
- Decision: Removed 8 correlated features (>0.8 correlation)
- Data: `data/processed/features_v3.csv`
```

---

### 1.4 Quality Gate Integration

**Principle:** Enforce automated checks at every commit to prevent quality drift.

**Universal Pattern:**
```bash
# Pre-commit checklist (customize per language/stack)
1. Code formatting/linting
2. Type safety validation (if applicable)
3. Unit tests (if available)
4. Security checks (if critical)

# Example multi-language implementations:

# Python
ruff check . && mypy . && pytest

# JavaScript/TypeScript
npm run lint && npm run typecheck && npm run test

# Go
golangci-lint run && go test ./...

# Rust
cargo clippy && cargo test

# Java
./gradlew check test
```

**Quality Gate Categories:**

1. **Code Quality** (Universal)
   - Linting (language-specific rules)
   - Formatting (style consistency)
   - Complexity checks (cyclomatic complexity)

2. **Type Safety** (Typed Languages)
   - Static type checking (TypeScript, mypy, Go compiler)
   - Type annotation coverage (Python, optional JS)

3. **Testing** (All Projects)
   - Unit tests (when available)
   - Integration tests (critical paths)
   - Test coverage tracking (optional)

4. **Security** (Production Code)
   - Dependency scanning (npm audit, safety, etc.)
   - Secret detection (git-secrets, trufflehog)
   - SAST tools (language-specific)

**Integration Points:**
- Pre-commit hooks (local enforcement)
- CI/CD pipelines (remote enforcement)
- Git pre-push hooks (network-aware)

---

### 1.5 File Naming Conventions

**Principle:** Use timestamp-prefixed filenames for chronological tracking.

**Universal Pattern:**
- **Format:** `YYYY-MM-DD-HHMM-description.{ext}`
- **Rationale:** Track chronological order when many files created in one day

**Apply To:**
- Session handoffs
- Research reports
- Architecture review documents
- Analysis outputs
- Meeting notes
- Design documents

**Examples Across Contexts:**
```
# Web Development
2025-10-26-1430-api-versioning-strategy.md
2025-10-26-0900-frontend-component-refactor.md

# Data Science
2025-10-26-1600-model-evaluation-report.md
2025-10-26-1030-data-quality-analysis.md

# DevOps
2025-10-26-1200-infrastructure-cost-analysis.md
2025-10-26-0800-incident-postmortem.md

# General Project Management
2025-10-26-1500-sprint-planning-notes.md
2025-10-26-1000-architecture-decision-record.md
```

**Header Timestamp Format:** Use `HH:MM:SS` for sections within documents
```markdown
## 14:30:00 — Authentication Implementation

Summary of work done at this time...

## 15:45:00 — Testing Strategy

New section added later in session...
```

---

## 2. Generic Context Types

**Principle:** Detect work context to load appropriate tools, patterns, and workflows.

### 2.1 Context Detection Algorithm

**Input Signals:**
1. Git branch name pattern
2. Current working directory
3. Active work items/issues
4. Recent file edits

**Output:** Context type + confidence score (HIGH/MEDIUM/LOW)

### 2.2 Proposed Universal Contexts

Replace domain-specific contexts (VENDOR/FRONTEND/API/TESTING) with:

#### Context 1: IMPLEMENTATION
**Definition:** Writing production code (business logic, algorithms, features)

**Detection Heuristics:**
- Branch patterns: `feat/*`, `feature/*`, `impl/*`
- Directories: `src/`, `lib/`, `app/`, `core/`
- File patterns: `*.py`, `*.js`, `*.go`, `*.rs`, `*.java`, etc. (source files)

**Workflow Emphasis:**
- Micro-commits every 20-50 lines
- Unit tests alongside implementation
- Code quality gates enforced
- Design pattern application

**Quality Gates:**
- Linter (language-specific)
- Type checker (if applicable)
- Unit tests (if TDD)

---

#### Context 2: TESTING
**Definition:** Writing tests, test infrastructure, quality assurance

**Detection Heuristics:**
- Branch patterns: `test/*`, `testing/*`, `qa/*`
- Directories: `tests/`, `test/`, `spec/`, `__tests__/`
- File patterns: `test_*.py`, `*.test.js`, `*_test.go`, `*.spec.ts`

**Workflow Emphasis:**
- Test coverage tracking
- Fixture/mock management
- Parameterized test patterns
- Integration test strategy

**Quality Gates:**
- Test linter (pytest-style, eslint-jest)
- Test execution (ensure tests pass)
- Coverage measurement (optional)

---

#### Context 3: INFRASTRUCTURE
**Definition:** DevOps, CI/CD, deployment, configuration, tooling

**Detection Heuristics:**
- Branch patterns: `infra/*`, `devops/*`, `deploy/*`, `ci/*`
- Directories: `.github/`, `terraform/`, `ansible/`, `k8s/`, `docker/`
- File patterns: `*.yml`, `*.yaml`, `Dockerfile`, `*.tf`, `*.sh`

**Workflow Emphasis:**
- Infrastructure as code patterns
- Security-first approach
- Rollback procedures
- Cost optimization

**Quality Gates:**
- YAML/config validation
- Terraform plan (if applicable)
- Security scanning (checkov, tfsec)
- Dry-run deployments

---

#### Context 4: DOCUMENTATION
**Definition:** Writing docs, guides, READMEs, API documentation

**Detection Heuristics:**
- Branch patterns: `docs/*`, `documentation/*`, `readme/*`
- Directories: `docs/`, `documentation/`, `wiki/`
- File patterns: `*.md`, `*.rst`, `*.adoc`, `*.tex`

**Workflow Emphasis:**
- Clear structure (headings, sections)
- Code examples (runnable)
- Timestamp tracking (for session notes)
- Cross-referencing

**Quality Gates:**
- Markdown linting (markdownlint)
- Spell checking (cspell, aspell)
- Link validation (markdown-link-check)
- Example code validation

---

#### Context 5: RESEARCH
**Definition:** Investigation, analysis, prototyping, exploration

**Detection Heuristics:**
- Branch patterns: `research/*`, `spike/*`, `prototype/*`, `explore/*`
- Directories: `research/`, `prototypes/`, `experiments/`, `notebooks/`
- File patterns: `*.ipynb`, `research-*.md`, `analysis-*.md`

**Workflow Emphasis:**
- Three-step research process
- Parallel investigation agents
- Documentation of findings
- Decision logging

**Quality Gates:**
- Research report completeness
- Findings documentation
- Decision rationale capture
- Prototype code quality (relaxed)

---

#### Context 6: BUGFIX
**Definition:** Debugging, fixing defects, addressing regressions

**Detection Heuristics:**
- Branch patterns: `fix/*`, `bugfix/*`, `hotfix/*`
- Issue/ticket references in branch name
- Directories: Any (cross-cutting)
- File patterns: Any modified files

**Workflow Emphasis:**
- Root cause analysis
- Minimal change principle
- Regression test addition
- Deployment verification

**Quality Gates:**
- Reproduction test (before fix)
- Fix verification (test passes)
- No new regressions (full suite)
- Performance impact check

---

### 2.3 Context Switching

**When to Switch:**
- Branch change
- Working directory change
- Explicit user intent
- Task completion

**How to Switch:**
1. Save current context (session handoff)
2. Detect new context (automatic)
3. Load new patterns/tools
4. Resume workflow

**Example:**
```bash
# Working in IMPLEMENTATION context
git checkout main
git checkout -b docs/api-documentation

# Context automatically switches to DOCUMENTATION
# Load documentation tools, templates, guidelines
```

---

## 3. Health Validation Checks

**Principle:** Validate system health before starting work to catch issues early.

### 3.1 Universal Health Categories

#### 1. Version Control Status
**Purpose:** Ensure clean git state before starting work

**Checks:**
```bash
git status --short --branch
# Verify: Clean working tree, correct branch, synced with remote
```

**Expected Output:**
- Branch name matches expected pattern
- No uncommitted changes (or known WIP)
- No unpushed commits (or intentional local work)
- No merge conflicts

**Red Flags:**
- Detached HEAD state
- Untracked files in critical directories
- Uncommitted changes from previous session

---

#### 2. Code Quality Tools
**Purpose:** Verify linters/formatters/type checkers are available

**Language-Specific Examples:**

**Python:**
```bash
ruff --version        # Linter/formatter
mypy --version        # Type checker
pytest --version      # Test runner
```

**JavaScript/TypeScript:**
```bash
npx eslint --version      # Linter
npx tsc --version         # Type checker
npx jest --version        # Test runner
```

**Go:**
```bash
golangci-lint --version   # Linter
go version                # Compiler
```

**Rust:**
```bash
cargo clippy --version    # Linter
cargo test --version      # Test runner
```

**Expected Output:**
- All tools installed and accessible
- Versions compatible with project requirements
- Configuration files present (`.eslintrc`, `pyproject.toml`, etc.)

---

#### 3. Project-Specific Tooling
**Purpose:** Verify domain-specific tools are available

**Examples:**

**Data Science:**
```bash
jupyter --version         # Notebook server
python -c "import pandas; print(pandas.__version__)"
python -c "import sklearn; print(sklearn.__version__)"
```

**Web Development:**
```bash
node --version           # Node runtime
npm --version            # Package manager
docker --version         # Containerization (if used)
```

**DevOps:**
```bash
terraform --version      # Infrastructure as code
kubectl version          # Kubernetes CLI
aws --version            # Cloud provider CLI
```

**Mobile Development:**
```bash
flutter --version        # Flutter SDK
xcrun simctl list        # iOS simulators (macOS)
adb devices              # Android devices
```

---

#### 4. Documentation Structure
**Purpose:** Verify project documentation exists and is organized

**Checks:**
```bash
# Core documentation files
test -f README.md          # Project overview
test -f CONTRIBUTING.md    # Contribution guidelines
test -f docs/architecture.md  # Architecture docs (if applicable)

# Session handoff directory
test -d session-handoffs/  # Handoff storage
ls -l session-handoffs/ | tail -5  # Recent handoffs
```

**Expected Structure:**
```
project-root/
├── README.md                    # Project overview
├── docs/
│   ├── architecture.md          # System design
│   ├── development.md           # Dev setup
│   └── deployment.md            # Deploy procedures
└── session-handoffs/            # Work continuity
    └── YYYY-MM-DD-HHMM-*.md
```

---

#### 5. Dependency Management
**Purpose:** Ensure dependencies are installed and up-to-date

**Language-Specific:**

**Python:**
```bash
pip list | grep {critical-package}
# Or with modern tools:
uv pip list | grep {critical-package}
```

**JavaScript/TypeScript:**
```bash
npm list --depth=0
# Check for vulnerabilities:
npm audit
```

**Go:**
```bash
go list -m all
# Check for updates:
go list -u -m all
```

**Rust:**
```bash
cargo tree
# Check for outdated deps:
cargo outdated
```

---

#### 6. Build System Verification
**Purpose:** Verify project builds successfully

**Examples:**

**Compiled Languages:**
```bash
# Go
go build ./...

# Rust
cargo build

# Java
./gradlew build

# C/C++
make
```

**Interpreted Languages (Linting as Build):**
```bash
# Python
ruff check . && mypy .

# JavaScript
npm run lint && npm run typecheck

# Ruby
rubocop
```

**Expected Output:**
- Build completes successfully
- No compilation errors
- No critical warnings

---

### 3.2 Health Check Output Format

**Template:**
```markdown
## System Health Check

**Timestamp:** YYYY-MM-DD HH:MM:SS

### Version Control
- ✅ Branch: {branch-name}
- ✅ Status: Clean working tree
- ✅ Sync: Up-to-date with remote

### Code Quality Tools
- ✅ Linter: {tool} v{version}
- ✅ Type Checker: {tool} v{version}
- ✅ Test Runner: {tool} v{version}

### Project Tooling
- ✅ {Tool 1}: Available
- ✅ {Tool 2}: Available
- ⚠️ {Tool 3}: Version mismatch (expected v2.x, found v1.9)

### Documentation
- ✅ README.md exists
- ✅ Session handoffs: 5 recent files found
- ⚠️ Architecture docs missing

### Dependencies
- ✅ All dependencies installed
- ⚠️ 3 outdated packages (non-critical)

### Build System
- ✅ Build successful (2.3s)
- ✅ No warnings

**Overall Status:** ✅ HEALTHY (2 warnings, non-blocking)
```

---

## 4. Pattern Examples Across Domains

### 4.1 Micro-Commits in Different Project Types

#### Web Development (React + TypeScript)
```typescript
// Commit 1: Component structure
export const Dashboard: React.FC = () => {
    const [data, setData] = useState<Data[]>([]);
    // 30-40 lines of component logic
    return <DashboardView data={data} />;
};
// COMMIT: "feat(ui): add Dashboard component structure"

// Commit 2: Data fetching
const useDashboardData = () => {
    // 25-35 lines of data fetching logic
    return { data, loading, error };
};
// COMMIT: "feat(ui): add Dashboard data fetching hook"

// Commit 3: Tests
describe('Dashboard', () => {
    it('renders without crashing', () => { /* ... */ });
    it('fetches data on mount', () => { /* ... */ });
    // 20-30 lines of tests
});
// COMMIT: "test(ui): add Dashboard component tests"
```

---

#### Data Science (Python + Pandas)
```python
# Commit 1: Data loading
def load_dataset(path: str) -> pd.DataFrame:
    """Load and validate raw dataset."""
    # 20-30 lines of loading/validation
    return df
# COMMIT: "feat(data): add dataset loading pipeline"

# Commit 2: Feature engineering
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived features."""
    # 40-50 lines of feature creation
    return df_features
# COMMIT: "feat(data): add feature engineering pipeline"

# Commit 3: Model training
def train_model(X_train, y_train) -> Model:
    """Train baseline model."""
    # 30-40 lines of model setup/training
    return model
# COMMIT: "feat(model): add baseline model training"
```

---

#### DevOps (Terraform + AWS)
```hcl
# Commit 1: VPC configuration
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
  # 15-20 lines of VPC setup
}
# COMMIT: "feat(infra): add VPC configuration"

# Commit 2: Security groups
resource "aws_security_group" "app" {
  name = "app-sg"
  # 25-30 lines of security rules
}
# COMMIT: "feat(infra): add application security group"

# Commit 3: Validation
terraform validate
terraform plan
# COMMIT: "chore(infra): validate infrastructure configuration"
```

---

### 4.2 Session Handoffs for Different Domains

#### Mobile Development (Flutter)
```markdown
# Session Handoff: User Authentication Screen

**Date:** 2025-10-26
**Time:** 16:00
**Context:** Flutter mobile app authentication flow
**Status:** 70% Complete

## Completed Work
- ✅ Login screen UI (email + password fields)
- ✅ Form validation logic (email format, password strength)
- ✅ Integration with authentication API
- ✅ Error handling and user feedback

## Next Priorities
1. Biometric authentication (fingerprint/face ID) - 3-4 hours
2. "Remember me" functionality - 1-2 hours
3. Password reset flow - 2-3 hours

## Context for Next Session
- Files: `lib/screens/auth/login_screen.dart`, `lib/services/auth_service.dart`
- Decision: Chose Provider for state management (over BLoC for simplicity)
- Branch: `feat/authentication-flow`
- Simulator: iPhone 14 Pro (iOS 17.0)
```

---

#### Machine Learning (PyTorch)
```markdown
# Session Handoff: Image Classification Model

**Date:** 2025-10-26
**Time:** 11:30
**Context:** ResNet50 fine-tuning for custom dataset
**Status:** Training in progress (epoch 15/50)

## Completed Work
- ✅ Dataset preprocessing (augmentation, normalization)
- ✅ Transfer learning setup (ResNet50 pretrained on ImageNet)
- ✅ Training pipeline with checkpointing
- ✅ TensorBoard logging configured

## Next Priorities
1. Monitor training completion (35 epochs remaining, ~6 hours)
2. Evaluate on validation set (1 hour)
3. Hyperparameter tuning if accuracy <90% (2-4 hours)

## Context for Next Session
- Checkpoint: `models/resnet50_epoch15.pth`
- Training logs: `runs/experiment_2025-10-26/`
- Decision: Learning rate 0.001 (reduced from 0.01 due to overfitting)
- GPU: NVIDIA RTX 3090 (24GB VRAM)
```

---

#### Game Development (Unity + C#)
```markdown
# Session Handoff: Enemy AI Behavior

**Date:** 2025-10-26
**Time:** 19:00
**Context:** Patrol and chase AI for enemy NPCs
**Status:** Patrol complete, chase in progress

## Completed Work
- ✅ Waypoint patrol system (4 waypoints, smooth navigation)
- ✅ Player detection (raycast-based vision cone)
- ✅ State machine setup (Idle, Patrol, Chase, Attack states)
- ✅ Animation integration (walk, run, idle)

## Next Priorities
1. Chase behavior (NavMesh pathfinding) - 2-3 hours
2. Attack state implementation - 2 hours
3. AI difficulty tuning (detection range, speed) - 1 hour

## Context for Next Session
- Files: `Scripts/AI/EnemyController.cs`, `Scripts/AI/StateMachine.cs`
- Scene: `Levels/Level01_TestArena`
- Decision: NavMesh over A* for performance (100+ enemies)
- Unity version: 2023.2.10f1
```

---

### 4.3 Quality Gates Across Languages

#### Python (Data Science)
```bash
# Code quality
ruff check .                  # Linting (fast)
black --check .               # Formatting (opinionated)

# Type safety
mypy src/                     # Static type checking

# Testing
pytest tests/ -v              # Unit + integration tests
pytest tests/ --cov=src/      # With coverage

# Notebook validation
jupyter nbconvert --to notebook --execute notebooks/*.ipynb

# Security
safety check                  # Dependency vulnerabilities
bandit -r src/                # Security issues in code
```

---

#### JavaScript/TypeScript (Full-Stack Web)
```bash
# Code quality
npm run lint                  # ESLint
npm run format:check          # Prettier

# Type safety
npm run typecheck             # TypeScript compiler

# Testing
npm run test                  # Jest unit tests
npm run test:e2e              # Playwright E2E tests

# Security
npm audit                     # Dependency vulnerabilities
npm run security:check        # Custom security checks

# Build verification
npm run build                 # Production build
```

---

#### Go (Backend API)
```bash
# Code quality
golangci-lint run             # Comprehensive linting
gofmt -s -w .                 # Standard formatting

# Testing
go test ./... -v              # All tests
go test ./... -race           # Race condition detection
go test ./... -cover          # Coverage reporting

# Security
gosec ./...                   # Security scanning

# Build verification
go build ./cmd/...            # Build all binaries
```

---

#### Rust (Systems Programming)
```bash
# Code quality
cargo clippy -- -D warnings   # Linting (strict)
cargo fmt --check             # Formatting

# Testing
cargo test                    # Unit tests
cargo test --release          # Optimized tests (performance)

# Security
cargo audit                   # Dependency vulnerabilities

# Build verification
cargo build --release         # Release build
cargo bench                   # Benchmarks (optional)
```

---

## 5. Implementation Guide

### 5.1 Adopting These Patterns

**Step 1: Choose Applicable Patterns** (Week 1)
- Review all 5 core principles
- Select 2-3 that address current pain points
- Document selected patterns in project README

**Step 2: Set Up Infrastructure** (Week 1-2)
- Configure quality gates (linters, type checkers)
- Create session handoff template
- Set up session-handoffs/ directory
- Configure git hooks (optional)

**Step 3: Pilot with Team** (Week 2-4)
- Introduce micro-commits on one feature branch
- Try session handoffs for one sprint
- Run parallel tasks on one complex feature
- Gather feedback

**Step 4: Refine and Scale** (Month 2+)
- Adjust patterns based on feedback
- Automate quality gates in CI/CD
- Create team-specific context types
- Measure impact (time saved, work loss prevention)

---

### 5.2 Customization Points

**Micro-Commit Frequency:**
- Adjust target (≤30 min) based on:
  - Team experience (junior vs senior)
  - Work complexity (research vs routine)
  - Risk tolerance (prototype vs production)

**Context Types:**
- Add domain-specific contexts:
  - MOBILE (iOS/Android development)
  - DATA_PIPELINE (ETL, streaming)
  - SECURITY (penetration testing, audits)
- Remove unused contexts
- Merge similar contexts

**Quality Gates:**
- Relax for prototypes/research
- Enforce strictly for production code
- Add domain-specific checks:
  - Model accuracy thresholds (ML)
  - Performance benchmarks (systems programming)
  - Accessibility compliance (web)

---

### 5.3 Common Pitfalls

**Over-Parallelization:**
- ❌ Spawning 20+ parallel tasks (coordination overhead)
- ✅ Limit to 5-10 parallel tasks, queue remainder

**Micro-Commits Too Small:**
- ❌ Committing every 5 lines (git history noise)
- ✅ Target 20-50 lines OR logical milestone

**Session Handoffs Too Detailed:**
- ❌ 10-page session notes (nobody reads)
- ✅ 1-2 page executive summary with key context

**Quality Gates Too Strict:**
- ❌ 100% test coverage required (slows development)
- ✅ Focus on critical paths, 70-80% coverage goal

**Rigid Context Switching:**
- ❌ Forcing work into predefined contexts
- ✅ Adapt contexts to team's actual workflows

---

## 6. Success Metrics

### 6.1 Quantitative Metrics

**Workflow Efficiency:**
- Session startup time: Target 10-15 min (vs 30-40 min without handoffs)
- Parallel task speedup: 3-10x (vs sequential execution)
- Work loss reduction: 80-90% (via micro-commits)

**Code Quality:**
- Quality gate pass rate: >95% before commit
- Regression rate: <5% (via testing discipline)
- Technical debt: Decreasing trend (via continuous refactoring)

**Team Velocity:**
- Sprint completion rate: +10-20% (via reduced context switching)
- Defect escape rate: -30-50% (via quality gates)

---

### 6.2 Qualitative Indicators

**Positive Signs:**
- Developers autonomously use session handoffs
- Quality gates seen as helpful (not blocking)
- Parallel task orchestration becomes default approach
- Micro-commits feel natural (not forced)

**Warning Signs:**
- Session handoffs rarely updated (not providing value)
- Quality gates frequently bypassed (too strict or slow)
- Parallel tasks cause confusion (poor orchestration)
- Commits too large (discipline not adopted)

---

## 7. Conclusion

These universal workflow patterns emerged from production use but are designed for broad applicability. Core principles:

1. **Parallel Orchestration:** Decompose complex work for speed and clarity
2. **Micro-Commits:** Prevent work loss through frequent commits
3. **Session Handoffs:** Transfer context efficiently between work periods
4. **Quality Gates:** Enforce automated checks at every commit
5. **File Naming:** Use timestamps for chronological tracking

**Adoption Strategy:** Start with 2-3 patterns, pilot with one team/project, measure impact, refine, and scale.

**Customization:** Adjust frequencies, context types, and quality gates to match your team's domain, experience, and risk tolerance.

**Expected Impact:** 10-20% velocity improvement, 80-90% work loss reduction, 15-25 min faster session startups.

---

**Version:** 1.0.0
**Last Updated:** 2025-10-27
**Source:** commission-workflow-orchestrator skill (commission-processing-vendor-extractors project)
**License:** Public domain (adapt freely)
