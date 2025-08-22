"""
Base AI backend interface and configuration for Archy.

This module provides the abstract base class and configuration models
for different AI backends (cursor-agent, fabric, etc.).
"""

import subprocess
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..exceptions import ArchyAIBackendError


class AIBackendConfig(BaseModel):
    """Base configuration for AI backends."""

    timeout: int = Field(
        default=300, description="Timeout for AI backend calls in seconds"
    )
    max_retries: int = Field(default=2, description="Maximum number of retry attempts")
    dry_run: bool = Field(
        default=False, description="Return mock responses without calling AI services"
    )


class AIResponse(BaseModel):
    """Standardized AI backend response."""

    content: str
    success: bool
    backend: str
    processing_time: Optional[float] = None
    tokens_used: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIBackend(ABC):
    """
    Abstract base class for AI backends.

    All AI backends (cursor-agent, fabric, etc.) must implement this interface.
    """

    def __init__(self, config: Optional[AIBackendConfig] = None):
        """Initialize AI backend with configuration."""
        self.config = config or AIBackendConfig()
        self.name = self.__class__.__name__

    def _create_mock_response(self, prompt: str) -> AIResponse:
        """Create a mock response for dry-run mode."""

        mock_content = """# Architecture Documentation

## System Overview

This is a **mock architecture document** generated in dry-run mode.

## Context Diagram

```mermaid
C4Context
    title System Context Diagram

    System(MockSystem, "Mock System", "Generated for dry-run testing")
    Person(User, "User", "System user")

    Rel(User, MockSystem, "Uses")
```

## Container Diagram

```mermaid
C4Container
    title Container Diagram

    Container(WebApp, "Web Application", "React", "User interface")
    Container(API, "API Gateway", "Node.js", "API layer")
    Container(Database, "Database", "PostgreSQL", "Data storage")

    Rel(WebApp, API, "Makes API calls")
    Rel(API, Database, "Reads/writes data")
```

## Deployment Diagram

```mermaid
C4Deployment
    title Deployment Diagram

    Deployment_Node(AWS, "AWS Cloud", "Amazon Web Services"){
        Container(WebApp, "Web App", "React")
        Container(API, "API", "Node.js")
        Container(DB, "Database", "PostgreSQL")
    }
```

---
*This document was generated in dry-run mode for testing purposes.*
"""

        return AIResponse(
            content=mock_content,
            success=True,
            backend=self.name,
            processing_time=0.1,  # Fast mock response
            tokens_used=150,
            metadata={"mock": True, "dry_run": True},
        )

    @abstractmethod
    def generate(self, prompt: str, force: bool = False) -> AIResponse:
        """
        Generate architecture documentation from prompt.

        Args:
            prompt: Complete prompt including pattern + codebase data
            force: Whether to force generation (for updates)

        Returns:
            AIResponse with generated content

        Raises:
            ArchyAIBackendError: If backend call fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI backend is available and properly configured."""
        pass

    def test_connection(
        self,
        test_message: str = "Hello from Archy! Please respond with a simple test message.",
    ) -> AIResponse:
        """Test the AI backend with a simple message."""
        try:
            return self.generate(test_message)
        except Exception as e:
            return AIResponse(
                content=f"Test failed: {e}",
                success=False,
                backend=self.name,
                metadata={"error": str(e)},
            )

    def _run_command(
        self,
        cmd: list[str],
        input_text: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> subprocess.CompletedProcess[str]:
        """
        Run a command with proper error handling and timeout.

        Args:
            cmd: Command and arguments as list
            input_text: Optional text to send to stdin
            timeout: Optional timeout override

        Returns:
            CompletedProcess result

        Raises:
            ArchyAIBackendError: If command fails
        """
        if timeout is None:
            timeout = self.config.timeout

        try:
            result = subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,  # Don't raise on non-zero exit
            )
            return result
        except subprocess.TimeoutExpired as e:
            raise ArchyAIBackendError(
                f"Backend '{self.name}' timed out after {timeout}s"
            ) from e
        except FileNotFoundError as e:
            raise ArchyAIBackendError(f"Backend command not found: {cmd[0]}") from e
        except Exception as e:
            raise ArchyAIBackendError(
                f"Backend '{self.name}' execution failed: {e}"
            ) from e


def get_backend(
    backend_name: str, config: Optional[AIBackendConfig] = None
) -> AIBackend:
    """
    Factory function to get AI backend by name.

    Args:
        backend_name: Name of the backend ('cursor-agent', 'fabric')
        config: Optional backend configuration

    Returns:
        Configured AI backend instance

    Raises:
        ArchyAIBackendError: If backend not found or cannot be created
    """
    from .cursor_agent import CursorAgentBackend
    from .fabric import FabricBackend

    backends = {"cursor-agent": CursorAgentBackend, "fabric": FabricBackend}

    if backend_name not in backends:
        raise ArchyAIBackendError(
            f"Unknown backend: {backend_name}. Available: {list(backends.keys())}"
        )

    try:
        backend_class = backends[backend_name]
        return backend_class(config)
    except Exception as e:
        raise ArchyAIBackendError(
            f"Failed to create backend '{backend_name}': {e}"
        ) from e


def clean_architecture_response(raw_response: str) -> str:
    """
    Clean AI response to extract only architecture content.

    Removes AI thinking process and extracts content from "## BUSINESS POSTURE" onwards.
    """
    if not raw_response.strip():
        return "No response from AI backend"

    # Look for business posture section (various formats)
    markers = [
        "## BUSINESS POSTURE",
        "# BUSINESS POSTURE",
        "##BUSINESS POSTURE",
        "#BUSINESS POSTURE",
    ]

    for marker in markers:
        if marker in raw_response:
            # Find the marker and extract everything after it
            marker_pos = raw_response.find(marker)
            if marker_pos != -1:
                # Get the line that contains the marker
                lines = raw_response[marker_pos:].split("\n")
                # Reconstruct from the marker line onwards
                cleaned_lines = [marker] + lines[1:] if lines[0] != marker else lines
                return "\n".join(cleaned_lines).strip()

    # If no marker found, try to remove common AI prefixes

    lines = raw_response.split("\n")
    cleaned_lines = []
    skip_thinking = True

    for line in lines:
        # Look for the start of actual content
        if line.strip().startswith("#") or any(
            section in line for section in ["BUSINESS", "SECURITY", "DESIGN", "RISK"]
        ):
            skip_thinking = False

        if not skip_thinking:
            cleaned_lines.append(line)

    if cleaned_lines:
        return "\n".join(cleaned_lines).strip()

    # Fallback: return original response
    return raw_response.strip()
