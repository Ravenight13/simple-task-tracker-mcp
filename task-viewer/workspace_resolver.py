"""
Workspace Path Resolver for Task Viewer API.

Maps project hash IDs to filesystem workspace paths for task-mcp database access.
Caches project mappings on startup for fast resolution.
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class WorkspaceResolver:
    """
    Resolve workspace_path from project hash ID or explicit path.

    The task-mcp MCP server requires a workspace_path parameter for all tools.
    This class maps short project hash IDs (e.g., "1e7be4ae") to full
    filesystem paths, with caching for performance.
    """

    def __init__(self) -> None:
        """Initialize workspace resolver with empty cache."""
        self._project_cache: dict[str, dict[str, str]] = {}  # hash_id -> project data
        self._initialized: bool = False

    async def initialize(self, mcp_service: Any) -> None:
        """
        Load all projects from master database on startup.

        Args:
            mcp_service: MCP client service instance

        Raises:
            RuntimeError: If project loading fails critically
        """
        if self._initialized:
            logger.warning("Workspace resolver already initialized")
            return

        try:
            logger.info("Loading projects from task-mcp master database...")

            # Query task-mcp for all known projects
            projects = await mcp_service.call_tool("mcp__task-mcp__list_projects", {})

            # Build cache: use hash of workspace_path as project_id
            for project in projects:
                workspace_path = project.get("workspace_path", "")
                if workspace_path:
                    # Generate hash ID from workspace path
                    hash_id = self._generate_hash_id(workspace_path)

                    # Store project data with hash ID as key
                    self._project_cache[hash_id] = {
                        "id": hash_id,
                        "workspace_path": workspace_path,
                        "friendly_name": project.get("friendly_name"),
                        "created_at": project.get("created_at"),
                        "last_accessed": project.get("last_accessed"),
                    }

            self._initialized = True
            logger.info(f"Loaded {len(self._project_cache)} projects into cache")
            logger.debug(f"Project IDs: {list(self._project_cache.keys())}")

        except Exception as e:
            logger.error(f"Failed to initialize workspace resolver: {e}", exc_info=True)
            # Non-fatal: can still use default workspace or explicit paths
            self._initialized = True  # Mark as initialized even if cache is empty

    def _generate_hash_id(self, workspace_path: str) -> str:
        """
        Generate short hash ID from workspace path.

        Uses first 8 characters of SHA-256 hash for compact identifiers.

        Args:
            workspace_path: Absolute filesystem path to workspace

        Returns:
            8-character hash ID (e.g., "1e7be4ae")
        """
        # Normalize path (remove trailing slash)
        normalized_path = workspace_path.rstrip("/")

        # Generate SHA-256 hash
        hash_digest = hashlib.sha256(normalized_path.encode()).hexdigest()

        # Return first 8 characters
        return hash_digest[:8]

    def resolve(
        self, project_id: Optional[str] = None, workspace_path: Optional[str] = None
    ) -> str:
        """
        Resolve workspace_path from project hash ID or explicit path.

        Resolution priority:
        1. Explicit workspace_path parameter (highest)
        2. Project ID lookup in cache
        3. Default workspace from environment variable
        4. Raise error if none found

        Args:
            project_id: Short project hash ID (e.g., "1e7be4ae")
            workspace_path: Full filesystem path to workspace

        Returns:
            Absolute path to workspace directory

        Raises:
            ValueError: If workspace cannot be resolved
        """
        # Priority 1: Explicit workspace_path
        if workspace_path:
            if os.path.isdir(workspace_path):
                return workspace_path
            raise ValueError(f"Workspace path does not exist: {workspace_path}")

        # Priority 2: Project ID lookup
        if project_id:
            if project_id in self._project_cache:
                return self._project_cache[project_id]["workspace_path"]

            # Provide helpful error message
            available_projects = [
                f"{pid} ({self._project_cache[pid].get('friendly_name', 'Unnamed')})"
                for pid in self._project_cache.keys()
            ]
            raise ValueError(
                f"Project '{project_id}' not found. "
                f"Available projects: {', '.join(available_projects) if available_projects else 'none'}"
            )

        # Priority 3: Default workspace
        default = os.getenv("DEFAULT_WORKSPACE_PATH")
        if default and os.path.isdir(default):
            logger.debug(f"Using default workspace: {default}")
            return default

        raise ValueError(
            "No workspace_path or project_id provided. "
            "Please specify project_id query parameter or set DEFAULT_WORKSPACE_PATH environment variable"
        )

    def get_project_by_id(self, project_id: str) -> Optional[dict[str, str]]:
        """
        Get full project data by hash ID.

        Args:
            project_id: Project hash ID

        Returns:
            Project data dict or None if not found
        """
        return self._project_cache.get(project_id)

    def list_projects(self) -> list[dict[str, str]]:
        """
        List all cached projects.

        Returns:
            List of project info dicts with id, workspace_path, friendly_name, etc.
        """
        return list(self._project_cache.values())

    def get_project_count(self) -> int:
        """Get number of cached projects."""
        return len(self._project_cache)


# Singleton instance
workspace_resolver = WorkspaceResolver()
