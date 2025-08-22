"""
Custom exceptions for Archy architecture documentation generator.

Provides specific exception types for different error categories to enable
better error handling and user experience.
"""

from typing import Optional


class ArchyError(Exception):
    """Base exception for all Archy-related errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ArchyConfigError(ArchyError):
    """Raised when configuration is invalid or incomplete."""

    pass


class ArchyGitError(ArchyError):
    """Raised when git operations fail or repository is invalid."""

    pass


class ArchySecurityError(ArchyError):
    """Raised when security validation fails (path traversal, etc.)."""

    pass


class ArchyAIBackendError(ArchyError):
    """Raised when AI backend operations fail."""

    pass


class ArchyFileError(ArchyError):
    """Raised when file operations fail."""

    pass


class ArchyValidationError(ArchyError):
    """Raised when input validation fails."""

    pass
