"""
Pydantic v2 data models for the Task MCP server.

This module defines all data models with comprehensive validation rules:
- Task model with full field validation
- Entity model with full field validation (v0.3.0)
- ProjectInfo model for project metadata
- TaskCreate, TaskUpdate, EntityCreate, EntityUpdate models for API operations
- Helper functions for validation and normalization
"""

import json
from datetime import datetime
from typing import Annotated, Any, Optional

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

# Constants for validation
MAX_DESCRIPTION_LENGTH = 10_000
VALID_STATUSES = ("todo", "in_progress", "blocked", "done", "cancelled")
VALID_PRIORITIES = ("low", "medium", "high")
VALID_ENTITY_TYPES = ("file", "other")


# Helper Functions

def normalize_tags(tags: str) -> str:
    """
    Normalize tag string to lowercase with single spaces.

    Args:
        tags: Space-separated tag string

    Returns:
        Normalized tag string (lowercase, single spaces, trimmed)

    Examples:
        >>> normalize_tags("  Python   Django  REST  ")
        "python django rest"
        >>> normalize_tags("API Backend")
        "api backend"
    """
    if not tags:
        return ""
    # Split on whitespace, filter empty strings, lowercase, rejoin with single space
    return " ".join(filter(None, tags.lower().split()))


def validate_status_transition(old_status: str, new_status: str) -> bool:
    """
    Validate if a status transition is allowed.

    State machine transitions:
    - todo -> in_progress, blocked, cancelled
    - in_progress -> blocked, done, cancelled
    - blocked -> in_progress, cancelled
    - done -> (no transitions)
    - cancelled -> (no transitions)

    Args:
        old_status: Current task status
        new_status: Desired new status

    Returns:
        True if transition is valid, False otherwise

    Examples:
        >>> validate_status_transition("todo", "in_progress")
        True
        >>> validate_status_transition("done", "in_progress")
        False
    """
    # Terminal states cannot transition
    if old_status in ("done", "cancelled"):
        return old_status == new_status  # Only allow same status

    # Allow staying in same status
    if old_status == new_status:
        return True

    # Define valid transitions
    valid_transitions = {
        "todo": {"in_progress", "blocked", "cancelled"},
        "in_progress": {"blocked", "done", "cancelled"},
        "blocked": {"in_progress", "cancelled"},
    }

    return new_status in valid_transitions.get(old_status, set())


def validate_json_list_of_ints(v: Any) -> Optional[str]:
    """
    Validate and convert depends_on to JSON array of integers.

    Args:
        v: Input value (JSON string, list, or None)

    Returns:
        JSON string or None
    """
    if v is None or v == "":
        return None

    # If it's already a string, validate JSON
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError("depends_on must be a JSON array")
            if not all(isinstance(x, int) for x in parsed):
                raise ValueError("depends_on must contain only integers")
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"depends_on must be valid JSON: {e}") from e

    # If it's a list, convert to JSON
    if isinstance(v, list):
        if not all(isinstance(x, int) for x in v):
            raise ValueError("depends_on must contain only integers")
        return json.dumps(v)

    raise ValueError("depends_on must be a JSON string or list of integers")


def validate_json_list_of_strings(v: Any) -> Optional[str]:
    """
    Validate and convert file_references to JSON array of strings.

    Args:
        v: Input value (JSON string, list, or None)

    Returns:
        JSON string or None
    """
    if v is None or v == "":
        return None

    # If it's already a string, validate JSON
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError("file_references must be a JSON array")
            if not all(isinstance(x, str) for x in parsed):
                raise ValueError("file_references must contain only strings")
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"file_references must be valid JSON: {e}") from e

    # If it's a list, convert to JSON
    if isinstance(v, list):
        if not all(isinstance(x, str) for x in v):
            raise ValueError("file_references must contain only strings")
        return json.dumps(v)

    raise ValueError("file_references must be a JSON string or list of strings")


def validate_json_metadata(v: Any) -> Optional[str]:
    """
    Validate and convert metadata to JSON string.

    Accepts any valid JSON structure (objects, arrays, primitives).

    Args:
        v: Input value (JSON string, dict, list, or None)

    Returns:
        JSON string or None

    Examples:
        >>> validate_json_metadata('{"key": "value"}')
        '{"key": "value"}'
        >>> validate_json_metadata({"key": "value"})
        '{"key": "value"}'
        >>> validate_json_metadata(None)
        None
    """
    if v is None or v == "":
        return None

    # If it's already a string, validate JSON
    if isinstance(v, str):
        try:
            json.loads(v)  # Validate it's valid JSON
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"metadata must be valid JSON: {e}") from e

    # If it's a dict or list, convert to JSON
    if isinstance(v, (dict, list)):
        try:
            return json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"metadata cannot be serialized to JSON: {e}") from e

    raise ValueError("metadata must be a JSON string, dict, or list")


# Pydantic Models

class Task(BaseModel):
    """
    Complete task model with all fields and validations.

    Represents a task or subtask in the tracking system with comprehensive
    metadata, status tracking, dependencies, and file references.
    """

    model_config = ConfigDict(
        strict=False,  # Allow coercion for datetime strings from DB
        validate_assignment=True,  # Validate on attribute updates
        extra='forbid',  # Reject unknown fields
    )

    # Core fields
    id: Optional[int] = Field(None, description="Task ID (auto-generated)")
    title: Annotated[str, Field(min_length=1, max_length=500)] = Field(
        ..., description="Task title (required, 1-500 chars)"
    )
    description: Optional[str] = Field(
        None, description="Task description (max 10,000 chars)"
    )

    # Status and priority
    status: str = Field(
        default="todo",
        description="Task status: todo, in_progress, blocked, done, cancelled"
    )
    priority: str = Field(
        default="medium",
        description="Task priority: low, medium, high"
    )

    # Relationships
    parent_task_id: Optional[int] = Field(
        None, description="Parent task ID for subtasks"
    )
    depends_on: Annotated[
        Optional[str],
        BeforeValidator(validate_json_list_of_ints)
    ] = Field(
        None, description="JSON array of task IDs this task depends on"
    )

    # Organization
    tags: Optional[str] = Field(
        None, description="Space-separated tags (normalized to lowercase)"
    )
    blocker_reason: Optional[str] = Field(
        None, description="Reason for blocked status (required when status=blocked)"
    )
    file_references: Annotated[
        Optional[str],
        BeforeValidator(validate_json_list_of_strings)
    ] = Field(
        None, description="JSON array of file paths referenced by this task"
    )

    # Metadata
    created_by: Optional[str] = Field(
        None, description="Conversation ID that created this task"
    )
    created_at: Optional[datetime] = Field(
        None, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Last update timestamp"
    )
    completed_at: Optional[datetime] = Field(
        None, description="Completion timestamp (when status changed to done)"
    )
    deleted_at: Optional[datetime] = Field(
        None, description="Soft delete timestamp"
    )

    # Field Validators

    @field_validator('description')
    @classmethod
    def validate_description_length(cls, v: Optional[str]) -> Optional[str]:
        """Enforce maximum description length of 10,000 characters."""
        if v is not None and len(v) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters "
                f"(got {len(v)} characters)"
            )
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status is one of the allowed values."""
        if v is None:
            return None
        if v not in VALID_STATUSES:
            raise ValueError(
                f"Status must be one of {VALID_STATUSES}, got '{v}'"
            )
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority is one of the allowed values."""
        if v is None:
            return None
        if v not in VALID_PRIORITIES:
            raise ValueError(
                f"Priority must be one of {VALID_PRIORITIES}, got '{v}'"
            )
        return v

    @field_validator('tags')
    @classmethod
    def validate_and_normalize_tags(cls, v: Optional[str]) -> Optional[str]:
        """Normalize tags to lowercase with single spaces."""
        if v is None:
            return None
        return normalize_tags(v)

    # Model Validators

    @model_validator(mode='after')
    def validate_blocker_reason_required(self) -> 'Task':
        """
        Ensure blocker_reason is provided when status is 'blocked'.

        This cross-field validation enforces the business rule that blocked
        tasks must document why they are blocked.
        """
        if self.status == 'blocked' and (not self.blocker_reason or not self.blocker_reason.strip()):
            raise ValueError(
                "blocker_reason is required when status is 'blocked'"
            )
        return self

    @model_validator(mode='after')
    def set_completed_at(self) -> 'Task':
        """
        Auto-set completed_at timestamp when status changes to 'done'.

        Note: This only works for new Task instances. For updates, the
        database layer should handle this logic.
        """
        if self.status == 'done' and self.completed_at is None:
            self.completed_at = datetime.utcnow()
        return self

    # Helper Methods

    def get_depends_on_list(self) -> list[int]:
        """
        Parse depends_on JSON string into list of task IDs.

        Returns:
            List of integer task IDs, or empty list if no dependencies
        """
        if not self.depends_on:
            return []
        try:
            result: list[int] = json.loads(self.depends_on)
            return result
        except json.JSONDecodeError:
            return []

    def get_file_references_list(self) -> list[str]:
        """
        Parse file_references JSON string into list of file paths.

        Returns:
            List of file paths, or empty list if no references
        """
        if not self.file_references:
            return []
        try:
            result: list[str] = json.loads(self.file_references)
            return result
        except json.JSONDecodeError:
            return []


class TaskCreate(BaseModel):
    """
    Model for creating new tasks.

    Subset of Task fields that can be provided during creation.
    Other fields (id, timestamps) are auto-generated.
    """

    model_config = ConfigDict(
        strict=False,
        extra='forbid',
    )

    title: Annotated[str, Field(min_length=1, max_length=500)]
    description: Optional[str] = None
    status: str = Field(default="todo")
    priority: str = Field(default="medium")
    parent_task_id: Optional[int] = None
    depends_on: Annotated[
        Optional[str],
        BeforeValidator(validate_json_list_of_ints)
    ] = None
    tags: Optional[str] = None
    blocker_reason: Optional[str] = None
    file_references: Annotated[
        Optional[str],
        BeforeValidator(validate_json_list_of_strings)
    ] = None
    created_by: Optional[str] = None

    # Reuse validators from Task model
    _validate_description = field_validator('description')(
        Task.validate_description_length.__func__  # type: ignore[attr-defined]
    )
    _validate_status = field_validator('status')(
        Task.validate_status.__func__  # type: ignore[attr-defined]
    )
    _validate_priority = field_validator('priority')(
        Task.validate_priority.__func__  # type: ignore[attr-defined]
    )
    _validate_tags = field_validator('tags')(
        Task.validate_and_normalize_tags.__func__  # type: ignore[attr-defined]
    )

    @model_validator(mode='after')
    def validate_blocker_reason_required(self) -> 'TaskCreate':
        """Ensure blocker_reason is provided when status is 'blocked'."""
        if self.status == 'blocked' and (not self.blocker_reason or not self.blocker_reason.strip()):
            raise ValueError(
                "blocker_reason is required when status is 'blocked'"
            )
        return self


class TaskUpdate(BaseModel):
    """
    Model for updating existing tasks.

    All fields are optional - only provided fields will be updated.
    Includes validation for field constraints.
    """

    model_config = ConfigDict(
        strict=False,
        extra='forbid',
    )

    title: Optional[Annotated[str, Field(min_length=1, max_length=500)]] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    parent_task_id: Optional[int] = None
    depends_on: Annotated[
        Optional[str],
        BeforeValidator(validate_json_list_of_ints)
    ] = None
    tags: Optional[str] = None
    blocker_reason: Optional[str] = None
    file_references: Annotated[
        Optional[str],
        BeforeValidator(validate_json_list_of_strings)
    ] = None

    # Reuse validators from Task model
    _validate_description = field_validator('description')(
        Task.validate_description_length.__func__  # type: ignore[attr-defined]
    )
    _validate_status = field_validator('status')(
        Task.validate_status.__func__  # type: ignore[attr-defined]
    )
    _validate_priority = field_validator('priority')(
        Task.validate_priority.__func__  # type: ignore[attr-defined]
    )
    _validate_tags = field_validator('tags')(
        Task.validate_and_normalize_tags.__func__  # type: ignore[attr-defined]
    )

    @model_validator(mode='after')
    def validate_blocker_reason_if_blocked(self) -> 'TaskUpdate':
        """
        Validate blocker_reason is provided if status is being set to 'blocked'.

        Note: This only validates if status is in the update. The database
        layer must check the current task status for complete validation.
        """
        if self.status == 'blocked' and (not self.blocker_reason or not self.blocker_reason.strip()):
            raise ValueError(
                "blocker_reason is required when status is 'blocked'"
            )
        return self


class ProjectInfo(BaseModel):
    """
    Project metadata from master database.

    Represents a registered project workspace with tracking information.
    """

    model_config = ConfigDict(
        strict=False,
        extra='forbid',
    )

    id: str = Field(
        ...,
        min_length=8,
        max_length=8,
        description="8-character hash of workspace path"
    )
    workspace_path: str = Field(
        ...,
        min_length=1,
        description="Absolute path to project workspace"
    )
    friendly_name: Optional[str] = Field(
        None,
        description="User-friendly project name"
    )
    created_at: datetime = Field(
        ...,
        description="Project registration timestamp"
    )
    last_accessed: datetime = Field(
        ...,
        description="Last access timestamp"
    )

    @field_validator('workspace_path')
    @classmethod
    def validate_workspace_path(cls, v: str) -> str:
        """Validate workspace path is absolute."""
        if not v.startswith('/'):
            raise ValueError("workspace_path must be an absolute path")
        return v


class ProjectStats(BaseModel):
    """
    Project statistics for dashboard/reporting.

    Provides aggregate counts and metrics for a project.
    """

    model_config = ConfigDict(extra='forbid')

    total_tasks: int = Field(ge=0)
    todo_count: int = Field(ge=0)
    in_progress_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    done_count: int = Field(ge=0)
    cancelled_count: int = Field(ge=0)
    low_priority_count: int = Field(ge=0)
    medium_priority_count: int = Field(ge=0)
    high_priority_count: int = Field(ge=0)


class ProjectInfoWithStats(ProjectInfo):
    """
    Extended project info including task statistics.

    Combines project metadata with task counts for comprehensive reporting.
    """

    stats: ProjectStats = Field(
        ...,
        description="Task statistics for this project"
    )


# ============================================================================
# ENTITY SYSTEM MODELS (v0.3.0)
# ============================================================================


class Entity(BaseModel):
    """
    Entity model representing domain concepts linked to tasks.

    Entities represent files, vendors, APIs, or any domain concept that
    tasks reference. The MVP supports two types:
    - file: File paths in the codebase
    - other: Generic catch-all for domain-specific entities

    Examples:
        File entity:
            Entity(
                entity_type="file",
                name="Login Controller",
                identifier="/src/auth/login.py",
                metadata='{"language": "python", "line_count": 250}',
                tags="auth backend"
            )

        Vendor entity (using "other" type):
            Entity(
                entity_type="other",
                name="ABC Insurance Vendor",
                identifier="ABC-INS",
                metadata='{"vendor_code": "ABC", "format": "xlsx", "phase": "active"}',
                tags="vendor insurance commission"
            )
    """

    model_config = ConfigDict(
        strict=False,  # Allow coercion for datetime strings from DB
        validate_assignment=True,  # Validate on attribute updates
        extra='forbid',  # Reject unknown fields
    )

    # Core fields
    id: Optional[int] = Field(None, description="Entity ID (auto-generated)")
    entity_type: str = Field(
        ...,
        description="Entity type: 'file' or 'other'"
    )
    name: Annotated[str, Field(min_length=1, max_length=500)] = Field(
        ..., description="Human-readable entity name (required, 1-500 chars)"
    )
    identifier: Optional[Annotated[str, Field(max_length=1000)]] = Field(
        None,
        description="Unique identifier (file path, vendor code, etc.) - max 1000 chars"
    )
    description: Optional[str] = Field(
        None, description="Optional description (max 10,000 chars)"
    )

    # Metadata and organization
    metadata: Annotated[
        Optional[str],
        BeforeValidator(validate_json_metadata)
    ] = Field(
        None,
        description="Generic JSON metadata (freeform structure)"
    )
    tags: Optional[str] = Field(
        None,
        description="Space-separated tags (normalized to lowercase)"
    )

    # Audit fields
    created_by: Optional[str] = Field(
        None,
        description="Conversation/session ID that created this entity"
    )
    created_at: Optional[datetime] = Field(
        None,
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Last update timestamp"
    )
    updated_by: Optional[str] = Field(
        None,
        description="Conversation/session ID that last updated this entity"
    )
    deleted_at: Optional[datetime] = Field(
        None,
        description="Soft delete timestamp"
    )

    # Field Validators

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity_type is one of the allowed values."""
        if v not in VALID_ENTITY_TYPES:
            raise ValueError(
                f"entity_type must be one of {VALID_ENTITY_TYPES}, got '{v}'"
            )
        return v

    @field_validator('description')
    @classmethod
    def validate_description_length(cls, v: Optional[str]) -> Optional[str]:
        """Enforce maximum description length of 10,000 characters."""
        if v is not None and len(v) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters "
                f"(got {len(v)} characters)"
            )
        return v

    @field_validator('tags')
    @classmethod
    def validate_and_normalize_tags(cls, v: Optional[str]) -> Optional[str]:
        """Normalize tags to lowercase with single spaces."""
        if v is None:
            return None
        return normalize_tags(v)

    # Helper Methods

    def get_metadata_dict(self) -> dict[str, Any]:
        """
        Parse metadata JSON string into dictionary.

        Returns:
            Dictionary from metadata JSON, or empty dict if no metadata

        Examples:
            >>> entity = Entity(entity_type="file", name="test.py",
            ...                 metadata='{"language": "python"}')
            >>> entity.get_metadata_dict()
            {'language': 'python'}
        """
        if not self.metadata:
            return {}
        try:
            result: dict[str, Any] = json.loads(self.metadata)
            return result if isinstance(result, dict) else {}
        except json.JSONDecodeError:
            return {}


class EntityCreate(BaseModel):
    """
    Model for creating new entities.

    Subset of Entity fields that can be provided during creation.
    Other fields (id, timestamps) are auto-generated.
    """

    model_config = ConfigDict(
        strict=False,
        extra='forbid',
    )

    entity_type: str
    name: Annotated[str, Field(min_length=1, max_length=500)]
    identifier: Optional[Annotated[str, Field(max_length=1000)]] = None
    description: Optional[str] = None
    metadata: Annotated[
        Optional[str],
        BeforeValidator(validate_json_metadata)
    ] = None
    tags: Optional[str] = None
    created_by: Optional[str] = None

    # Reuse validators from Entity model
    _validate_entity_type = field_validator('entity_type')(
        Entity.validate_entity_type.__func__  # type: ignore[attr-defined]
    )
    _validate_description = field_validator('description')(
        Entity.validate_description_length.__func__  # type: ignore[attr-defined]
    )
    _validate_tags = field_validator('tags')(
        Entity.validate_and_normalize_tags.__func__  # type: ignore[attr-defined]
    )


class EntityUpdate(BaseModel):
    """
    Model for updating existing entities.

    All fields are optional - only provided fields will be updated.
    Includes validation for field constraints.
    """

    model_config = ConfigDict(
        strict=False,
        extra='forbid',
    )

    name: Optional[Annotated[str, Field(min_length=1, max_length=500)]] = None
    identifier: Optional[Annotated[str, Field(max_length=1000)]] = None
    description: Optional[str] = None
    metadata: Annotated[
        Optional[str],
        BeforeValidator(validate_json_metadata)
    ] = None
    tags: Optional[str] = None
    updated_by: Optional[str] = Field(
        None,
        description="Conversation/session ID updating this entity"
    )

    # Reuse validators from Entity model
    _validate_description = field_validator('description')(
        Entity.validate_description_length.__func__  # type: ignore[attr-defined]
    )
    _validate_tags = field_validator('tags')(
        Entity.validate_and_normalize_tags.__func__  # type: ignore[attr-defined]
    )
