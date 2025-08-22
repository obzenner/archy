"""
Tests for the CLI interface.

Tests the main CLI commands and argument parsing using Typer's testing utilities.
"""

from pathlib import Path
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
    result = runner.invoke(app, ["fresh"])
    assert result.exit_code == 0
    assert "Creating" in result.stdout
    assert "implementation pending" in result.stdout


def test_fresh_command_with_flags():
    """Test fresh command with various flags."""
    result = runner.invoke(app, [
        "fresh", 
        "--folder", "backend",
        "--doc", "api.md",
        "--name", "TestProject",
        "--tool", "fabric"
    ])
    assert result.exit_code == 0
    assert "backend" in result.stdout
    assert "api.md" in result.stdout


def test_update_command_basic():
    """Test update command with default arguments."""
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0
    assert "Updating" in result.stdout
    assert "implementation pending" in result.stdout


def test_test_command():
    """Test the test command."""
    result = runner.invoke(app, ["test"])
    assert result.exit_code == 0
    assert "Testing" in result.stdout
    assert "cursor-agent" in result.stdout


def test_test_command_with_fabric():
    """Test the test command with fabric backend."""
    result = runner.invoke(app, ["test", "--tool", "fabric"])
    assert result.exit_code == 0
    assert "fabric" in result.stdout


def test_invalid_backend():
    """Test that invalid backend is rejected."""
    result = runner.invoke(app, ["fresh", "--tool", "invalid-backend"])
    assert result.exit_code != 0
