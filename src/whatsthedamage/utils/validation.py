"""Common validation result types used across the application.

This module provides validation result types that can be used by both
CLI and web components without requiring web framework dependencies.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        is_valid: Whether validation passed
        error_message: Human-readable error message if validation failed
        error_code: Machine-readable error code for API responses
        details: Additional context about the validation failure
    """
    is_valid: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    @classmethod
    def success(cls) -> 'ValidationResult':
        """Create a successful validation result."""
        return cls(is_valid=True)

    @classmethod
    def failure(
        cls,
        error_message: str,
        error_code: str = 'VALIDATION_ERROR',
        details: Optional[Dict[str, Any]] = None
    ) -> 'ValidationResult':
        """Create a failed validation result."""
        return cls(
            is_valid=False,
            error_message=error_message,
            error_code=error_code,
            details=details or {}
        )


class ValidationError(Exception):
    """Exception raised when validation fails.

    This exception wraps a ValidationResult for easier error handling
    in contexts where exceptions are preferred over result objects.
    """
    def __init__(self, result: ValidationResult):
        self.result = result
        super().__init__(result.error_message)
