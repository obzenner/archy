"""
Pattern loading and template management for Archy.

This module handles loading and processing the architecture analysis patterns
that are used to instruct AI backends on how to generate documentation.
"""

from pathlib import Path
from typing import Any, Optional

from ..exceptions import ArchyError


class PatternManager:
    """
    Manages loading and processing of architecture analysis patterns.

    Patterns are prompt templates that instruct AI backends on how to
    analyze codebases and generate architecture documentation.
    """

    def __init__(self, patterns_dir: Optional[Path] = None):
        """Initialize pattern manager with patterns directory."""
        if patterns_dir is None:
            # Default to patterns directory relative to script location
            current_dir = Path(__file__).parent
            self.patterns_dir = current_dir.parent.parent.parent / "patterns"
        else:
            self.patterns_dir = patterns_dir

        self._pattern_cache: dict[str, str] = {}

    def load_pattern(self, pattern_name: str) -> str:
        """
        Load a pattern template from the patterns directory.

        Args:
            pattern_name: Name of the pattern file (without .md extension)

        Returns:
            Pattern content as string

        Raises:
            ArchyError: If pattern file not found or cannot be read
        """
        # Check cache first
        if pattern_name in self._pattern_cache:
            return self._pattern_cache[pattern_name]

        pattern_file = self.patterns_dir / f"{pattern_name}.md"

        if not pattern_file.exists():
            raise ArchyError(f"Pattern file not found: {pattern_file}")

        try:
            with open(pattern_file, encoding="utf-8") as f:
                content = f.read()

            # Cache the pattern
            self._pattern_cache[pattern_name] = content
            return content

        except Exception as e:
            raise ArchyError(f"Failed to load pattern {pattern_name}: {e}") from e

    def get_create_pattern(self) -> str:
        """Get the pattern for creating fresh architecture documentation."""
        return self.load_pattern("create_design_document_pattern")

    def get_update_pattern(self) -> str:
        """Get the pattern for updating existing architecture documentation."""
        return self.load_pattern("update_arch_diagram_pattern")

    def create_fresh_prompt(
        self,
        project_name: str,
        analysis_target: Path,
        tracked_files: list[Path],
        directory_structure: str,
        git_info: dict[str, Any],
    ) -> str:
        """
        Create a complete prompt for fresh architecture analysis using the pattern template.

        The pattern file already contains all the instructions. We just append
        the actual codebase information that the AI should analyze.
        """
        pattern = self.get_create_pattern()

        # Build the actual codebase input as specified by the pattern's "# INPUT:" section
        codebase_input = f"""
Project Name: {project_name}
Analysis Target: {analysis_target}
Git Repository: {git_info.get("git_root", "Unknown")}
Current Branch: {git_info.get("current_branch", "Unknown")}
Default Branch: {git_info.get("default_branch", "main")}

Directory Structure:
```
{directory_structure}
```

Files to Analyze ({len(tracked_files)} total):
{chr(10).join(f"- {file}" for file in tracked_files[:50])}
{"..." if len(tracked_files) > 50 else ""}
"""

        # The pattern ends with "# INPUT:" - append our actual codebase data
        return f"{pattern}\n{codebase_input}"

    def create_update_prompt(
        self, existing_doc: str, changes_summary: str, git_info: dict[str, Any]
    ) -> str:
        """
        Create a complete prompt for updating architecture documentation using the pattern template.

        The pattern file already contains all the instructions. We just append
        the actual input data as specified by the pattern.
        """
        pattern = self.get_update_pattern()

        # Build the input as specified by the pattern's "# INPUT:" section
        # The pattern expects: 1. DESIGN DOCUMENT, 2. CODE CHANGES
        input_data = f"""
DESIGN DOCUMENT:

{existing_doc}

CODE CHANGES:

Git Information:
- Current Branch: {git_info.get("current_branch", "Unknown")}
- Default Branch: {git_info.get("default_branch", "main")}
- Git Repository: {git_info.get("git_root", "Unknown")}

{changes_summary}
"""

        # The pattern ends with "# INPUT:" - append our actual data
        return f"{pattern}\n{input_data}"


# Global pattern manager instance
pattern_manager = PatternManager()
