"""
Custom MCP error classes for task tracking server.

Provides structured error handling with error codes, messages, and detailed
context for client error handling and logging.
"""

from typing import Any


class MCPError(Exception):
    """Base MCP error with code, message, and details."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize MCP error.

        Args:
            code: Error code for client identification
            message: Human-readable error message
            details: Additional error context as dict
        """
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert error to dict representation for MCP response.

        Returns:
            Dictionary with code, message, and details
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class ResponseSizeExceededError(MCPError):
    """Raised when response would exceed token limit."""

    def __init__(
        self,
        actual_tokens: int,
        max_tokens: int = 15000,
    ) -> None:
        """
        Initialize response size error.

        Args:
            actual_tokens: Actual token count of response
            max_tokens: Maximum allowed tokens
        """
        super().__init__(
            code="RESPONSE_SIZE_EXCEEDED",
            message=f"Response ({actual_tokens} tokens) exceeds {max_tokens} token limit",
            details={
                "actual_tokens": actual_tokens,
                "max_tokens": max_tokens,
            },
        )


class InvalidModeError(MCPError):
    """Raised when invalid mode (summary/details) provided."""

    def __init__(self, provided_mode: str) -> None:
        """
        Initialize invalid mode error.

        Args:
            provided_mode: The invalid mode value provided
        """
        super().__init__(
            code="INVALID_MODE",
            message=f"Invalid mode: {provided_mode}. Must be 'summary' or 'details'",
            details={"provided_mode": provided_mode},
        )


class PaginationError(MCPError):
    """Raised for invalid pagination parameters."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """
        Initialize pagination error.

        Args:
            message: Human-readable error message
            details: Additional error context
        """
        super().__init__(
            code="PAGINATION_INVALID",
            message=message,
            details=details or {},
        )


class NotFoundError(MCPError):
    """Raised when task/entity not found."""

    def __init__(self, resource_type: str, resource_id: int) -> None:
        """
        Initialize not found error.

        Args:
            resource_type: Type of resource (e.g., 'Task', 'Entity')
            resource_id: ID of missing resource
        """
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource_type} with id {resource_id} not found",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )


class InvalidFilterError(MCPError):
    """Raised for invalid filter values."""

    def __init__(
        self,
        filter_name: str,
        invalid_value: str,
        valid_values: list[str],
    ) -> None:
        """
        Initialize invalid filter error.

        Args:
            filter_name: Name of the filter parameter
            invalid_value: The invalid value provided
            valid_values: List of valid values
        """
        super().__init__(
            code="INVALID_FILTER",
            message=f"Invalid {filter_name}: {invalid_value}. Must be one of: {', '.join(valid_values)}",
            details={
                "filter_name": filter_name,
                "invalid_value": invalid_value,
                "valid_values": valid_values,
            },
        )


class WorkspaceValidationError(MCPError):
    """Raised for workspace validation failures."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize workspace validation error.

        Args:
            message: Human-readable error message
            details: Additional error context
        """
        super().__init__(
            code="WORKSPACE_INVALID",
            message=message,
            details=details or {},
        )
