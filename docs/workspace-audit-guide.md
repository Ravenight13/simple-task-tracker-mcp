# Workspace Audit and Validation Guide

## Overview

Task MCP v0.4.0 introduces workspace metadata tracking and audit tools to prevent cross-project contamination. This guide explains how to use these features to maintain clean, project-specific task databases.

## Quick Start

### Check if a task belongs to your project
```python
# Validate single task
result = validate_task_workspace(task_id=42)
if not result["valid"]:
    print(f"Warning: Task from {result['task_workspace']}")
```

### Run a full workspace audit
```python
# Basic audit
audit = audit_workspace_integrity()
if audit["contamination_found"]:
    print(f"Found {audit['statistics']['contaminated_tasks']} contaminated tasks")
    print("Recommendations:", audit["recommendations"])
```

## Understanding Workspace Metadata

Every new task automatically captures:
- **workspace_path**: Where the task was created
- **git_root**: Git repository root (if applicable)
- **cwd_at_creation**: Working directory at creation time
- **project_name**: Derived from workspace directory

This metadata enables:
- Detection of tasks created in wrong projects
- Validation after workspace migrations
- Audit trails for debugging

## Using validate_task_workspace

### Basic Usage
```python
result = validate_task_workspace(task_id=123)
```

### Understanding the Response
```python
{
    "valid": True,           # False if task from different workspace
    "task_id": 123,
    "current_workspace": "/Users/you/project-a",
    "task_workspace": "/Users/you/project-a",    # Where task was created
    "workspace_match": True,
    "warnings": [],          # Any issues detected
    "metadata": {            # Full workspace context
        "workspace_path": "/Users/you/project-a",
        "git_root": "/Users/you/project-a",
        "cwd_at_creation": "/Users/you/project-a/src",
        "project_name": "project-a"
    }
}
```

### Common Scenarios

#### Scenario 1: Task from Different Project
```python
result = validate_task_workspace(task_id=456)
# result["valid"] = False
# result["warnings"] = [
#     "Task created in different workspace: /Users/you/project-b",
#     "Current workspace: /Users/you/project-a",
#     "This task may not be relevant to current project"
# ]
```

#### Scenario 2: Legacy Task (No Metadata)
```python
result = validate_task_workspace(task_id=10)
# result["valid"] = True (assumed valid)
# result["warnings"] = ["Task created before workspace metadata tracking (legacy task)"]
```

## Using audit_workspace_integrity

### Basic Audit
```python
# Run standard audit
audit = audit_workspace_integrity()
```

### Advanced Options
```python
# Include deleted tasks/entities
audit = audit_workspace_integrity(include_deleted=True)

# Skip git checks (faster)
audit = audit_workspace_integrity(check_git_repo=False)

# Specify workspace explicitly
audit = audit_workspace_integrity(workspace_path="/path/to/project")
```

### Understanding Audit Results

The audit returns a comprehensive report:

```python
{
    "workspace_path": "/Users/you/project",
    "audit_timestamp": "2025-11-02T10:30:00",
    "contamination_found": False,
    "issues": {
        # File references pointing outside workspace
        "file_reference_mismatches": [],

        # Tags containing other project names
        "suspicious_tags": [],

        # Tasks from different git repositories
        "git_repo_mismatches": [],

        # File entities with external paths
        "entity_identifier_mismatches": [],

        # Absolute paths in descriptions
        "description_path_references": []
    },
    "statistics": {
        "contaminated_tasks": 0,
        "contaminated_entities": 0
    },
    "recommendations": []
}
```

### Interpreting Issues

#### file_reference_mismatches
Tasks with file references outside the workspace:
```python
"file_reference_mismatches": [
    {
        "task_id": 42,
        "title": "Fix authentication bug",
        "file_references": ["/Users/you/other-project/auth.py"],
        "reason": "File reference outside workspace"
    }
]
```

#### suspicious_tags
Tags containing other project names:
```python
"suspicious_tags": [
    {
        "task_id": 55,
        "title": "Update API endpoints",
        "tags": "api backend project-xyz",
        "reason": "Tag 'project-xyz' may indicate wrong project"
    }
]
```

#### git_repo_mismatches
Tasks from different git repositories:
```python
"git_repo_mismatches": [
    {
        "task_id": 78,
        "title": "Refactor database layer",
        "task_git_root": "/Users/you/old-repo",
        "current_git_root": "/Users/you/new-repo",
        "reason": "Task from different git repository"
    }
]
```

## Best Practices

### 1. Regular Audits
```python
# Weekly health check
def weekly_audit():
    audit = audit_workspace_integrity()
    if audit["contamination_found"]:
        send_notification(
            f"Workspace contamination detected: "
            f"{audit['statistics']['contaminated_tasks']} tasks affected"
        )
```

### 2. Pre-Work Validation
```python
# Before working on a task
def start_work_on_task(task_id):
    # Validate workspace first
    validation = validate_task_workspace(task_id)
    if not validation["valid"]:
        if confirm("Task from different project. Continue anyway?"):
            log_warning(f"Working on cross-project task {task_id}")
        else:
            raise ValueError("Cannot work on task from different project")

    # Proceed with work
    update_task(task_id, status="in_progress")
```

### 3. Post-Migration Validation
```python
# After moving/forking a project
def validate_after_migration():
    audit = audit_workspace_integrity(check_git_repo=True)

    # Handle git mismatches
    for issue in audit["issues"]["git_repo_mismatches"]:
        task_id = issue["task_id"]
        print(f"Task {task_id} needs attention: {issue['reason']}")
        # Optionally update or delete
```

### 4. Bulk Import Validation
```python
# After importing tasks from another source
def validate_import(imported_task_ids):
    contaminated = []
    for task_id in imported_task_ids:
        result = validate_task_workspace(task_id)
        if not result["valid"]:
            contaminated.append(task_id)

    if contaminated:
        print(f"Warning: {len(contaminated)} imported tasks from other workspaces")
        # Consider soft-deleting or re-categorizing
```

## Troubleshooting

### Problem: Many False Positives
**Cause**: Workspace path has changed (moved/renamed project)
**Solution**: Tasks retain original workspace metadata. This is expected behavior. Consider if tasks are still relevant.

### Problem: Audit Takes Too Long
**Solution**: Skip git checks if not needed:
```python
audit = audit_workspace_integrity(check_git_repo=False)
```

### Problem: Legacy Tasks Show as Invalid
**Cause**: Tasks created before v0.4.0 have no metadata
**Solution**: These are assumed valid. The warning is informational only.

## Cleanup Strategies

### Soft Delete Contaminated Tasks
```python
audit = audit_workspace_integrity()
for category, issues in audit["issues"].items():
    for issue in issues:
        if "task_id" in issue:
            # Soft delete contaminated task
            delete_task(issue["task_id"])
            print(f"Deleted task {issue['task_id']}: {issue.get('reason')}")
```

### Update File References
```python
# Fix file references pointing outside workspace
for issue in audit["issues"]["file_reference_mismatches"]:
    task_id = issue["task_id"]
    # Review and update file references
    print(f"Task {task_id} has external file refs: {issue['file_references']}")
    # Manually update or remove references
```

### Clean Suspicious Tags
```python
# Remove project-specific tags
for issue in audit["issues"]["suspicious_tags"]:
    task_id = issue["task_id"]
    current_tags = issue["tags"]
    # Filter out suspicious tags
    clean_tags = " ".join([
        tag for tag in current_tags.split()
        if not tag.startswith("project-")
    ])
    update_task(task_id, tags=clean_tags)
```

## Version Compatibility

- **v0.4.0+**: Full workspace metadata tracking and audit support
- **v0.3.0 and earlier**: Tasks lack workspace metadata, assumed valid
- **Legacy tasks**: Can coexist with new tasks, shown as "legacy" in validation

## Summary

Workspace validation helps maintain clean, project-specific task databases by:
1. Automatically capturing creation context
2. Detecting cross-project contamination
3. Providing actionable cleanup recommendations
4. Preventing accidental task mixing

Regular use of these tools ensures your task database remains focused and relevant to your current project.