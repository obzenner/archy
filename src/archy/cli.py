"""
Main CLI interface for Archy architecture documentation generator.

This module provides the command-line interface using Typer, replacing the
bash scripts with a modern, type-safe Python CLI.
"""

from pathlib import Path
from typing import Optional

import json
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from . import __version__
from .core.analyzer import ArchitectureAnalyzer
from .core.config import AIBackend, ArchyConfig, MultiPRConfig
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
    extend: Optional[Path] = typer.Option(
        None,
        "--extend",
        help="Path to pattern file that extends the built-in create pattern",
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
                extend_pattern_path=extend,
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
    extend: Optional[Path] = typer.Option(
        None,
        "--extend",
        help="Path to pattern file that extends the built-in update pattern",
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
                extend_pattern_path=extend,
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
def distributed(
    prs: str = typer.Option(
        ...,
        "--prs",
        help="JSON specification of PRs to analyze (see help for format)",
    ),
    output: str = typer.Option(
        "distributed-arch.md",
        "-o",
        "--output",
        help="Output filename for distributed architecture documentation",
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
        help="Show what would be done without executing",
    ),
    save_prompt: bool = typer.Option(
        False,
        "--save-prompt", 
        help="Save generated prompt to file for debugging"
    ),
) -> None:
    """
    🌐 Analyze multiple PRs for distributed system architecture.
    
    This mode fetches PR diffs from multiple repositories using GitHub CLI (gh),
    analyzes cross-service interactions, and generates system-level architecture
    documentation focusing on service integration patterns.
    
    Example JSON format for --prs option:
    
    {
      "prs": [
        {
          "repo": "funnel-io/data-in-hatchery",
          "number": 4085,
          "description": "Add streaming pipeline"
        },
        {
          "repo": "funnel-io/web-app",
          "number": 1234,
          "focus_areas": ["ui", "state-management"]
        }
      ]
    }
    
    Requirements:
    - GitHub CLI (gh) must be installed and authenticated
    - Access to the specified repositories
    """
    try:
        console.print("🌐 Analyzing distributed system PRs...")
        
        # Parse and validate JSON
        try:
            prs_data = json.loads(prs)
            multi_pr_config = MultiPRConfig(**prs_data)
        except json.JSONDecodeError as e:
            console.print(f"[red]❌ Invalid JSON in --prs: {e}[/red]")
            console.print("\n[yellow]Expected format:[/yellow]")
            console.print('{"prs": [{"repo": "org/repo", "number": 123}]}')
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]❌ Invalid PR specification:[/red]")
            if hasattr(e, 'errors'):
                for error in e.errors():
                    field = " → ".join(str(x) for x in error["loc"])
                    console.print(f"  • {field}: {error['msg']}")
            else:
                console.print(f"  • {e}")
            raise typer.Exit(1)
        
        console.print(f"📊 Found {len(multi_pr_config.prs)} PRs to analyze:")
        for pr_spec in multi_pr_config.prs:
            service_name = pr_spec.repo.split('/')[-1]
            console.print(f"  • {service_name}: {pr_spec.repo}#{pr_spec.number}")
        
        # Create output path
        output_path = Path(output)
        
        # Run distributed system analysis
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("🔧 Initializing multi-PR analyzer...", total=None)
            
            # Create git repository for multi-PR analysis
            from .core.git_ops import GitRepository
            git_repo = GitRepository(Path("."), dry_run=dry_run)
            
            # Convert PR specs to dict format for git_ops
            pr_specs = [pr.model_dump() for pr in multi_pr_config.prs]
            
            # Analyze PRs
            progress.update(task, description="📡 Fetching PR diffs from GitHub...")
            multi_pr_analysis = git_repo.analyze_pull_requests(pr_specs)
            
            # Create distributed prompt
            progress.update(task, description="🧠 Creating distributed system prompt...")
            from .core.patterns import get_pattern_manager
            pattern_manager = get_pattern_manager()
            prompt = pattern_manager.create_distributed_prompt(multi_pr_analysis)
            
            # Save prompt if requested
            if save_prompt:
                prompt_file = output_path.with_suffix('.prompt.txt')
                prompt_file.write_text(prompt)
                console.print(f"[cyan]📝 Saved prompt to: {prompt_file}[/cyan]")
            
            # Generate documentation using AI backend
            progress.update(task, description=f"🤖 Generating distributed architecture with {backend.value}...")
            
            # Create AI backend
            from .backends.base import AIBackendConfig, get_backend
            
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
            
            if not dry_run and not ai_backend.is_available():
                console.print(f"[red]❌ Backend '{backend.value}' is not available[/red]")
                raise typer.Exit(1)
            
            # Generate documentation
            if dry_run:
                progress.update(task, description="🔍 Dry-run: Skipping AI generation...")
                console.print(f"[cyan]🔍 DRY-RUN: Would create {output_path}[/cyan]")
                console.print(f"[cyan]📊 Analysis: {multi_pr_analysis.total_services} services, {multi_pr_analysis.total_changes} changes[/cyan]")
                console.print("[green]✨ Mock distributed architecture analysis complete![/green]")
            else:
                response = ai_backend.generate(prompt)
                
                if response.success:
                    progress.update(task, description="💾 Saving distributed architecture...")
                    output_path.write_text(response.content)
                    console.print(f"[green]✅ Created: {output_path}[/green]")
                    console.print(f"[green]📊 Analyzed {multi_pr_analysis.total_services} services with {multi_pr_analysis.total_changes} total changes[/green]")
                else:
                    console.print(f"[red]❌ AI generation failed: {response.content}[/red]")
                    raise typer.Exit(1)
            
            progress.update(task, completed=True)
            
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
