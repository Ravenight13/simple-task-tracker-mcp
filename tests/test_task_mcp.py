"""Basic test placeholder for Task MCP server."""

import pytest

from task_mcp import __version__


def test_version() -> None:
    """Test that version is defined correctly."""
    assert __version__ == "0.1.0"


@pytest.mark.asyncio
async def test_placeholder() -> None:
    """Placeholder test for async functionality."""
    # TODO: Add actual tests when implementation is complete
    assert True
