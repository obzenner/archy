"""
Main CLI interface for Archy architecture documentation generator.

This module provides the command-line interface using Typer, replacing the
bash scripts with a modern, type-safe Python CLI.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from . import __version__
from .core.analyzer import ArchitectureAnalyzer
from .core.config import AIBackend, ArchyConfig
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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate configuration and show what would be done without running analysis",
    ),
) -> None:
    """
    Create fresh architecture documentation from complete codebase analysis.

    This mode analyzes the entire codebase (respecting .gitignore) and generates
    comprehensive architecture documentation including C4 diagrams and design documents.
    """
    try:
        _print_command_header("Creating", "🏗️", project, folder, doc, backend, name)

        # Create configuration with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            # Step 1: Configuration
            task = progress.add_task("🔧 Initializing configuration...", total=None)
            config = ArchyConfig(
                project_path=project,
                subfolder=folder,
                arch_filename=doc,
                project_name=name,
                ai_backend=backend,
                fresh_mode=True,
                dry_run=dry_run,
            )
            progress.update(task, completed=True)

            # Step 2: Analysis setup
            progress.update(task, description="📊 Setting up analyzer...")
            analyzer = ArchitectureAnalyzer(config, progress=progress)
            analyzer._set_task(task)

            # Step 3: Run analysis (this will update progress internally)
            progress.update(
                task, description="🏗️ Generating architecture documentation..."
            )
            document = analyzer.analyze()

            # Step 4: Save (skip in dry-run mode)
            if config.dry_run:
                progress.update(task, description="🔍 Dry-run: Skipping file save...")
                console.print(
                    f"[cyan]🔍 DRY-RUN: Would create {document.file_path}[/cyan]"
                )
                console.print(
                    "[green]✨ Mock architecture document generated successfully![/green]"
                )
            else:
                progress.update(task, description="💾 Saving document...")
                document.save()
                console.print(f"[green]✅ Created: {document.file_path}[/green]")
            progress.update(task, completed=True)

    except ArchyError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1) from None


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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate configuration and show what would be done without running analysis",
    ),
) -> None:
    """
    Update architecture documentation based on git changes.

    This mode analyzes git changes since the last commit to the default branch
    and updates existing documentation or creates new documentation if none exists.
    """
    try:
        _print_command_header("Updating", "🔄", project, folder, doc, backend)

        # Create configuration with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            # Step 1: Configuration
            task = progress.add_task("🔧 Initializing configuration...", total=None)
            config = ArchyConfig(
                project_path=project,
                subfolder=folder,
                arch_filename=doc,
                ai_backend=backend,
                fresh_mode=False,  # Update mode
                dry_run=dry_run,
            )
            progress.update(task, completed=True)

            # Step 2: Analysis setup
            progress.update(task, description="📊 Setting up analyzer...")
            analyzer = ArchitectureAnalyzer(config, progress=progress)
            analyzer._set_task(task)

            # Step 3: Run analysis (this will update progress internally)
            progress.update(
                task, description="🔄 Updating architecture documentation..."
            )
            document = analyzer.analyze()

            # Step 4: Save (skip in dry-run mode)
            if config.dry_run:
                progress.update(task, description="🔍 Dry-run: Skipping file save...")
                console.print(
                    f"[cyan]🔍 DRY-RUN: Would update {document.file_path}[/cyan]"
                )
                console.print(
                    "[green]✨ Mock architecture document generated successfully![/green]"
                )
            else:
                progress.update(task, description="💾 Saving document...")
                document.save()
                console.print(f"[green]✅ Updated: {document.file_path}[/green]")
            progress.update(task, completed=True)

    except ArchyError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1) from None


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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Test configuration validation without calling AI backend",
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

        # Test the AI backend
        from .backends.base import AIBackendConfig, get_backend

        # Create the appropriate backend config with dry_run setting
        backend_config: AIBackendConfig
        if backend.value == "cursor-agent":
            from .backends.cursor_agent import CursorAgentConfig

            backend_config = CursorAgentConfig(dry_run=dry_run)
        elif backend.value == "fabric":
            from .backends.fabric import FabricConfig

            backend_config = FabricConfig(dry_run=dry_run)
        else:
            backend_config = AIBackendConfig(dry_run=dry_run)

        ai_backend = get_backend(backend.value, backend_config)

        # Check if backend is available
        if not ai_backend.is_available():
            console.print(f"[red]❌ Backend '{backend.value}' is not available[/red]")
            console.print(
                f"[yellow]💡 Make sure {backend.value} is installed and in your PATH[/yellow]"
            )
            raise typer.Exit(1) from None

        console.print(f"[green]✅ Backend '{backend.value}' is available[/green]")

        # Test connection (or dry-run)
        if dry_run:
            console.print("🔍 [cyan]DRY-RUN: Skipping actual backend test[/cyan]")
            console.print("[green]✅ Configuration test successful![/green]")
            console.print(
                f"[green]✨ Would send message to {backend.value} backend[/green]"
            )
        else:
            console.print("📡 Testing connection...")
            with console.status(
                f"Sending test message to {backend.value}...", spinner="dots"
            ):
                response = ai_backend.test_connection(message)

            if response.success:
                console.print("[green]✅ Test successful![/green]")
                console.print(
                    f"⏱️  Processing time: {response.processing_time:.2f}s"
                    if response.processing_time
                    else ""
                )
                console.print("\n📄 Response:")
                console.print(
                    f"[dim]{response.content[:200]}{'...' if len(response.content) > 200 else ''}[/dim]"
                )
            else:
                console.print(f"[red]❌ Test failed: {response.content}[/red]")
                raise typer.Exit(1) from None

    except ArchyError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1) from None


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
