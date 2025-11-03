"""
Pydantic response models for Task Viewer REST API.

This module defines type-safe response models for all API endpoints.
All models use Pydantic v2 for validation and serialization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    """Response model for a single task."""

    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    parent_task_id: Optional[int] = None
    depends_on: Optional[str] = None  # JSON array as string
    tags: Optional[str] = None
    blocker_reason: Optional[str] = None
    file_references: Optional[str] = None  # JSON array as string
    created_by: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    subtasks: Optional[list[TaskResponse]] = None  # For tree endpoint

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Response model for list of tasks with pagination and metadata."""

    tasks: list[TaskResponse]
    total: int
    limit: int = 100
    offset: int = 0
    filters: Optional[dict[str, Any]] = None
    meta: Optional[dict[str, Any]] = None  # Task counts by status/priority


class TaskSearchResponse(BaseModel):
    """Response model for task search results."""

    tasks: list[TaskResponse]
    total: int
    query: str
    limit: int = 20


class ProjectResponse(BaseModel):
    """Response model for a single project."""

    id: str  # Project hash ID
    workspace_path: str
    friendly_name: Optional[str] = None
    created_at: datetime
    last_accessed: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Response model for list of projects."""

    projects: list[ProjectResponse]
    total: int


class ProjectStatsResponse(BaseModel):
    """Response model for project statistics."""

    total_tasks: int
    by_status: dict[str, int]
    by_priority: dict[str, int]


class ProjectInfoResponse(BaseModel):
    """Response model for detailed project info."""

    project: ProjectResponse
    stats: ProjectStatsResponse


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    status_code: int
    details: Optional[dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str
    version: str = "1.0.0"
    mcp_connected: bool
    projects_loaded: int = 0
    timestamp: Optional[datetime] = None
    error: Optional[str] = None


class EntityResponse(BaseModel):
    """Response model for a single entity.

    Entities are typed objects (file, vendor, etc.) that can be linked to tasks
    for rich context management. Entity metadata is stored as a JSON string for
    flexible domain-specific data storage.
    """

    id: int
    entity_type: str = Field(..., description="Entity type: 'file' or 'other'")
    name: str = Field(..., description="Human-readable entity name")
    identifier: Optional[str] = Field(None, description="Unique identifier (file path, vendor code, etc.)")
    description: Optional[str] = Field(None, max_length=10000, description="Entity description (max 10k chars)")
    metadata: Optional[str] = Field(None, description="Generic JSON metadata as string")
    tags: Optional[str] = Field(None, description="Space-separated tags")
    created_by: str = Field(..., description="Conversation ID that created this entity")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    updated_at: str = Field(..., description="ISO 8601 timestamp")
    deleted_at: Optional[str] = Field(None, description="Soft delete timestamp")

    class Config:
        from_attributes = True


class EntityListResponse(BaseModel):
    """Response model for paginated entity list.

    Used for list_entities endpoint with optional filtering by entity_type and tags.
    """

    entities: list[EntityResponse]
    total: int = Field(..., description="Total number of entities matching filters")
    limit: int = Field(100, description="Maximum entities per page")
    offset: int = Field(0, description="Number of entities skipped")
    filters: Optional[dict[str, Any]] = Field(None, description="Applied filters (entity_type, tags)")


class EntitySearchResponse(BaseModel):
    """Response model for entity search results.

    Full-text search on entity name and identifier fields.
    """

    entities: list[EntityResponse]
    total: int = Field(..., description="Total number of search results")
    query: str = Field(..., description="Search query string")
    limit: int = Field(20, description="Maximum results returned")
