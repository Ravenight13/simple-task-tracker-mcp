"""Tests for token limit validation in response handling."""

from __future__ import annotations

from pathlib import Path

import pytest

from task_mcp.views import estimate_tokens, validate_response_size


class TestEstimateTokens:
    """Test estimate_tokens utility function."""

    def test_estimate_tokens_empty_string(self) -> None:
        """Test token estimation for empty string."""
        assert estimate_tokens("") == 0

    def test_estimate_tokens_short_string(self) -> None:
        """Test token estimation for short string."""
        # "hello" = 5 chars / 4 = 1 token
        assert estimate_tokens("hello") == 1

    def test_estimate_tokens_exact_division(self) -> None:
        """Test token estimation with exact 4-char boundary."""
        # "abcd" = 4 chars / 4 = 1 token
        assert estimate_tokens("abcd") == 1

    def test_estimate_tokens_long_string(self) -> None:
        """Test token estimation for longer string."""
        # 400 chars / 4 = 100 tokens
        text = "a" * 400
        assert estimate_tokens(text) == 100

    def test_estimate_tokens_dict(self) -> None:
        """Test token estimation for dictionary."""
        # Sum of values only (not keys in our implementation)
        data = {"name": "test", "id": "123"}
        # "test" (4) + "123" (3) = 7 chars / 4 = 1 token
        assert estimate_tokens(data) == 1

    def test_estimate_tokens_nested_dict(self) -> None:
        """Test token estimation for nested dictionary."""
        data = {
            "title": "My Task",
            "metadata": {
                "key": "value"
            }
        }
        # Recursively sum all string values
        tokens = estimate_tokens(data)
        assert tokens > 0

    def test_estimate_tokens_list(self) -> None:
        """Test token estimation for list."""
        data = ["hello", "world", "test"]
        # "hello" (5) + "world" (5) + "test" (4) = 14 chars / 4 = 3 tokens
        assert estimate_tokens(data) == 3

    def test_estimate_tokens_mixed_types(self) -> None:
        """Test token estimation for mixed types."""
        data = {
            "id": 42,  # Numbers don't count
            "name": "task",  # Strings count
            "tags": ["important", "urgent"],  # Nested strings count
        }
        tokens = estimate_tokens(data)
        assert tokens > 0

    def test_estimate_tokens_numeric_types(self) -> None:
        """Test that numeric types don't contribute tokens."""
        data = {
            "int_val": 12345,
            "float_val": 3.14159,
            "bool_val": True,
            "none_val": None,
        }
        assert estimate_tokens(data) == 0

    def test_estimate_tokens_large_response(self) -> None:
        """Test token estimation for large response object."""
        large_list = [
            {
                "id": i,
                "title": f"Task {i}",
                "description": "a" * 100,  # 100 chars of description
                "status": "todo",
            }
            for i in range(10)  # 10 tasks
        ]
        tokens = estimate_tokens(large_list)
        # Each description is ~100 chars = 25 tokens
        # 10 * 25 = 250+ tokens
        assert tokens >= 250


class TestValidateResponseSize:
    """Test validate_response_size validation function."""

    def test_validate_response_size_empty_response(self) -> None:
        """Test validation passes for empty response."""
        # Should not raise
        validate_response_size({})
        validate_response_size([])

    def test_validate_response_size_small_response(self) -> None:
        """Test validation passes for small response."""
        small_data = {
            "id": 1,
            "title": "Task",
            "status": "todo"
        }
        # Should not raise
        validate_response_size(small_data)

    def test_validate_response_size_list_of_tasks(self) -> None:
        """Test validation passes for reasonable task list."""
        tasks = [
            {
                "id": i,
                "title": f"Task {i}",
                "status": "todo"
            }
            for i in range(100)
        ]
        # Should not raise for reasonable list
        validate_response_size(tasks)

    def test_validate_response_size_exceeds_limit(self) -> None:
        """Test validation raises for response exceeding token limit."""
        # Create response that exceeds 15000 tokens
        # 4000 chars = 1000 tokens, need 60000 chars for 15000 tokens
        large_response = [
            {
                "id": i,
                "title": f"Task {i}",
                "description": "a" * 6000,  # 6000 chars per task
                "status": "todo"
            }
            for i in range(10)  # 10 * 6000 = 60000 chars = 15000 tokens
        ]

        with pytest.raises(ValueError, match="exceeds token limit"):
            validate_response_size(large_response)

    def test_validate_response_size_warning_threshold(self, caplog) -> None:
        """Test warning is logged when approaching limit."""
        # Create response that exceeds 12000 tokens but under 15000
        # 50000 chars = 12500 tokens (80%+ of limit)
        large_response = [
            {
                "id": i,
                "title": f"Task {i}",
                "description": "a" * 5000,  # 5000 chars per task
                "status": "todo"
            }
            for i in range(10)  # 10 * 5000 = 50000 chars = 12500 tokens
        ]

        # Should not raise but should log warning
        import logging
        with caplog.at_level(logging.WARNING):
            validate_response_size(large_response)

        # Check warning was logged
        assert any("approaching token limit" in record.message for record in caplog.records)

    def test_validate_response_size_custom_limits(self) -> None:
        """Test validation with custom token limits."""
        large_data = {
            "data": "a" * 10000  # 2500 tokens
        }

        # Should pass with high limit
        validate_response_size(large_data, max_tokens=5000)

        # Should fail with low limit
        with pytest.raises(ValueError, match="exceeds token limit"):
            validate_response_size(large_data, max_tokens=2000)

    def test_validate_response_size_custom_warning_threshold(self, caplog) -> None:
        """Test warning threshold can be customized."""
        data = {
            "data": "a" * 4000  # 1000 tokens
        }

        import logging
        with caplog.at_level(logging.WARNING):
            # Should warn since 1000 > 900 threshold
            validate_response_size(data, max_tokens=2000, warning_threshold=900)

        assert any("approaching token limit" in record.message for record in caplog.records)

    def test_validate_response_size_at_boundary(self, caplog) -> None:
        """Test validation at exact boundary."""
        # Create response with exactly 15000 tokens
        data = {
            "data": "a" * 60000  # 60000 / 4 = 15000 tokens
        }

        # Should warn but not raise (15000 is at boundary, triggers warning)
        import logging
        with caplog.at_level(logging.WARNING):
            validate_response_size(data, max_tokens=15000)

        # Should log warning for being at warning threshold
        assert any("approaching token limit" in record.message for record in caplog.records)

    def test_validate_response_size_just_under_limit(self) -> None:
        """Test validation just under limit."""
        # Create response with 14999 tokens (just under)
        data = {
            "data": "a" * 59996  # 59996 / 4 = 14999 tokens
        }

        # Should pass
        validate_response_size(data, max_tokens=15000)

    def test_validate_response_size_complex_structure(self) -> None:
        """Test validation with complex nested structure."""
        complex_data = {
            "tasks": [
                {
                    "id": i,
                    "title": f"Task {i}",
                    "subtasks": [
                        {
                            "id": f"{i}-{j}",
                            "title": f"Subtask {j}",
                            "description": "a" * 500,
                        }
                        for j in range(5)
                    ],
                    "tags": ["important", "urgent", "backend"],
                }
                for i in range(10)
            ]
        }

        # Should pass for reasonable structure
        validate_response_size(complex_data)

    def test_validate_response_size_error_message(self) -> None:
        """Test that error message includes helpful information."""
        large_data = {
            "data": "a" * 100000  # 25000 tokens
        }

        with pytest.raises(ValueError) as exc_info:
            validate_response_size(large_data, max_tokens=15000)

        error_msg = str(exc_info.value)
        assert "25000" in error_msg  # Token count
        assert "15000" in error_msg  # Limit
        assert "summary mode" in error_msg  # Helpful suggestion
