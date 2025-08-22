"""
Core architecture analysis engine for Archy.

This module contains the main ArchitectureAnalyzer class that orchestrates
the analysis process, replacing the bash script's main functions.
"""

from pathlib import Path
from typing import Optional

from rich.progress import Progress, TaskID

from ..backends.base import AIBackendConfig, clean_architecture_response, get_backend
from ..exceptions import ArchyAIBackendError, ArchyError
from .config import ArchyConfig
from .git_ops import GitAnalysis, GitChange, GitRepository
from .patterns import pattern_manager


class ArchitectureDocument:
    """Represents a generated architecture document."""

    def __init__(self, content: str, file_path: Path):
        self.content = content
        self.file_path = file_path
        self.sections: dict[
            str, str
        ] = {}  # Will be populated when we parse the content

    def save(self) -> None:
        """Save the document to disk."""
        # Remove existing file to ensure correct filename case
        if self.file_path.exists():
            self.file_path.unlink()

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.content)


class ArchitectureAnalyzer:
    """
    Main architecture analysis engine.

    Replaces the bash script's main orchestration logic with a clean,
    object-oriented Python interface.
    """

    def __init__(self, config: ArchyConfig, progress: Optional[Progress] = None):
        """Initialize the analyzer with validated configuration."""
        self.config = config
        self.progress = progress
        self.current_task: Optional[TaskID] = None

        self.git_repo = GitRepository(config.project_path)
        self._git_analysis: Optional[GitAnalysis] = None

        # Initialize AI backend
        try:
            # Create the appropriate backend config with dry_run setting
            backend_config: AIBackendConfig
            if config.ai_backend.value == "cursor-agent":
                from ..backends.cursor_agent import CursorAgentConfig

                backend_config = CursorAgentConfig(dry_run=config.dry_run)
            elif config.ai_backend.value == "fabric":
                from ..backends.fabric import FabricConfig

                backend_config = FabricConfig(dry_run=config.dry_run)
            else:
                backend_config = AIBackendConfig(dry_run=config.dry_run)

            self.ai_backend = get_backend(config.ai_backend.value, backend_config)
        except Exception as e:
            raise ArchyError(
                f"Failed to initialize AI backend '{config.ai_backend}': {e}"
            ) from e

    @property
    def git_analysis(self) -> GitAnalysis:
        """Get git analysis, ensuring it's been initialized."""
        if self._git_analysis is None:
            raise ArchyError(
                "Git analysis not initialized - call generate_fresh() or update_from_changes() first"
            )
        return self._git_analysis

    @git_analysis.setter
    def git_analysis(self, value: GitAnalysis) -> None:
        """Set git analysis."""
        self._git_analysis = value

    def _update_progress(self, description: str) -> None:
        """Update progress if available."""
        if self.progress and self.current_task:
            self.progress.update(self.current_task, description=description)

    def _set_task(self, task_id: TaskID) -> None:
        """Set the current task for progress updates."""
        self.current_task = task_id

    def generate_fresh(self) -> ArchitectureDocument:
        """
        Generate fresh architecture documentation from complete codebase analysis.

        Replaces the bash generate_fresh_architecture() function.
        """
        # Step 1: Git analysis
        self._update_progress("📂 Analyzing git repository...")
        self.git_analysis = self.git_repo.analyze_repository(
            path_filter=self.config.path_filter,
            excluded_patterns=self.config.get_excluded_patterns(),
        )

        # Step 2: Directory structure
        self._update_progress("🌳 Generating directory structure...")
        directory_structure = self._get_directory_structure()

        # Step 3: Prepare git information
        self._update_progress("🔧 Preparing analysis data...")
        git_info = {
            "git_root": str(self.git_analysis.git_root),
            "current_branch": self.git_analysis.current_branch,
            "default_branch": self.git_analysis.default_branch,
        }

        # Step 4: Create the complete prompt
        self._update_progress("📋 Creating AI prompt from pattern template...")
        prompt = pattern_manager.create_fresh_prompt(
            project_name=self.config.project_name,  # type: ignore[arg-type]
            analysis_target=self.config.analysis_target_abs,  # type: ignore[arg-type]
            tracked_files=self.git_analysis.all_tracked_files,
            directory_structure=directory_structure,
            git_info=git_info,
        )

        # Step 5: Send prompt to AI backend
        self._update_progress(
            f"🤖 Calling {self.config.ai_backend.value} AI backend (this may take a while)..."
        )
        try:
            response = self.ai_backend.generate(prompt, force=False)

            if not response.success:
                raise ArchyAIBackendError(f"AI backend failed: {response.content}")

            # Step 6: Clean the response
            self._update_progress("🧹 Processing AI response...")
            cleaned_content = clean_architecture_response(response.content)

            return ArchitectureDocument(
                content=cleaned_content,
                file_path=self.config.arch_file_path,  # type: ignore[arg-type]
            )

        except ArchyAIBackendError as e:
            # If AI backend fails, save prompt for manual processing
            prompt_file = (
                self.config.arch_file_path.parent  # type: ignore[union-attr]
                / f"{self.config.arch_file_path.stem}_prompt.txt"  # type: ignore[union-attr,operator]
            )
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(prompt)

            error_content = f"""# Architecture Documentation for {self.config.project_name}

## Error: AI Backend Failed

**Error Details:**
{str(e)}

**Configuration:**
- Mode: Fresh (complete codebase analysis)
- Project: {self.config.project_name}
- Files Analyzed: {len(self.git_analysis.all_tracked_files)}
- AI Backend: {self.config.ai_backend}

**Fallback Action:**
The prompt has been saved to: {prompt_file}

You can manually process it with:
`{self.config.ai_backend.value} < {prompt_file}`

---
*Generated by Archy Python - AI Backend Error Fallback*
"""
            return ArchitectureDocument(
                content=error_content,
                file_path=self.config.arch_file_path,  # type: ignore[arg-type]
            )

    def _get_directory_structure(self) -> str:
        """Get directory structure representation."""
        try:
            import subprocess

            result = subprocess.run(
                [
                    "tree",
                    str(self.config.analysis_target_abs),
                    "-I",
                    "node_modules|.git|__pycache__|dist|build|target",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (
                result.stdout
                if result.returncode == 0
                else "Directory structure unavailable (tree command failed)"
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback if tree command not available
            return f"Directory listing:\n{self._simple_directory_listing()}"

    def _simple_directory_listing(self) -> str:
        """Simple directory listing fallback when tree is not available."""
        try:
            paths = []
            for file_path in self.git_analysis.all_tracked_files[:20]:
                paths.append(f"  {file_path}")
            if len(self.git_analysis.all_tracked_files) > 20:
                paths.append(
                    f"  ... and {len(self.git_analysis.all_tracked_files) - 20} more files"
                )
            return "\n".join(paths)
        except Exception:
            return "Directory listing unavailable"

    def update_from_changes(self) -> ArchitectureDocument:
        """
        Update architecture documentation based on git changes.

        Replaces the bash update_from_git_changes() function.
        """
        # Step 1: Get git analysis for changes
        self._update_progress("📂 Analyzing git repository for changes...")
        self.git_analysis = self.git_repo.analyze_repository(
            path_filter=self.config.path_filter,
            excluded_patterns=self.config.get_excluded_patterns(),
        )

        # Step 2: Check if there are any changes
        self._update_progress("🔍 Checking for relevant changes...")
        if not self.git_analysis.has_changes:
            # No changes detected - check if arch file exists
            if self.config.arch_file_path.exists():  # type: ignore[union-attr]
                raise ArchyError(
                    f"No relevant changes found between {self.git_analysis.default_branch} and {self.git_analysis.current_branch}. "
                    "Architecture file exists and is up to date."
                )
            else:
                # No changes and no existing file - fall back to fresh mode
                self._update_progress(
                    "📄 No changes found, falling back to fresh analysis..."
                )
                return self.generate_fresh()

        # Step 3: Analyze the changes
        self._update_progress("📊 Summarizing changes...")
        changes_summary = self._summarize_changes(self.git_analysis.changed_files)

        # Step 4: Check if existing architecture file exists
        self._update_progress("📄 Checking for existing architecture file...")
        if self.config.arch_file_path.exists():  # type: ignore[union-attr]
            # Update existing file
            self._update_progress("🔄 Updating existing architecture file...")
            return self._update_existing_architecture(changes_summary)
        else:
            # Create new file based on changes
            self._update_progress("🏗️ Creating new architecture file from changes...")
            return self._create_from_changes(changes_summary)

    def _summarize_changes(self, changes: list[GitChange]) -> str:
        """Create a summary of git changes for analysis."""
        if not changes:
            return "No changes detected."

        summary_lines = [
            "## Git Changes Summary",
            "",
            f"**Total Files Changed:** {len(changes)}",
            "",
            "**Changes by Type:**",
        ]

        # Group by change type
        by_type: dict[str, list[GitChange]] = {}
        for change in changes:
            if change.change_type not in by_type:
                by_type[change.change_type] = []
            by_type[change.change_type].append(change)

        for change_type, change_list in by_type.items():
            summary_lines.append(f"- {change_type.title()}: {len(change_list)} files")

        summary_lines.extend(["", "**Detailed Changes:**"])

        for change in changes[:10]:  # Limit to first 10 for brevity
            summary_lines.append(
                f"- {change.change_type.title()}: {change.file_path} "
                f"(+{change.lines_added}/-{change.lines_removed})"
            )

        if len(changes) > 10:
            summary_lines.append(f"... and {len(changes) - 10} more files")

        return "\n".join(summary_lines)

    def _update_existing_architecture(
        self, changes_summary: str
    ) -> ArchitectureDocument:
        """Update existing architecture file with changes using pattern template."""
        # Read existing content
        try:
            with open(self.config.arch_file_path, encoding="utf-8") as f:  # type: ignore[arg-type]
                existing_content = f.read()
        except Exception as e:
            raise ArchyError(f"Failed to read existing architecture file: {e}") from e

        # Prepare git information for pattern
        git_info = {
            "git_root": str(self.git_analysis.git_root),
            "current_branch": self.git_analysis.current_branch,
            "default_branch": self.git_analysis.default_branch,
        }

        # Create the complete prompt using update pattern template
        prompt = pattern_manager.create_update_prompt(
            existing_doc=existing_content,
            changes_summary=changes_summary,
            git_info=git_info,
        )

        # Send prompt to AI backend and get response
        try:
            response = self.ai_backend.generate(
                prompt, force=True
            )  # Use force for updates

            if not response.success:
                raise ArchyAIBackendError(f"AI backend failed: {response.content}")

            # Clean the response to extract architecture content
            cleaned_content = clean_architecture_response(response.content)

            return ArchitectureDocument(
                content=cleaned_content,
                file_path=self.config.arch_file_path,  # type: ignore[arg-type]
            )

        except ArchyAIBackendError as e:
            # If AI backend fails, save prompt for manual processing
            prompt_file = (
                self.config.arch_file_path.parent  # type: ignore[union-attr]
                / f"{self.config.arch_file_path.stem}_update_prompt.txt"  # type: ignore[union-attr,operator]
            )
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(prompt)

            error_content = f"""# Architecture Documentation for {self.config.project_name}

## Error: AI Backend Update Failed

**Error Details:**
{str(e)}

**Configuration:**
- Mode: Update (existing architecture + git changes)
- Project: {self.config.project_name}
- Changes: {len(self.git_analysis.changed_files)} files modified
- AI Backend: {self.config.ai_backend}

**Changes Summary:**
{changes_summary}

**Fallback Action:**
The update prompt has been saved to: {prompt_file}

You can manually process it with:
`{self.config.ai_backend.value} < {prompt_file}`

---
*Generated by Archy Python - AI Backend Error Fallback*
"""
            return ArchitectureDocument(
                content=error_content,
                file_path=self.config.arch_file_path,  # type: ignore[arg-type]
            )

    def _create_from_changes(self, changes_summary: str) -> ArchitectureDocument:
        """Create new architecture file based on changes using pattern template."""
        # When creating from changes, we use the create pattern but focus on changed files
        directory_structure = self._get_directory_structure()

        # Focus on changed files rather than all tracked files
        changed_file_paths = [
            change.file_path for change in self.git_analysis.changed_files
        ]

        # Prepare git information for pattern
        git_info = {
            "git_root": str(self.git_analysis.git_root),
            "current_branch": self.git_analysis.current_branch,
            "default_branch": self.git_analysis.default_branch,
        }

        # Create the complete prompt using create pattern template (focused on changes)
        prompt = pattern_manager.create_fresh_prompt(
            project_name=self.config.project_name,  # type: ignore[arg-type]
            analysis_target=self.config.analysis_target_abs,  # type: ignore[arg-type]
            tracked_files=changed_file_paths,  # Focus on changed files only
            directory_structure=directory_structure,
            git_info=git_info,
        )

        # Add changes context to the prompt
        enhanced_prompt = f"""{prompt}

## FOCUS ON RECENT CHANGES

**IMPORTANT**: This analysis should focus on the recent git changes shown below, as no existing architecture document was found:

{changes_summary}

Use the changed files and directory structure to understand the system architecture and create appropriate C4 diagrams.
"""

        # Send prompt to AI backend and get response
        try:
            response = self.ai_backend.generate(enhanced_prompt, force=False)

            if not response.success:
                raise ArchyAIBackendError(f"AI backend failed: {response.content}")

            # Clean the response to extract architecture content
            cleaned_content = clean_architecture_response(response.content)

            return ArchitectureDocument(
                content=cleaned_content,
                file_path=self.config.arch_file_path,  # type: ignore[arg-type]
            )

        except ArchyAIBackendError as e:
            # If AI backend fails, save prompt for manual processing
            prompt_file = (
                self.config.arch_file_path.parent  # type: ignore[union-attr]
                / f"{self.config.arch_file_path.stem}_create_from_changes_prompt.txt"  # type: ignore[union-attr,operator]
            )
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(enhanced_prompt)

            error_content = f"""# Architecture Documentation for {self.config.project_name}

## Error: AI Backend Creation Failed

**Error Details:**
{str(e)}

**Configuration:**
- Mode: Create from Changes (no existing architecture)
- Project: {self.config.project_name}
- Changes: {len(self.git_analysis.changed_files)} files modified
- AI Backend: {self.config.ai_backend}

**Changes Summary:**
{changes_summary}

**Fallback Action:**
The creation prompt has been saved to: {prompt_file}

You can manually process it with:
`{self.config.ai_backend.value} < {prompt_file}`

---
*Generated by Archy Python - AI Backend Error Fallback*
"""
            return ArchitectureDocument(
                content=error_content,
                file_path=self.config.arch_file_path,  # type: ignore[arg-type]
            )

    def analyze(self) -> ArchitectureDocument:
        """
        Main analysis entry point - routes to fresh or update mode.

        Replaces the bash main() function logic.
        """
        if self.config.fresh_mode:
            return self.generate_fresh()
        else:
            return self.update_from_changes()
