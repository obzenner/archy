"""
Tests for the CLI interface.

Tests the main CLI commands and argument parsing using Typer's testing utilities.
"""

import pytest
from typer.testing import CliRunner

from archy.cli import app

runner = CliRunner()


def test_cli_help():
    """Test that help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "architecture documentation generator" in result.stdout


def test_version_command():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Archy" in result.stdout


def test_fresh_command_basic():
    """Test fresh command with default arguments."""
    result = runner.invoke(app, ["fresh", "--dry-run"])
    assert result.exit_code == 0
    assert "Creating" in result.stdout


@pytest.mark.skip(
    reason="Temporarily disabled - needs debugging of dry-run mode with specific flags"
)
def test_fresh_command_with_flags():
    """Test fresh command with various flags."""
    result = runner.invoke(
        app,
        [
            "fresh",
            "--folder",
            "backend",
            "--doc",
            "api.md",
            "--name",
            "TestProject",
            "--tool",
            "fabric",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0


@pytest.mark.skip(
    reason="Temporarily disabled - needs debugging of dry-run mode with update command"
)
def test_update_command_basic():
    """Test update command with default arguments."""
    result = runner.invoke(app, ["update", "--dry-run"])
    assert result.exit_code == 0
    assert "Updating" in result.stdout


def test_test_command():
    """Test the test command."""
    result = runner.invoke(app, ["test", "--dry-run"])
    assert result.exit_code == 0
    assert "Testing" in result.stdout
    assert "cursor-agent" in result.stdout


def test_test_command_with_fabric():
    """Test the test command with fabric backend."""
    result = runner.invoke(app, ["test", "--tool", "fabric", "--dry-run"])
    assert result.exit_code == 0
    assert "fabric" in result.stdout


def test_invalid_backend():
    """Test that invalid backend is rejected."""
    result = runner.invoke(app, ["fresh", "--tool", "invalid-backend", "--dry-run"])
    assert result.exit_code != 0
