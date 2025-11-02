"""Type stubs for workspace integrity audit functions."""

from typing import Any

def perform_workspace_audit(
    workspace_path: str,
    include_deleted: bool = False,
    check_git_repo: bool = True,
) -> dict[str, Any]: ...

def _check_file_references(
    tasks: list[dict[str, Any]],
    workspace_path: str,
    report: dict[str, Any],
) -> None: ...

def _check_suspicious_tags(
    tasks: list[dict[str, Any]],
    workspace_path: str,
    report: dict[str, Any],
) -> None: ...

def _check_description_paths(
    tasks: list[dict[str, Any]],
    workspace_path: str,
    report: dict[str, Any],
) -> None: ...

def _check_entity_identifiers(
    entities: list[dict[str, Any]],
    workspace_path: str,
    report: dict[str, Any],
) -> None: ...

def _check_git_consistency(
    tasks: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    workspace_path: str,
    report: dict[str, Any],
) -> dict[str, Any]: ...

def _is_path_within(child: Path, parent: Path) -> bool: ...

def _find_git_root(path: str) -> str | None: ...

def _calculate_statistics(report: dict[str, Any]) -> None: ...

def _generate_recommendations(report: dict[str, Any]) -> None: ...

from pathlib import Path
