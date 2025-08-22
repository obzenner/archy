"""
Main CLI interface for Archy architecture documentation generator.

This module provides the command-line interface using Typer, replacing the
bash scripts with a modern, type-safe Python CLI.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from . import __version__
from .exceptions import ArchyError

# Create the main Typer app
app = typer.Typer(
    name="archy",
    help="🏛️ AI-powered architecture documentation generator",
    epilog="For more information, visit: https://github.com/your-org/archy-repo",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Rich console for better output
console = Console()


class AIBackend(str, Enum):
    """Supported AI backend options."""
    
    CURSOR_AGENT = "cursor-agent"
    FABRIC = "fabric"


@app.command()
def fresh(
    project: Path = typer.Argument(
        Path("."),
        help="Path to the git project directory",
        show_default=True,
    ),
    folder: Optional[str] = typer.Option(
        None,
        "-f",
        "--folder",
        help="Subfolder to focus analysis on",
    ),
    doc: str = typer.Option(
        "arch.md",
        "-d",
        "--doc",
        help="Architecture document filename",
        show_default=True,
    ),
    name: Optional[str] = typer.Option(
        None,
        "-n",
        "--name", 
        help="Project name (auto-detected if not provided)",
    ),
    backend: AIBackend = typer.Option(
        AIBackend.CURSOR_AGENT,
        "-t",
        "--tool",
        help="AI backend to use for generation",
        show_default=True,
    ),
) -> None:
    """
    Create fresh architecture documentation from complete codebase analysis.
    
    This mode analyzes the entire codebase (respecting .gitignore) and generates
    comprehensive architecture documentation including C4 diagrams and design documents.
    """
    try:
        _print_command_header("Creating", "🏗️", project, folder, doc, backend, name)
        
        # TODO: Import and use ArchitectureAnalyzer once implemented
        console.print("[yellow]⚠️  Fresh mode implementation pending...[/yellow]")
        console.print(f"Would create: {project / (folder or '.') / doc}")
        
    except ArchyError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def update(
    project: Path = typer.Argument(
        Path("."),
        help="Path to the git project directory", 
        show_default=True,
    ),
    folder: Optional[str] = typer.Option(
        None,
        "-f",
        "--folder",
        help="Subfolder to focus analysis on",
    ),
    doc: str = typer.Option(
        "arch.md",
        "-d", 
        "--doc",
        help="Architecture document filename",
        show_default=True,
    ),
    backend: AIBackend = typer.Option(
        AIBackend.CURSOR_AGENT,
        "-t",
        "--tool",
        help="AI backend to use for generation",
        show_default=True,
    ),
) -> None:
    """
    Update architecture documentation based on git changes.
    
    This mode analyzes git changes since the last commit to the default branch
    and updates existing documentation or creates new documentation if none exists.
    """
    try:
        _print_command_header("Updating", "🔄", project, folder, doc, backend)
        
        # TODO: Import and use ArchitectureAnalyzer once implemented  
        console.print("[yellow]⚠️  Update mode implementation pending...[/yellow]")
        console.print(f"Would update: {project / (folder or '.') / doc}")
        
    except ArchyError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def test(
    backend: AIBackend = typer.Option(
        AIBackend.CURSOR_AGENT,
        "-t",
        "--tool",
        help="AI backend to test",
        show_default=True,
    ),
    message: str = typer.Argument(
        "Hello from Archy! Please respond with a simple test message.",
        help="Custom test message to send to the AI backend",
    ),
) -> None:
    """
    Test AI backend connectivity and functionality.
    
    Sends a simple test message to the specified AI backend to verify
    it's working correctly and accessible.
    """
    try:
        console.print(f"🧪 Testing {backend.value} backend...")
        console.print(f"📝 Message: {message}")
        
        # TODO: Import and use AI backend testing once implemented
        console.print("[yellow]⚠️  Backend testing implementation pending...[/yellow]")
        console.print("✅ Test would be run here")
        
    except ArchyError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    table = Table(title="Archy Version Information")
    table.add_column("Component", style="cyan")
    table.add_column("Version", style="green")
    
    table.add_row("Archy", __version__)
    table.add_row("Python Implementation", "Modern CLI rewrite")
    
    console.print(table)


def _print_command_header(
    action: str,
    icon: str, 
    project: Path,
    folder: Optional[str],
    doc: str,
    backend: AIBackend,
    name: Optional[str] = None,
) -> None:
    """Print a formatted command execution header."""
    console.print(f"{icon} {action} architecture documentation...")
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Project:", str(project.resolve()))
    table.add_row("Folder:", folder or "(root)")
    table.add_row("File:", doc)
    table.add_row("AI Backend:", backend.value)
    
    if name:
        table.add_row("Name:", name)
    else:
        table.add_row("Name:", "(auto-detect)")
    
    console.print(table)
    console.print()


if __name__ == "__main__":
    app()
