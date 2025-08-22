"""
Cursor Agent AI backend for Archy.

This module implements the Cursor Agent integration, which uses the
cursor-agent CLI tool for AI-powered architecture analysis.
"""

import json
import time
from typing import Optional

from ..exceptions import ArchyAIBackendError
from .base import AIBackend, AIBackendConfig, AIResponse


class CursorAgentConfig(AIBackendConfig):
    """Configuration specific to Cursor Agent backend."""

    output_format: str = "json"
    use_force_flag: bool = True  # Whether to use --force for updates


class CursorAgentBackend(AIBackend):
    """
    Cursor Agent AI backend implementation.

    Integrates with the cursor-agent CLI tool to generate architecture documentation.
    Based on the bash implementation: cursor-agent -p --output-format json
    """

    def __init__(self, config: Optional[CursorAgentConfig] = None):
        """Initialize Cursor Agent backend."""
        super().__init__(config or CursorAgentConfig())
        self.cursor_config = config or CursorAgentConfig()

    def is_available(self) -> bool:
        """Check if cursor-agent command is available."""
        try:
            result = self._run_command(["cursor-agent", "--version"], timeout=10)
            return result.returncode == 0
        except ArchyAIBackendError:
            return False

    def generate(self, prompt: str, force: bool = False) -> AIResponse:
        """
        Generate architecture documentation using cursor-agent.

        Args:
            prompt: Complete prompt including pattern + codebase data
            force: Whether to use --force flag (for updates)

        Returns:
            AIResponse with generated content
        """
        start_time = time.time()

        # Return mock response if in dry-run mode
        if self.config.dry_run:
            return self._create_mock_response(prompt)

        try:
            # Build cursor-agent command
            cmd = ["cursor-agent", "-p"]

            # Add output format
            cmd.extend(["--output-format", self.cursor_config.output_format])

            # Add force flag if requested
            if force and self.cursor_config.use_force_flag:
                cmd.append("--force")

            # Add the prompt as the final argument
            cmd.append(prompt)

            # Execute cursor-agent
            result = self._run_command(cmd, timeout=self.config.timeout)

            processing_time = time.time() - start_time

            if result.returncode != 0:
                error_msg = (
                    result.stderr.strip()
                    if result.stderr
                    else "Unknown cursor-agent error"
                )
                raise ArchyAIBackendError(
                    f"cursor-agent failed (exit code {result.returncode}): {error_msg}"
                )

            # Parse JSON response
            try:
                response_data = json.loads(result.stdout)
                content = response_data.get("result", result.stdout.strip())
            except json.JSONDecodeError:
                # Fallback: use raw stdout if not valid JSON
                content = result.stdout.strip()

            if not content:
                raise ArchyAIBackendError("cursor-agent returned empty response")

            return AIResponse(
                content=content,
                success=True,
                backend="cursor-agent",
                processing_time=processing_time,
                metadata={
                    "command": " ".join(cmd[:-1] + ["<prompt>"]),  # Hide prompt in logs
                    "exit_code": result.returncode,
                    "force_used": force and self.cursor_config.use_force_flag,
                },
            )

        except ArchyAIBackendError:
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            return AIResponse(
                content=f"cursor-agent error: {e}",
                success=False,
                backend="cursor-agent",
                processing_time=processing_time,
                metadata={"error": str(e)},
            )

    def test_connection(
        self,
        test_message: str = "Hello from Archy! Please respond with a simple test message.",
    ) -> AIResponse:
        """Test cursor-agent with a simple message."""
        try:
            if not self.is_available():
                return AIResponse(
                    content="cursor-agent command not found. Install from: https://cursor.com/cli",
                    success=False,
                    backend="cursor-agent",
                    metadata={"error": "command_not_found"},
                )

            return self.generate(test_message)

        except Exception as e:
            return AIResponse(
                content=f"cursor-agent test failed: {e}",
                success=False,
                backend="cursor-agent",
                metadata={"error": str(e)},
            )
