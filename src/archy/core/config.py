"""
Configuration models and validation for Archy.

This module replaces the bash configuration and validation logic with
type-safe Pydantic models and comprehensive security checks.
"""

import os
import re
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings

from ..exceptions import ArchyConfigError, ArchyGitError, ArchySecurityError


class AIBackend(str, Enum):
    """Supported AI backend options."""

    CURSOR_AGENT = "cursor-agent"
    FABRIC = "fabric"


class ArchyConfig(BaseModel):
    """
    Main configuration model for Archy operations.

    Replaces all the bash validation and path setup logic with type-safe
    validation and comprehensive security checks.
    """

    # Core parameters
    project_path: Path = Field(
        default=Path("."), description="Path to the git project directory"
    )
    subfolder: Optional[str] = Field(
        default=None, description="Subfolder to focus analysis on"
    )
    arch_filename: str = Field(
        default="arch.md", description="Architecture document filename"
    )
    project_name: Optional[str] = Field(
        default=None, description="Project name (auto-detected if not provided)"
    )
    ai_backend: AIBackend = Field(
        default=AIBackend.CURSOR_AGENT, description="AI backend to use for generation"
    )
    fresh_mode: bool = Field(
        default=False,
        description="Whether to use fresh mode (full analysis) vs update mode",
    )
    dry_run: bool = Field(
        default=False, description="Run in dry-run mode with mock AI responses"
    )
    extend_pattern_path: Optional[Path] = Field(
        default=None,
        description="Path to pattern file that extends the built-in pattern",
    )

    # Derived paths (computed after validation)
    project_path_abs: Optional[Path] = Field(default=None, exclude=True)
    analysis_target_abs: Optional[Path] = Field(default=None, exclude=True)
    git_root: Optional[Path] = Field(default=None, exclude=True)
    arch_file_path: Optional[Path] = Field(default=None, exclude=True)
    path_filter: Optional[str] = Field(default=None, exclude=True)
    default_branch: Optional[str] = Field(default=None, exclude=True)

    # Security and validation constants
    MAX_PATH_LENGTH: int = Field(default=4096, exclude=True)
    BLOCKED_SYSTEM_DIRS: list[str] = Field(
        default=["/etc", "/sys", "/proc", "/dev", "/boot", "/root"], exclude=True
    )
    EXCLUDED_PATTERNS: list[str] = Field(
        default=[
            # Lock files
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "Pipfile.lock",
            "poetry.lock",
            "Cargo.lock",
            "composer.lock",
            "Gemfile.lock",
            "go.sum",
            # Build artifacts & minified files
            "*.min.js",
            "*.min.css",
            "*.bundle.js",
            "*.bundle.css",
            "*.pyc",
            "*.class",
            "*.o",
            "*.so",
            "*.dll",
            "*.exe",
        ],
        exclude=True,
    )

    @field_validator("project_path")
    @classmethod
    def validate_project_path(cls, v: Path) -> Path:
        """Validate project path for security and existence."""
        path_str = str(v)

        # Security: Check for path traversal attacks
        if ".." in path_str or path_str.startswith("/"):
            if any(
                blocked in path_str
                for blocked in ["/etc", "/sys", "/proc", "/dev", "/boot", "/root"]
            ):
                raise ArchySecurityError(
                    f"Access to system directory not allowed: {path_str}"
                )

            # Allow relative paths with .. if they don't go to system dirs
            if re.search(r"\.\..*/", path_str):
                resolved = Path(path_str).resolve()
                if any(
                    str(resolved).startswith(blocked)
                    for blocked in ["/etc", "/sys", "/proc", "/dev", "/boot", "/root"]
                ):
                    raise ArchySecurityError(
                        f"Resolved path accesses system directory: {resolved}"
                    )

        # Security: Check path length
        if len(path_str) > 4096:
            raise ArchySecurityError(f"Path too long (>{4096} chars): {path_str}")

        return v

    @field_validator("subfolder")
    @classmethod
    def validate_subfolder(cls, v: Optional[str]) -> Optional[str]:
        """Validate subfolder for security."""
        if v is None:
            return v

        # Security: Check for path traversal
        if ".." in v or v.startswith("/"):
            raise ArchySecurityError(f"Path traversal detected in subfolder: {v}")

        # Security: Only allow safe characters
        if not re.match(r"^[a-zA-Z0-9._/-]+$", v):
            raise ArchySecurityError(f"Invalid characters in subfolder: {v}")

        return v

    @field_validator("arch_filename")
    @classmethod
    def validate_arch_filename(cls, v: str) -> str:
        """Validate filename for security."""
        # Security: Only allow safe characters
        if not re.match(r"^[a-zA-Z0-9._-]+$", v):
            raise ArchySecurityError(f"Invalid characters in filename: {v}")

        return v

    @field_validator("extend_pattern_path")
    @classmethod
    def validate_extend_pattern_path(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate extension pattern path for existence."""
        if v is None:
            return v

        # Convert to absolute path for validation
        try:
            abs_path = v.resolve()
            if not abs_path.exists():
                raise ArchyConfigError(f"Extension pattern file not found: {v}")
            if not abs_path.is_file():
                raise ArchyConfigError(f"Extension pattern path is not a file: {v}")
        except Exception as e:
            if isinstance(e, ArchyConfigError):
                raise
            raise ArchyConfigError(f"Invalid extension pattern path: {v}") from e

        return v

    @model_validator(mode="after")
    def setup_paths_and_git_context(self) -> "ArchyConfig":
        """
        Set up all derived paths and git context after basic validation.

        This replaces the bash setup_paths() and setup_git_context() functions.
        """
        # Convert to absolute path and verify existence
        try:
            self.project_path_abs = self.project_path.resolve()
            if not self.project_path_abs.exists():
                raise ArchyConfigError(
                    f"Project path does not exist: {self.project_path}"
                )
        except Exception as e:
            raise ArchyConfigError(f"Invalid project path: {self.project_path}") from e

        # Determine analysis target
        if self.subfolder:
            self.analysis_target_abs = self.project_path_abs / self.subfolder
            if not self.analysis_target_abs.exists():
                raise ArchyConfigError(f"Subfolder does not exist: {self.subfolder}")
        else:
            self.analysis_target_abs = self.project_path_abs

        # Auto-detect project name if not provided
        if not self.project_name:
            self.project_name = self.analysis_target_abs.name

        # Find git repository root
        self.git_root = self._find_git_root(self.analysis_target_abs)
        if not self.git_root:
            raise ArchyConfigError(f"Not a git repository: {self.analysis_target_abs}")

        # Set up path filter for git operations
        if self.analysis_target_abs != self.git_root:
            # Get relative path from git root for filtering
            relative_path = self.analysis_target_abs.relative_to(self.git_root)
            self.path_filter = str(relative_path) + "/"
        else:
            self.path_filter = ""

        # Detect default branch
        self.default_branch = self._detect_default_branch(self.git_root)

        # Construct final architecture file path
        self.arch_file_path = self.analysis_target_abs / self.arch_filename

        # Validate write permissions
        self._validate_write_permissions(self.arch_file_path)

        return self

    def _find_git_root(self, start_path: Path) -> Optional[Path]:
        """Find the git repository root using GitRepository."""
        try:
            # Import here to avoid circular imports
            from .git_ops import GitRepository

            git_repo = GitRepository(start_path)
            return git_repo.git_root
        except ArchyGitError:
            return None

    def _detect_default_branch(self, git_root: Path) -> str:
        """Detect the default branch name using GitRepository."""
        try:
            # Import here to avoid circular imports
            from .git_ops import GitRepository

            git_repo = GitRepository(git_root)
            return git_repo.get_default_branch()
        except ArchyGitError:
            return "main"  # Fallback

    def _validate_write_permissions(self, filepath: Path) -> None:
        """Validate that we can write to the target file location."""
        dir_path = filepath.parent

        # Check if directory is writable
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ArchyConfigError(f"Cannot create directory: {dir_path}") from e

        if not os.access(dir_path, os.W_OK):
            raise ArchyConfigError(f"Cannot write to directory: {dir_path}")

        # If file exists, check if it's writable
        if filepath.exists() and not os.access(filepath, os.W_OK):
            raise ArchyConfigError(f"Cannot overwrite existing file: {filepath}")

    def get_excluded_patterns(self) -> list[str]:
        """Get the list of file patterns to exclude from analysis."""
        return self.EXCLUDED_PATTERNS

    def should_exclude_file(self, file_path: str) -> bool:
        """Check if a file should be excluded based on patterns."""
        for pattern in self.EXCLUDED_PATTERNS:
            if pattern in file_path:
                return True
        return False


class ArchySettings(BaseSettings):
    """
    Environment-based settings for Archy.

    Automatically loads from environment variables with ARCHY_ prefix.
    """

    ai_backend: AIBackend = Field(
        default=AIBackend.CURSOR_AGENT, description="Default AI backend to use"
    )
    max_file_size: int = Field(
        default=10_000_000, description="Maximum file size to analyze (10MB)"
    )
    temp_dir_prefix: str = Field(
        default="archy", description="Prefix for temporary directories"
    )

    model_config = {
        "env_prefix": "ARCHY_",
        "case_sensitive": False,
    }


class PRSpec(BaseModel):
    """Specification for a single pull request to analyze."""

    repo: str = Field(..., description="Repository in format 'org/repo'")
    number: int = Field(..., gt=0, description="PR number")
    branch: Optional[str] = Field(None, description="Target branch (optional)")
    description: Optional[str] = Field(None, description="Custom description")
    focus_areas: List[str] = Field(
        default_factory=list, description="Areas to focus analysis on"
    )

    @field_validator("repo")
    @classmethod
    def validate_repo_format(cls, v: str) -> str:
        """Ensure repo is in 'org/repo' format."""
        if "/" not in v or len(v.split("/")) != 2:
            raise ValueError("Repository must be in format 'org/repo'")

        org, repo_name = v.split("/")
        if not org or not repo_name:
            raise ValueError("Both organization and repository name must be non-empty")

        return v


class MultiPRConfig(BaseModel):
    """Configuration for multi-PR distributed system analysis."""

    prs: List[PRSpec] = Field(..., min_length=1, description="List of PRs to analyze")

    @model_validator(mode="after")
    def validate_unique_prs(self):
        """Ensure no duplicate repo#number combinations."""
        seen = set()
        for pr_spec in self.prs:
            key = f"{pr_spec.repo}#{pr_spec.number}"
            if key in seen:
                raise ValueError(f"Duplicate PR specification: {key}")
            seen.add(key)
        return self


# Global settings instance
settings = ArchySettings()
