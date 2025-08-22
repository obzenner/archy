"""
Fabric AI backend for Archy.

This module implements the Fabric AI integration, which uses the
fabric-ai CLI tool for AI-powered architecture analysis with local models.
"""

import time
from typing import Optional

from ..exceptions import ArchyAIBackendError
from .base import AIBackend, AIBackendConfig, AIResponse


class FabricConfig(AIBackendConfig):
    """Configuration specific to Fabric AI backend."""

    model: Optional[str] = None  # Let fabric use its default model
    redirect_stderr: bool = True  # Whether to redirect stderr to avoid noise


class FabricBackend(AIBackend):
    """
    Fabric AI backend implementation.

    Integrates with the fabric-ai CLI tool to generate architecture documentation
    using local AI models. Based on the bash implementation: echo "prompt" | fabric-ai
    """

    def __init__(self, config: Optional[FabricConfig] = None):
        """Initialize Fabric AI backend."""
        super().__init__(config or FabricConfig())
        self.fabric_config = config or FabricConfig()

    def is_available(self) -> bool:
        """Check if fabric-ai command is available."""
        # In dry-run mode, always return True to avoid external command dependencies
        if self.config.dry_run:
            return True
            
        try:
            # Try to run fabric-ai with --version or --help
            result = self._run_command(["fabric-ai", "--help"], timeout=10)
            return result.returncode == 0
        except ArchyAIBackendError:
            try:
                # Fallback: try just running fabric-ai (some versions might not have --help)
                result = self._run_command(["fabric-ai"], input_text="test", timeout=5)
                # fabric-ai might return non-zero even when working, check if command exists
                return "command not found" not in result.stderr.lower()
            except ArchyAIBackendError:
                return False

    def generate(self, prompt: str, force: bool = False) -> AIResponse:
        """
        Generate architecture documentation using fabric-ai.

        Args:
            prompt: Complete prompt including pattern + codebase data
            force: Not used for fabric (included for interface compatibility)

        Returns:
            AIResponse with generated content
        """
        start_time = time.time()

        # Return mock response if in dry-run mode
        if self.config.dry_run:
            return self._create_mock_response(prompt)

        try:
            # Build fabric-ai command
            cmd = ["fabric-ai"]

            # Add model if specified
            if self.fabric_config.model:
                cmd.extend(["--model", self.fabric_config.model])

            # Execute fabric-ai with prompt as stdin
            result = self._run_command(
                cmd, input_text=prompt, timeout=self.config.timeout
            )

            processing_time = time.time() - start_time

            # fabric-ai might return non-zero exit code even on success
            # Check for actual error conditions
            if result.returncode != 0:
                stderr_lower = result.stderr.lower() if result.stderr else ""
                if any(
                    error in stderr_lower
                    for error in ["error", "failed", "not found", "invalid"]
                ):
                    error_msg = (
                        result.stderr.strip()
                        if result.stderr
                        else f"fabric-ai failed (exit code {result.returncode})"
                    )
                    raise ArchyAIBackendError(f"fabric-ai error: {error_msg}")

            # Get the response content
            content = result.stdout.strip()

            if not content:
                # Check if there's useful info in stderr
                if result.stderr and "Error:" not in result.stderr:
                    content = result.stderr.strip()
                else:
                    raise ArchyAIBackendError("fabric-ai returned empty response")

            # Check for explicit error messages in output
            if content.startswith("Error:") or "Failed to call fabric-ai" in content:
                raise ArchyAIBackendError(f"fabric-ai error: {content}")

            return AIResponse(
                content=content,
                success=True,
                backend="fabric-ai",
                processing_time=processing_time,
                metadata={
                    "command": f"fabric-ai{f' --model {self.fabric_config.model}' if self.fabric_config.model else ''}",
                    "exit_code": result.returncode,
                    "model": self.fabric_config.model or "default",
                },
            )

        except ArchyAIBackendError:
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            return AIResponse(
                content=f"fabric-ai error: {e}",
                success=False,
                backend="fabric-ai",
                processing_time=processing_time,
                metadata={"error": str(e)},
            )

    def test_connection(
        self,
        test_message: str = "Hello from Archy! Please respond with a simple test message.",
    ) -> AIResponse:
        """Test fabric-ai with a simple message."""
        try:
            # In dry-run mode, return mock response immediately  
            if self.config.dry_run:
                return AIResponse(
                    content="Mock test response from fabric-ai (dry-run mode)",
                    success=True,
                    backend="fabric-ai",
                    processing_time=0.1,
                    metadata={"mock": True, "dry_run": True},
                )
                
            if not self.is_available():
                return AIResponse(
                    content="fabric-ai command not found. Install from: https://github.com/danielmiessler/fabric",
                    success=False,
                    backend="fabric-ai",
                    metadata={"error": "command_not_found"},
                )

            return self.generate(test_message)

        except Exception as e:
            return AIResponse(
                content=f"fabric-ai test failed: {e}",
                success=False,
                backend="fabric-ai",
                metadata={"error": str(e)},
            )
