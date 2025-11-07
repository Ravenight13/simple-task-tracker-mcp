"""View transformation utilities for reducing token usage in MCP tool outputs.

This module provides transformation functions that convert full database records
into summary views containing only essential fields, significantly reducing token
usage when listing or searching tasks and entities.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def estimate_tokens(obj: Any) -> int:
    """Estimate token count for a response object.

    Uses character count with ~4 characters per token as a heuristic.
    This provides a reasonable estimate for monitoring token usage.

    Args:
        obj: The object to estimate tokens for (dict, list, string, or other)

    Returns:
        Estimated token count (integer)
    """
    if isinstance(obj, dict):
        return sum(estimate_tokens(v) for v in obj.values())
    elif isinstance(obj, list):
        return sum(estimate_tokens(item) for item in obj)
    elif isinstance(obj, str):
        return len(obj) // 4  # Approximate 4 chars per token
    else:
        # For numbers, booleans, None, etc.
        return 0


def validate_response_size(
    response: Any,
    max_tokens: int = 15000,
    warning_threshold: int = 12000
) -> None:
    """Validate response doesn't exceed token limit.

    Raises ResponseSizeExceededError if response exceeds max_tokens.
    Logs warning if response approaches warning_threshold (>80% of max).

    Args:
        response: The response object to validate
        max_tokens: Maximum allowed tokens (default 15000)
        warning_threshold: Token count to trigger warning (default 12000)

    Raises:
        ResponseSizeExceededError: If estimated tokens > max_tokens

    Side Effects:
        Logs warning message if tokens > warning_threshold
    """
    from .errors import ResponseSizeExceededError

    tokens = estimate_tokens(response)

    if tokens > max_tokens:
        raise ResponseSizeExceededError(
            actual_tokens=tokens,
            max_tokens=max_tokens
        )

    if tokens > warning_threshold:
        logger.warning(
            f"Response approaching token limit: {tokens}/{max_tokens} tokens "
            f"({100*tokens//max_tokens}% full). Consider using summary mode or "
            f"pagination for better performance."
        )


def task_summary_view(task: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a full task record into a summary view.

    Reduces a task to essential fields for listing/search operations.
    Preserves: id, title, status, priority, tags, parent_task_id,
              created_at, updated_at

    Args:
        task: Full task dictionary from database

    Returns:
        Summary task dictionary with only essential fields
    """
    return {
        "id": task.get("id"),
        "title": task.get("title"),
        "status": task.get("status"),
        "priority": task.get("priority"),
        "tags": task.get("tags"),
        "parent_task_id": task.get("parent_task_id"),
        "created_at": task.get("created_at"),
        "updated_at": task.get("updated_at"),
    }


def entity_summary_view(entity: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a full entity record into a summary view.

    Reduces an entity to essential fields for listing/search operations.
    Preserves: id, entity_type, name, identifier, tags, created_at

    Args:
        entity: Full entity dictionary from database

    Returns:
        Summary entity dictionary with only essential fields
    """
    return {
        "id": entity.get("id"),
        "entity_type": entity.get("entity_type"),
        "name": entity.get("name"),
        "identifier": entity.get("identifier"),
        "tags": entity.get("tags"),
        "created_at": entity.get("created_at"),
    }


def task_tree_summary(task: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a task tree structure into summary format recursively.

    Applies task_summary_view to the root task and all subtasks recursively,
    preserving the tree structure while reducing token usage.

    Args:
        task: Full task dictionary with optional 'subtasks' field

    Returns:
        Summary task tree with all tasks reduced to essential fields
    """
    # Apply summary to main task
    summary = task_summary_view(task)

    # Recursively apply to subtasks if they exist
    if "subtasks" in task and task["subtasks"]:
        summary["subtasks"] = [
            task_tree_summary(subtask) for subtask in task["subtasks"]
        ]

    return summary


def link_metadata_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    """Transform an item with link metadata into summary format.

    Used for entities/tasks that include relationship metadata from junction tables.
    Preserves link_created_at and link_created_by fields alongside the summary.

    Args:
        item: Full dictionary that may contain link metadata fields

    Returns:
        Summary dictionary with essential fields plus link metadata
    """
    # Determine if this is a task or entity based on available fields
    if "entity_type" in item:
        # It's an entity
        summary = entity_summary_view(item)
    elif "title" in item and "status" in item:
        # It's a task
        summary = task_summary_view(item)
    else:
        # Unknown type, return minimal fields
        summary = {
            "id": item.get("id"),
            "name": item.get("name") or item.get("title"),
        }

    # Preserve link metadata if present
    if "link_created_at" in item:
        summary["link_created_at"] = item["link_created_at"]
    if "link_created_by" in item:
        summary["link_created_by"] = item["link_created_by"]

    return summary


def apply_list_mode(
    items: List[Dict[str, Any]],
    mode: str,
    transform_func: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Apply mode transformation to a list of items.

    Helper function to consistently apply summary/details mode to lists.

    Args:
        items: List of full dictionaries from database
        mode: Either "summary" or "details"
        transform_func: Optional transformation function for summary mode
                       Defaults to task_summary_view if not provided

    Returns:
        List of items in requested format

    Raises:
        ValueError: If mode is not "summary" or "details"
    """
    if mode == "summary":
        if transform_func is None:
            transform_func = task_summary_view
        return [transform_func(item) for item in items]
    elif mode == "details":
        return items
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'summary' or 'details'")
