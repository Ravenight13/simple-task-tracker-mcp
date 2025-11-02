# Implementation Plan: Workspace Audit Endpoint (Strategy 2)

**Date:** 2025-11-02
**Status:** Planning
**Complexity:** Medium
**Estimated Effort:** 6-8 hours

## Executive Summary

This plan outlines the implementation of `audit_workspace_integrity`, a new MCP tool that detects cross-workspace contamination in task-mcp databases. The tool will analyze tasks for file references, tags, and other indicators that don't belong to the current workspace, providing actionable reports to identify and fix data integrity issues.

## Problem Statement

Cross-workspace contamination occurs when:
1. Tasks in workspace A have `file_references` pointing to workspace B
2. Tasks contain tags indicating they belong to a different project
3. Multiple git repos are represented in a single workspace database
4. Task descriptions or metadata reference paths outside the workspace

This contamination can happen due to:
- Incorrect `TASK_MCP_WORKSPACE` environment variable
- Manual workspace_path parameter errors
- Copy-paste between Claude Code sessions
- Git repo changes without database cleanup

## Architecture Overview

### Tool Signature

```python
@mcp.tool()
def audit_workspace_integrity(
    workspace_path: str | None = None,
    include_deleted: bool = False,
    check_git_repo: bool = True,
) -> dict[str, Any]:
    """
    Audit workspace for cross-contamination and integrity issues.

    Args:
        workspace_path: Optional workspace path (auto-detected if not provided)
        include_deleted: Include soft-deleted tasks in audit (default: False)
        check_git_repo: Verify git repo consistency (default: True)

    Returns:
        Audit report with contamination findings and recommendations
    """
```

### Return Format

```python
{
    "workspace_path": "/absolute/path/to/workspace",
    "audit_timestamp": "2025-11-02T14:30:00",
    "total_tasks": 42,
    "total_entities": 15,
    "contamination_found": True,
    "issues": {
        "file_reference_mismatches": [
            {
                "task_id": 123,
                "task_title": "Fix auth bug",
                "file_references": ["/other/workspace/src/auth.py"],
                "expected_prefix": "/current/workspace",
                "severity": "high"
            }
        ],
        "suspicious_tags": [
            {
                "task_id": 456,
                "task_title": "Add feature X",
                "tags": "other-project vendor-integration",
                "reason": "Tag 'other-project' suggests different workspace",
                "severity": "medium"
            }
        ],
        "git_repo_mismatches": [
            {
                "task_id": 789,
                "task_title": "Update README",
                "file_references": ["/path/with/.git/at/different/location"],
                "current_git_root": "/current/workspace",
                "detected_git_root": "/path/with",
                "severity": "high"
            }
        ],
        "entity_identifier_mismatches": [
            {
                "entity_id": 5,
                "entity_type": "file",
                "name": "Login Controller",
                "identifier": "/other/workspace/src/login.py",
                "expected_prefix": "/current/workspace",
                "severity": "high"
            }
        ],
        "description_path_references": [
            {
                "task_id": 234,
                "task_title": "Refactor module",
                "description_excerpt": "...see /other/workspace/docs/design.md...",
                "detected_paths": ["/other/workspace/docs/design.md"],
                "severity": "low"
            }
        ]
    },
    "statistics": {
        "contaminated_tasks": 3,
        "contaminated_entities": 1,
        "contamination_percentage": 7.1,
        "high_severity_issues": 4,
        "medium_severity_issues": 1,
        "low_severity_issues": 1
    },
    "recommendations": [
        "Move 3 tasks to correct workspace database",
        "Update 1 entity identifier to match workspace",
        "Review tags for 1 task - may indicate wrong workspace",
        "Consider running cleanup_workspace_contamination tool"
    ],
    "git_info": {
        "git_repo_detected": True,
        "git_root": "/current/workspace",
        "git_remote": "git@github.com:user/repo.git",
        "is_workspace_git_root": True
    }
}
```

## Implementation Details

### File Changes Required

#### 1. `/Users/cliffclarke/Claude_Code/task-mcp/src/task_mcp/server.py`

**Add new tool function** (insert after `cleanup_deleted_tasks`, before entity tools):

```python
@mcp.tool()
def audit_workspace_integrity(
    workspace_path: str | None = None,
    include_deleted: bool = False,
    check_git_repo: bool = True,
) -> dict[str, Any]:
    """
    Audit workspace for cross-contamination and integrity issues.

    Detects:
    1. Tasks with file_references pointing outside workspace
    2. Entities with identifiers pointing outside workspace
    3. Tasks with tags suggesting different projects
    4. Git repo inconsistencies
    5. Description text referencing external paths

    Args:
        workspace_path: Optional workspace path (auto-detected if not provided)
        include_deleted: Include soft-deleted tasks in audit (default: False)
        check_git_repo: Verify git repo consistency (default: True)

    Returns:
        Comprehensive audit report with findings and recommendations
    """
    from .audit import perform_workspace_audit
    from .master import register_project
    from .utils import resolve_workspace

    # Auto-register project and update last_accessed
    workspace = resolve_workspace(workspace_path)
    register_project(workspace)

    # Delegate to audit module
    return perform_workspace_audit(
        workspace_path=workspace,
        include_deleted=include_deleted,
        check_git_repo=check_git_repo,
    )
```

#### 2. `/Users/cliffclarke/Claude_Code/task-mcp/src/task_mcp/audit.py` (NEW FILE)

**Create new audit module** with comprehensive validation logic:

```python
"""Workspace integrity audit functions for detecting cross-contamination."""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .database import get_connection


def perform_workspace_audit(
    workspace_path: str,
    include_deleted: bool = False,
    check_git_repo: bool = True,
) -> dict[str, Any]:
    """
    Main audit function orchestrating all validation checks.

    Args:
        workspace_path: Absolute workspace path
        include_deleted: Include soft-deleted items
        check_git_repo: Check git repository consistency

    Returns:
        Audit report dictionary
    """
    conn = get_connection(workspace_path)
    cursor = conn.cursor()

    try:
        # Initialize report structure
        report = {
            "workspace_path": workspace_path,
            "audit_timestamp": datetime.now().isoformat(),
            "contamination_found": False,
            "issues": {
                "file_reference_mismatches": [],
                "suspicious_tags": [],
                "git_repo_mismatches": [],
                "entity_identifier_mismatches": [],
                "description_path_references": [],
            },
            "statistics": {
                "contaminated_tasks": 0,
                "contaminated_entities": 0,
            },
            "recommendations": [],
        }

        # Get all tasks
        deleted_filter = "" if include_deleted else "WHERE deleted_at IS NULL"
        cursor.execute(f"SELECT * FROM tasks {deleted_filter}")
        tasks = [dict(row) for row in cursor.fetchall()]
        report["total_tasks"] = len(tasks)

        # Get all entities
        cursor.execute(f"SELECT * FROM entities {deleted_filter}")
        entities = [dict(row) for row in cursor.fetchall()]
        report["total_entities"] = len(entities)

        # Check 1: File references
        _check_file_references(tasks, workspace_path, report)

        # Check 2: Suspicious tags
        _check_suspicious_tags(tasks, workspace_path, report)

        # Check 3: Description path references
        _check_description_paths(tasks, workspace_path, report)

        # Check 4: Entity identifiers
        _check_entity_identifiers(entities, workspace_path, report)

        # Check 5: Git repository consistency (optional)
        if check_git_repo:
            git_info = _check_git_consistency(tasks, entities, workspace_path, report)
            report["git_info"] = git_info

        # Calculate statistics
        _calculate_statistics(report)

        # Generate recommendations
        _generate_recommendations(report)

        # Set contamination_found flag
        report["contamination_found"] = any(
            len(issues) > 0 for issues in report["issues"].values()
        )

        return report

    finally:
        conn.close()


def _check_file_references(
    tasks: list[dict[str, Any]],
    workspace_path: str,
    report: dict[str, Any],
) -> None:
    """Check if task file_references point outside workspace."""
    workspace_prefix = Path(workspace_path).resolve()

    for task in tasks:
        if not task.get("file_references"):
            continue

        try:
            file_refs = json.loads(task["file_references"])
        except json.JSONDecodeError:
            continue

        mismatched_refs = []
        for ref in file_refs:
            ref_path = Path(ref).resolve()

            # Check if path is outside workspace
            if not _is_path_within(ref_path, workspace_prefix):
                mismatched_refs.append(ref)

        if mismatched_refs:
            report["issues"]["file_reference_mismatches"].append({
                "task_id": task["id"],
                "task_title": task["title"],
                "file_references": mismatched_refs,
                "expected_prefix": str(workspace_prefix),
                "severity": "high",
            })


def _check_suspicious_tags(
    tasks: list[dict[str, Any]],
    workspace_path: str,
    report: dict[str, Any],
) -> None:
    """Check for tags that suggest different projects."""
    # Common suspicious tag patterns
    suspicious_patterns = [
        r"\b(other-project|another-workspace|different-repo)\b",
        r"\b\w+-mcp\b(?<!task-mcp)",  # Other MCP projects
        r"\btask-viewer\b",  # Known separate project
    ]

    for task in tasks:
        if not task.get("tags"):
            continue

        tags = task["tags"].lower()
        reasons = []

        for pattern in suspicious_patterns:
            if re.search(pattern, tags):
                reasons.append(f"Pattern '{pattern}' suggests different workspace")

        if reasons:
            report["issues"]["suspicious_tags"].append({
                "task_id": task["id"],
                "task_title": task["title"],
                "tags": tags,
                "reason": "; ".join(reasons),
                "severity": "medium",
            })


def _check_description_paths(
    tasks: list[dict[str, Any]],
    workspace_path: str,
    report: dict[str, Any],
) -> None:
    """Check task descriptions for absolute paths outside workspace."""
    workspace_prefix = Path(workspace_path).resolve()

    # Regex to find absolute paths (Unix and Windows)
    path_pattern = r"(?:/[\w\-./]+|[A-Z]:\\[\w\-\\./]+)"

    for task in tasks:
        if not task.get("description"):
            continue

        matches = re.findall(path_pattern, task["description"])
        external_paths = []

        for match in matches:
            try:
                path = Path(match).resolve()
                if not _is_path_within(path, workspace_prefix):
                    external_paths.append(match)
            except Exception:
                # Invalid path, skip
                continue

        if external_paths:
            # Create excerpt around first external path
            first_path = external_paths[0]
            idx = task["description"].index(first_path)
            start = max(0, idx - 20)
            end = min(len(task["description"]), idx + len(first_path) + 20)
            excerpt = task["description"][start:end]

            report["issues"]["description_path_references"].append({
                "task_id": task["id"],
                "task_title": task["title"],
                "description_excerpt": f"...{excerpt}...",
                "detected_paths": external_paths,
                "severity": "low",
            })


def _check_entity_identifiers(
    entities: list[dict[str, Any]],
    workspace_path: str,
    report: dict[str, Any],
) -> None:
    """Check if entity identifiers (especially file type) point outside workspace."""
    workspace_prefix = Path(workspace_path).resolve()

    for entity in entities:
        # Only check file entities and entities with path-like identifiers
        if not entity.get("identifier"):
            continue

        identifier = entity["identifier"]

        # Check if identifier looks like a path (starts with / or contains /)
        if "/" not in identifier and not identifier.startswith("/"):
            continue

        try:
            id_path = Path(identifier).resolve()

            # Check if path is outside workspace
            if not _is_path_within(id_path, workspace_prefix):
                report["issues"]["entity_identifier_mismatches"].append({
                    "entity_id": entity["id"],
                    "entity_type": entity["entity_type"],
                    "name": entity["name"],
                    "identifier": identifier,
                    "expected_prefix": str(workspace_prefix),
                    "severity": "high",
                })
        except Exception:
            # Invalid path, skip
            continue


def _check_git_consistency(
    tasks: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    workspace_path: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Check git repository consistency for the workspace."""
    git_info = {
        "git_repo_detected": False,
        "git_root": None,
        "git_remote": None,
        "is_workspace_git_root": False,
    }

    # Find git root for workspace
    workspace_git_root = _find_git_root(workspace_path)

    if workspace_git_root:
        git_info["git_repo_detected"] = True
        git_info["git_root"] = workspace_git_root
        git_info["is_workspace_git_root"] = (
            Path(workspace_git_root).resolve() == Path(workspace_path).resolve()
        )

        # Get remote URL
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=workspace_git_root,
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                git_info["git_remote"] = result.stdout.strip()
        except Exception:
            pass

    # Check if file references point to different git repos
    all_paths = []

    # Collect paths from tasks
    for task in tasks:
        if task.get("file_references"):
            try:
                file_refs = json.loads(task["file_references"])
                all_paths.extend([(task, ref) for ref in file_refs])
            except json.JSONDecodeError:
                pass

    # Collect paths from entities
    entity_paths = []
    for entity in entities:
        if entity.get("identifier") and "/" in entity["identifier"]:
            entity_paths.append((entity, entity["identifier"]))

    # Check each path's git root
    seen_mismatches = set()

    for task, path in all_paths:
        path_git_root = _find_git_root(path)

        if path_git_root and workspace_git_root:
            if Path(path_git_root).resolve() != Path(workspace_git_root).resolve():
                key = (task["id"], path_git_root)
                if key not in seen_mismatches:
                    seen_mismatches.add(key)
                    report["issues"]["git_repo_mismatches"].append({
                        "task_id": task["id"],
                        "task_title": task["title"],
                        "file_references": [path],
                        "current_git_root": workspace_git_root,
                        "detected_git_root": path_git_root,
                        "severity": "high",
                    })

    return git_info


def _is_path_within(child: Path, parent: Path) -> bool:
    """Check if child path is within parent path."""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _find_git_root(path: str) -> str | None:
    """Find git repository root for given path."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return None


def _calculate_statistics(report: dict[str, Any]) -> None:
    """Calculate statistics from audit findings."""
    contaminated_task_ids = set()
    contaminated_entity_ids = set()
    severity_counts = {"high": 0, "medium": 0, "low": 0}

    # Count unique contaminated tasks
    for issue_type, issues in report["issues"].items():
        for issue in issues:
            if "task_id" in issue:
                contaminated_task_ids.add(issue["task_id"])
            if "entity_id" in issue:
                contaminated_entity_ids.add(issue["entity_id"])

            # Count severities
            severity = issue.get("severity", "low")
            severity_counts[severity] += 1

    report["statistics"]["contaminated_tasks"] = len(contaminated_task_ids)
    report["statistics"]["contaminated_entities"] = len(contaminated_entity_ids)

    # Calculate percentage
    total_items = report["total_tasks"] + report["total_entities"]
    if total_items > 0:
        contaminated_total = len(contaminated_task_ids) + len(contaminated_entity_ids)
        report["statistics"]["contamination_percentage"] = round(
            (contaminated_total / total_items) * 100, 1
        )
    else:
        report["statistics"]["contamination_percentage"] = 0.0

    report["statistics"]["high_severity_issues"] = severity_counts["high"]
    report["statistics"]["medium_severity_issues"] = severity_counts["medium"]
    report["statistics"]["low_severity_issues"] = severity_counts["low"]


def _generate_recommendations(report: dict[str, Any]) -> None:
    """Generate actionable recommendations based on findings."""
    recommendations = []

    # File reference mismatches
    file_ref_count = len(report["issues"]["file_reference_mismatches"])
    if file_ref_count > 0:
        recommendations.append(
            f"Move {file_ref_count} task(s) to correct workspace database"
        )

    # Entity identifier mismatches
    entity_count = len(report["issues"]["entity_identifier_mismatches"])
    if entity_count > 0:
        recommendations.append(
            f"Update {entity_count} entity identifier(s) to match workspace"
        )

    # Suspicious tags
    tag_count = len(report["issues"]["suspicious_tags"])
    if tag_count > 0:
        recommendations.append(
            f"Review tags for {tag_count} task(s) - may indicate wrong workspace"
        )

    # Git mismatches
    git_count = len(report["issues"]["git_repo_mismatches"])
    if git_count > 0:
        recommendations.append(
            f"Investigate {git_count} task(s) with file references to different git repos"
        )

    # Description paths
    desc_count = len(report["issues"]["description_path_references"])
    if desc_count > 0:
        recommendations.append(
            f"Review descriptions for {desc_count} task(s) with external path references"
        )

    # General cleanup recommendation
    if any(len(issues) > 0 for issues in report["issues"].values()):
        recommendations.append(
            "Consider creating cleanup tasks to resolve contamination issues"
        )
    else:
        recommendations.append(
            "No contamination detected - workspace integrity is good!"
        )

    report["recommendations"] = recommendations
```

#### 3. `/Users/cliffclarke/Claude_Code/task-mcp/tests/test_audit.py` (NEW FILE)

**Create comprehensive test suite:**

```python
"""Tests for workspace integrity audit functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from task_mcp.audit import (
    _check_description_paths,
    _check_entity_identifiers,
    _check_file_references,
    _check_git_consistency,
    _check_suspicious_tags,
    _is_path_within,
    perform_workspace_audit,
)
from task_mcp.database import get_connection


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def setup_test_db(temp_workspace):
    """Setup test database with sample tasks and entities."""
    conn = get_connection(temp_workspace)
    cursor = conn.cursor()

    # Insert test task with file references
    cursor.execute(
        """
        INSERT INTO tasks (
            title, description, file_references, tags, created_at, updated_at
        ) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        (
            "Test task",
            "See /other/workspace/file.py for details",
            json.dumps([f"{temp_workspace}/file1.py", "/other/workspace/file2.py"]),
            "test other-project",
        )
    )

    # Insert entity with identifier
    cursor.execute(
        """
        INSERT INTO entities (
            entity_type, name, identifier, created_at, updated_at
        ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """,
        ("file", "Test File", "/other/workspace/src/test.py")
    )

    conn.commit()
    conn.close()

    return temp_workspace


def test_is_path_within():
    """Test path containment check."""
    parent = Path("/home/user/project")
    child = Path("/home/user/project/src/file.py")
    other = Path("/home/user/other/file.py")

    assert _is_path_within(child, parent) is True
    assert _is_path_within(other, parent) is False


def test_check_file_references(setup_test_db):
    """Test file reference validation."""
    conn = get_connection(setup_test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")
    tasks = [dict(row) for row in cursor.fetchall()]

    report = {"issues": {"file_reference_mismatches": []}}
    _check_file_references(tasks, setup_test_db, report)

    assert len(report["issues"]["file_reference_mismatches"]) == 1
    assert "/other/workspace/file2.py" in report["issues"]["file_reference_mismatches"][0]["file_references"]

    conn.close()


def test_check_suspicious_tags(setup_test_db):
    """Test suspicious tag detection."""
    conn = get_connection(setup_test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")
    tasks = [dict(row) for row in cursor.fetchall()]

    report = {"issues": {"suspicious_tags": []}}
    _check_suspicious_tags(tasks, setup_test_db, report)

    assert len(report["issues"]["suspicious_tags"]) == 1
    assert "other-project" in report["issues"]["suspicious_tags"][0]["tags"]

    conn.close()


def test_check_description_paths(setup_test_db):
    """Test description path detection."""
    conn = get_connection(setup_test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")
    tasks = [dict(row) for row in cursor.fetchall()]

    report = {"issues": {"description_path_references": []}}
    _check_description_paths(tasks, setup_test_db, report)

    assert len(report["issues"]["description_path_references"]) == 1
    assert "/other/workspace/file.py" in report["issues"]["description_path_references"][0]["detected_paths"]

    conn.close()


def test_check_entity_identifiers(setup_test_db):
    """Test entity identifier validation."""
    conn = get_connection(setup_test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM entities")
    entities = [dict(row) for row in cursor.fetchall()]

    report = {"issues": {"entity_identifier_mismatches": []}}
    _check_entity_identifiers(entities, setup_test_db, report)

    assert len(report["issues"]["entity_identifier_mismatches"]) == 1
    assert report["issues"]["entity_identifier_mismatches"][0]["identifier"] == "/other/workspace/src/test.py"

    conn.close()


def test_full_audit(setup_test_db):
    """Test complete audit workflow."""
    report = perform_workspace_audit(
        workspace_path=setup_test_db,
        include_deleted=False,
        check_git_repo=False,  # Skip git checks in test
    )

    # Verify report structure
    assert "workspace_path" in report
    assert "audit_timestamp" in report
    assert "contamination_found" in report
    assert "issues" in report
    assert "statistics" in report
    assert "recommendations" in report

    # Verify contamination detected
    assert report["contamination_found"] is True

    # Verify statistics calculated
    assert report["statistics"]["contaminated_tasks"] >= 1
    assert report["statistics"]["contaminated_entities"] >= 1
    assert report["statistics"]["contamination_percentage"] > 0

    # Verify recommendations generated
    assert len(report["recommendations"]) > 0
```

## Validation Checks

The audit endpoint will perform the following checks:

### 1. File Reference Validation (High Priority)
- **Check:** Parse `file_references` JSON arrays
- **Logic:** Compare each path against workspace prefix
- **Detection:** Path doesn't start with workspace root
- **Severity:** HIGH - Strong indicator of wrong workspace

### 2. Suspicious Tag Detection (Medium Priority)
- **Check:** Scan tags for project-specific patterns
- **Patterns:**
  - `other-project`, `another-workspace`
  - Other MCP projects (e.g., `workflow-mcp`)
  - Known separate projects (e.g., `task-viewer`)
- **Severity:** MEDIUM - May indicate wrong workspace or multi-project tags

### 3. Git Repository Consistency (High Priority)
- **Check:** Find git root for workspace
- **Logic:** Compare file reference paths' git roots
- **Detection:** Different git repos referenced
- **Severity:** HIGH - File from different repo suggests contamination

### 4. Entity Identifier Validation (High Priority)
- **Check:** Validate file-type entity identifiers
- **Logic:** Compare identifier paths against workspace
- **Detection:** Path outside workspace
- **Severity:** HIGH - Entity belongs to different workspace

### 5. Description Path References (Low Priority)
- **Check:** Regex scan for absolute paths in descriptions
- **Logic:** Extract paths and validate against workspace
- **Detection:** External path references
- **Severity:** LOW - May be documentation links, not actual contamination

## Testing Strategy

### Unit Tests
- Test each validation function independently
- Mock database connections and git operations
- Verify edge cases (empty paths, malformed JSON, etc.)

### Integration Tests
- Create contaminated test database
- Run full audit and verify all issues detected
- Test with real workspace structure
- Verify recommendations generated correctly

### Performance Tests
- Test with large databases (1000+ tasks)
- Ensure audit completes within reasonable time (< 5 seconds)
- Profile for optimization opportunities

## Edge Cases

1. **Relative Paths:** Convert to absolute before comparison
2. **Symlinks:** Resolve to real paths using `Path.resolve()`
3. **Windows Paths:** Handle both Unix and Windows path formats
4. **Malformed JSON:** Gracefully skip invalid file_references
5. **Missing Git:** Handle subprocess errors if git not installed
6. **Empty Workspace:** Report zero contamination correctly
7. **Nested Git Repos:** Handle submodules and nested repos

## Error Handling

- Database connection failures: Return error in report
- Git command failures: Set `check_git_repo` result to null
- Invalid paths: Log warning and skip validation
- JSON parsing errors: Skip malformed data, log issue count
- Subprocess timeouts: Set 2-second timeout for git operations

## Performance Considerations

- **Database Queries:** Single query per table (tasks, entities)
- **Path Operations:** Cache workspace prefix resolution
- **Git Operations:** Only check unique git roots (deduplicate)
- **Regex Matching:** Compile patterns once, reuse for all tasks
- **Memory Usage:** Stream results for large databases (use generators if >10k tasks)

## Future Enhancements

### Phase 2 Features (Not in Initial Implementation)
1. **Automatic Cleanup:** `cleanup_workspace_contamination(report)` tool
2. **Workspace Migration:** Move tasks between databases
3. **Pattern Learning:** Detect workspace-specific tag patterns
4. **Historical Tracking:** Store audit results for trend analysis
5. **Integration Points:** Auto-run audit on project access
6. **Severity Tuning:** Configurable severity thresholds

## Rollout Plan

### Phase 1: Core Implementation (This PR)
1. Create `audit.py` module with all validation checks
2. Add `audit_workspace_integrity` tool to `server.py`
3. Implement comprehensive test suite
4. Document in README and CLAUDE.md

### Phase 2: Production Hardening
1. Performance testing with large databases
2. Edge case handling refinement
3. User feedback integration
4. Documentation improvements

### Phase 3: Cleanup Automation
1. Design cleanup strategy
2. Implement migration tools
3. Add safety confirmations

## Success Criteria

1. Tool successfully detects all 5 types of contamination
2. Test coverage > 90% for audit module
3. No false positives in clean workspace audit
4. Audit completes in < 5 seconds for typical workspace (< 100 tasks)
5. Report format is actionable and user-friendly
6. Git operations handle missing/invalid repos gracefully

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| False positives from valid multi-repo projects | Medium | Document expected behavior, add severity levels |
| Performance issues with large databases | Low | Implement query optimization, lazy evaluation |
| Git subprocess hangs | Low | Add 2-second timeout to all git operations |
| Path resolution errors on Windows | Medium | Test on Windows, handle both path formats |
| Breaking changes to existing tools | Very Low | Audit is read-only, no data modification |

## Dependencies

- **No new external dependencies required**
- Uses existing modules: `database`, `utils`, `master`
- Standard library: `subprocess`, `pathlib`, `re`, `json`
- Git CLI (optional, graceful degradation if missing)

## Timeline Estimate

- **Audit module implementation:** 3-4 hours
- **Server.py integration:** 30 minutes
- **Test suite development:** 2-3 hours
- **Documentation updates:** 30 minutes
- **Testing and refinement:** 1-2 hours

**Total:** 6-8 hours for complete implementation

## Appendix: Example Usage

```python
# Basic audit
report = audit_workspace_integrity()

# Audit including deleted tasks
report = audit_workspace_integrity(include_deleted=True)

# Audit without git checks (faster)
report = audit_workspace_integrity(check_git_repo=False)

# Explicit workspace
report = audit_workspace_integrity(workspace_path="/path/to/project")

# Access report data
if report["contamination_found"]:
    print(f"Found {report['statistics']['contaminated_tasks']} contaminated tasks")

    for issue in report["issues"]["file_reference_mismatches"]:
        print(f"Task {issue['task_id']}: {issue['task_title']}")
        print(f"  Bad refs: {issue['file_references']}")

    for rec in report["recommendations"]:
        print(f"- {rec}")
```

---

**End of Implementation Plan**
