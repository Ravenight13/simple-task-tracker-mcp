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
