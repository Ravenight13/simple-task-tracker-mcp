"""
MCP Client Service for Task Viewer API.

Provides direct access to task-mcp MCP server tools without protocol overhead.
Since both services run locally on the same machine, we import the FastMCP
instance directly for maximum performance.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MCPClientService:
    """
    Wrapper service for direct task-mcp server access.

    This service provides direct function calls to task-mcp tools
    without MCP protocol overhead, since both services run locally.
    """

    def __init__(self) -> None:
        """Initialize MCP client service."""
        self._mcp: Optional[Any] = None
        self._initialized: bool = False
        self._task_mcp_path: Optional[Path] = None

    async def initialize(self) -> None:
        """
        Initialize MCP client by importing task-mcp server.

        Raises:
            RuntimeError: If task-mcp cannot be imported or initialized
        """
        if self._initialized:
            logger.warning("MCP client service already initialized")
            return

        try:
            logger.info("Initializing MCP client service...")

            # Add task-mcp to Python path
            task_mcp_path = Path("/Users/cliffclarke/Claude_Code/task-mcp/src")
            if not task_mcp_path.exists():
                raise RuntimeError(
                    f"task-mcp source directory not found at {task_mcp_path}"
                )

            if str(task_mcp_path) not in sys.path:
                sys.path.insert(0, str(task_mcp_path))
                logger.debug(f"Added {task_mcp_path} to Python path")

            self._task_mcp_path = task_mcp_path

            # Import task-mcp server module
            from task_mcp.server import mcp

            self._mcp = mcp
            self._initialized = True
            logger.info("MCP client service initialized successfully")

        except ImportError as e:
            logger.error(f"Failed to import task-mcp: {e}", exc_info=True)
            raise RuntimeError(f"MCP initialization failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}", exc_info=True)
            raise RuntimeError(f"MCP initialization failed: {str(e)}") from e

    async def close(self) -> None:
        """Close MCP client connection (cleanup on shutdown)."""
        if self._initialized:
            try:
                logger.info("Closing MCP client service...")
                self._initialized = False
                self._mcp = None

                # Remove task-mcp from Python path
                if self._task_mcp_path and str(self._task_mcp_path) in sys.path:
                    sys.path.remove(str(self._task_mcp_path))

                logger.info("MCP client service closed")
            except Exception as e:
                logger.error(f"Error closing MCP client: {e}", exc_info=True)

    async def call_tool(
        self, tool_name: str, arguments: Optional[dict[str, Any]] = None
    ) -> Any:
        """
        Call a task-mcp tool directly and return result.

        Args:
            tool_name: Name of the tool (e.g., "list_tasks", "get_task")
            arguments: Dictionary of tool arguments

        Returns:
            Tool result (type depends on tool)

        Raises:
            RuntimeError: If MCP client not initialized
            AttributeError: If tool not found
            Exception: If tool execution fails
        """
        if not self._initialized or self._mcp is None:
            raise RuntimeError("MCP client not initialized. Call initialize() first.")

        try:
            # Get the tool function from the FastMCP instance
            # FastMCP tools are registered with @mcp.tool() decorator

            # Strip "mcp__task-mcp__" prefix if present (Claude Desktop format)
            clean_tool_name = tool_name.replace("mcp__task-mcp__", "")

            # Get tool using FastMCP's get_tool method (it's async)
            try:
                tool = await self._mcp.get_tool(clean_tool_name)
            except KeyError:
                # Tool not found - list available tools
                available_tools = [t.name for t in await self._mcp.get_tools()]
                raise AttributeError(
                    f"Tool '{clean_tool_name}' not found. Available tools: {available_tools}"
                )

            # Call the tool function directly
            args = arguments or {}
            logger.debug(f"Calling tool '{clean_tool_name}' with args: {args}")

            # Call the function (may be sync or async)
            import inspect

            if inspect.iscoroutinefunction(tool.fn):
                result = await tool.fn(**args)
            else:
                result = tool.fn(**args)

            logger.debug(f"Tool '{clean_tool_name}' returned {type(result)}")
            return result

        except AttributeError as e:
            logger.warning(f"Tool not found: {clean_tool_name} - {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling tool {clean_tool_name}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to call tool '{clean_tool_name}': {str(e)}") from e

    async def list_available_tools(self) -> list[dict[str, str]]:
        """
        List all available tools from task-mcp.

        Returns:
            List of dicts with tool name and description
        """
        if not self._initialized or self._mcp is None:
            raise RuntimeError("MCP client not initialized")

        try:
            tools = []
            for tool in await self._mcp.get_tools():
                tools.append({"name": tool.name, "description": tool.description or ""})
            return tools
        except Exception as e:
            logger.error(f"Error listing tools: {e}", exc_info=True)
            raise RuntimeError(f"Failed to list tools: {str(e)}") from e


# Singleton instance
mcp_service = MCPClientService()
