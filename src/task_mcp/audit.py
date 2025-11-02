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
        report: dict[str, Any] = {
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
        tasks: list[dict[str, Any]] = [dict(row) for row in cursor.fetchall()]
        report["total_tasks"] = len(tasks)

        # Get all entities
        cursor.execute(f"SELECT * FROM entities {deleted_filter}")
        entities: list[dict[str, Any]] = [dict(row) for row in cursor.fetchall()]
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

        mismatched_refs: list[str] = []
        for ref in file_refs:
            try:
                ref_path = Path(ref).resolve()

                # Check if path is outside workspace
                if not _is_path_within(ref_path, workspace_prefix):
                    mismatched_refs.append(ref)
            except (ValueError, OSError):
                # Invalid path, skip
                continue

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
    workspace_path: str,  # noqa: ARG001
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
        reasons: list[str] = []

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
        external_paths: list[str] = []

        for match in matches:
            try:
                path = Path(match).resolve()
                if not _is_path_within(path, workspace_prefix):
                    external_paths.append(match)
            except (ValueError, OSError, RuntimeError):
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
        except (ValueError, OSError, RuntimeError):
            # Invalid path, skip
            continue


def _check_git_consistency(
    tasks: list[dict[str, Any]],
    entities: list[dict[str, Any]],  # noqa: ARG001
    workspace_path: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Check git repository consistency for the workspace."""
    git_info: dict[str, Any] = {
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
                check=False,
            )
            if result.returncode == 0:
                git_info["git_remote"] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

    # Check if file references point to different git repos
    all_paths: list[tuple[dict[str, Any], str]] = []

    # Collect paths from tasks
    for task in tasks:
        if task.get("file_references"):
            try:
                file_refs = json.loads(task["file_references"])
                all_paths.extend([(task, ref) for ref in file_refs])
            except json.JSONDecodeError:
                pass

    # Check each path's git root
    seen_mismatches: set[tuple[int, str]] = set()

    for task, path in all_paths:
        path_git_root = _find_git_root(path)

        if path_git_root and workspace_git_root and Path(path_git_root).resolve() != Path(workspace_git_root).resolve():
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
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def _calculate_statistics(report: dict[str, Any]) -> None:
    """Calculate statistics from audit findings."""
    contaminated_task_ids: set[int] = set()
    contaminated_entity_ids: set[int] = set()
    severity_counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

    # Count unique contaminated tasks
    for _issue_type, issues in report["issues"].items():
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
    recommendations: list[str] = []

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
