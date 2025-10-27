# Parallel Orchestration Guide

**Category**: Workflow Orchestration
**Token Budget**: ~800 tokens

---

## Orchestration Philosophy

The main chat (user ↔ Claude) is the **orchestration layer**. All complex tasks should be delegated to parallel subagents for maximum efficiency.

**Core Principle**: Main chat orchestrates, subagents execute specialized work.

---

## When to Use Parallel Subagents

### ALWAYS consider parallel subagents for:

- **Multiple independent tasks** (research, analysis, implementation)
- **Simultaneous evaluations** (analyze multiple components/files/commands)
- **Documentation generation** (create multiple reports in parallel)
- **Code reviews** across multiple files or modules
- **Research requiring diverse expertise** (architecture, security, testing, performance)

### Example Triggers:

**Complexity Indicators**:
- Task requires analyzing 10+ files
- Multiple independent research questions
- Need domain expertise across different areas
- Work can be parallelized (no sequential dependencies)
- Estimated effort >30 minutes if done sequentially

---

## How to Orchestrate

### Model-Invoked Architecture

**Important**: Users request subagent delegation via natural language, not by calling functions directly.

**User Request Pattern**:
```
"Please use parallel subagents to analyze the vendor format,
review base patterns, and check security requirements."
```

**What Claude Does**:
1. Evaluates request complexity
2. Decides delegation is beneficial
3. Spawns appropriate subagents with isolated contexts
4. Each subagent executes independently
5. Synthesizes results when complete

### Orchestration Pattern:

1. **Decide** which subagents to launch and what tasks to assign
2. **Launch** all agents (Claude handles parallel execution internally)
3. **Wait** for completion (non-blocking)
4. **Synthesize** outputs into actionable next steps
5. **Communicate** results to user in concise summary

---

## Main Chat Responsibilities

### 1. Orchestrate
Decide which subagents to launch and what tasks to assign. Consider:
- Task independence (can run in parallel)
- Required expertise (specialized vs general)
- Estimated effort (overhead vs benefit)

### 2. Coordinate
Ensure subagents have:
- Clear, independent objectives
- Isolated contexts (no overlap)
- Well-defined deliverables

### 3. Synthesize
Combine subagent outputs:
- Identify common themes
- Resolve conflicts
- Create unified action plan

### 4. Communicate
Present results to user:
- High-level summary
- Key findings from each subagent
- Recommended next steps

---

## Main Chat Should NOT

❌ **Perform complex research directly** (delegate to research agents)
❌ **Read 10+ files sequentially** (use exploration/analysis agents)
❌ **Analyze multiple independent components** (spawn parallel analysis agents)
❌ **Generate comprehensive reports** (use documentation agents)

---

## Benefits of Parallel Orchestration

### 1. Speed
- **Parallelism**: N tasks in parallel vs N sequential = up to N× faster
- **Concurrency**: Claude Code supports up to 10 concurrent subagents
- **Queueing**: Additional tasks automatically queued and executed as slots free

### 2. Expertise
- Specialized agents bring domain knowledge
- Each agent focuses on specific expertise area
- Better quality outputs from focused contexts

### 3. Token Efficiency
- Subagents have isolated contexts (no cross-contamination)
- No token bloat in main chat
- Progressive disclosure enforced per agent

### 4. Clarity
- Main chat focuses on orchestration, not execution
- Clean separation of concerns
- Easier to track progress and debug

---

## Real-World Examples

### Example 1: Multi-Language Codebase Analysis

**Task**: Analyze codebase with Python backend + JavaScript frontend

**Orchestration**:
```
User: "Please use parallel subagents to analyze the Python
backend patterns and JavaScript frontend architecture."

Claude spawns:
- backend-analysis agent (Python expertise)
- frontend-analysis agent (JavaScript expertise)
```

**Result**:
- 2 agents complete in ~40 minutes (parallel)
- Sequential estimate: ~80 minutes
- Speedup: 2×

### Example 2: Documentation Review

**Task**: Review 15 documentation files for consistency

**Orchestration**:
```
User: "Please use parallel subagents to review all 15
documentation files for consistency and completeness."

Claude spawns:
- 10 concurrent doc-review agents (first batch)
- 5 queued agents (second batch)
```

**Result**:
- 10 concurrent + 5 queued = ~30 minutes total
- Sequential estimate: ~150 minutes
- Speedup: 5×

### Example 3: Security Audit

**Task**: Audit application for security vulnerabilities

**Orchestration**:
```
User: "Please use parallel subagents to audit authentication,
API security, data validation, and deployment security."

Claude spawns:
- auth-security agent
- api-security agent
- validation-security agent
- deployment-security agent
```

**Result**:
- 4 agents complete in ~45 minutes (parallel)
- Sequential estimate: ~180 minutes
- Speedup: 4×

---

## Parallelism Reality

**Concurrent Execution**: Claude Code supports up to **10 concurrent task executions**.

**Queueing**: If more than 10 subagents are requested, additional tasks are automatically queued and executed as slots become available.

**Transparency**: Queueing is handled transparently—just request the work you need.

**Example**:
```
Request 15 parallel subagents:
- First batch: 10 agents execute concurrently
- Second batch: 5 agents queued, execute when slots free
```

---

## Anti-Patterns (NEVER)

❌ **Sequential subagent execution** (defeats parallelism benefits)
❌ **Main chat doing specialized work** (lose expertise benefits)
❌ **Launching subagents for trivial tasks** (overhead not justified)
❌ **Too many subagents without justification** (>10 = coordination overhead)
❌ **Overlapping contexts** (duplicate work across agents)

---

## Summary

**Philosophy**: Main chat orchestrates, subagents execute

**When**: Complex tasks, multiple independent objectives, diverse expertise needed

**How**: Request delegation via natural language, Claude handles parallel execution

**Benefits**: Up to N× speedup, expertise, token efficiency, clarity

**Key Insight**: Parallel orchestration maximizes efficiency for complex multi-faceted work.
