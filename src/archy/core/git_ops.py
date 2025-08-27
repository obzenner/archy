"""
Git operations for Archy using GitPython.

This module replaces all bash git commands with proper Python GitPython calls,
providing better error handling and cross-platform compatibility.
"""

import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from git import InvalidGitRepositoryError, Repo

from ..exceptions import ArchyGitError


class ChangeType(str, Enum):
    """Types of git changes."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class GitChange:
    """Represents a single git file change."""

    file_path: Path
    change_type: ChangeType
    lines_added: int = 0
    lines_removed: int = 0
    old_path: Optional[Path] = None  # For renames


@dataclass
class GitAnalysis:
    """Results of git analysis for architecture generation."""

    changed_files: list[GitChange]
    all_tracked_files: list[Path]
    default_branch: str
    current_branch: str
    git_root: Path
    total_changes: int
    has_changes: bool


@dataclass
class PRChange:
    """Represents a single file change in a PR."""
    
    file_path: str
    change_type: str  # "Modified", "Added", "Deleted", "Renamed"
    lines_added: int = 0
    lines_removed: int = 0
    pr_number: int = 0
    repo: str = ""  # "funnel-io/data-in-hatchery"
    old_path: Optional[Path] = None  # For renames


@dataclass
class PRDiff:
    """Complete diff from a single PR."""
    
    repo: str  # "funnel-io/data-in-hatchery" 
    number: int  # 4085
    changes: list[PRChange]  # All file changes in this PR
    total_changes: int
    summary: str  # Brief description
    description: str = ""  # Optional detailed description
    focus_areas: list[str] = None  # Optional focus areas
    raw_diff: str = ""  # Full PR diff content for AI analysis
    
    def __post_init__(self):
        if self.focus_areas is None:
            self.focus_areas = []
            
    @property
    def service_name(self) -> str:
        """Derive service name from repo name."""
        return self.repo.split('/')[-1]


@dataclass  
class MultiPRAnalysis:
    """Results of multi-PR distributed system analysis."""
    
    pr_diffs: List[PRDiff]
    total_services: int
    total_changes: int
    cross_service_patterns: Dict[str, List[str]]
    service_interactions: Dict[str, Dict[str, List[str]]]


class GitRepository:
    """
    Git operations wrapper using GitPython.

    Replaces bash git commands with proper Python API calls.
    """

    def __init__(self, path: Path, dry_run: bool = False):
        """Initialize git repository interface."""
        self.path = path
        self.dry_run = dry_run
        self._repo: Optional[Repo] = None
        self._git_root: Optional[Path] = None
        self._default_branch: Optional[str] = None

        if not dry_run:
            self._initialize_repo()
        else:
            # In dry-run mode, create mock git setup
            self._git_root = path
            # Don't initialize actual repo

    def _initialize_repo(self) -> None:
        """Initialize the git repository and find root."""
        try:
            # Find git repository root starting from given path
            current = self.path.resolve()
            while current != current.parent:
                if (current / ".git").exists():
                    self._git_root = current
                    self._repo = Repo(current)
                    break
                current = current.parent

            if not self._repo:
                raise ArchyGitError(f"Not a git repository: {self.path}")

        except InvalidGitRepositoryError as e:
            raise ArchyGitError(f"Invalid git repository: {self.path}") from e
        except Exception as e:
            raise ArchyGitError(f"Git initialization failed: {e}") from e

    @property
    def repo(self) -> Repo:
        """Get the GitPython repository object."""
        if self.dry_run:
            raise ArchyGitError("Git operations not available in dry-run mode")
        if not self._repo:
            raise ArchyGitError("Repository not initialized")
        return self._repo

    @property
    def git_root(self) -> Path:
        """Get the git repository root path."""
        if not self._git_root:
            raise ArchyGitError("Git root not found")
        return self._git_root

    def get_default_branch(self) -> str:
        """
        Detect the default branch name.

        Replaces bash: git symbolic-ref refs/remotes/origin/HEAD
        """
        if self._default_branch:
            return self._default_branch

        try:
            branch_name = "main"  # Default fallback

            # Try to get the default branch from origin/HEAD
            try:
                origin_head = self.repo.refs["origin/HEAD"]
                branch_name = origin_head.reference.name.split("/")[-1]
            except (KeyError, AttributeError):
                # Fallback: check common default branches
                for candidate in ["main", "master", "develop"]:
                    try:
                        if f"refs/heads/{candidate}" in [
                            ref.name for ref in self.repo.refs
                        ]:
                            branch_name = candidate
                            break
                    except Exception:
                        continue
                else:
                    # Final fallback: use current branch
                    try:
                        branch_name = self.repo.active_branch.name
                    except Exception:
                        branch_name = "main"  # Ultimate fallback

            self._default_branch = branch_name
            return branch_name

        except Exception as e:
            raise ArchyGitError(f"Failed to detect default branch: {e}") from e

    def get_current_branch(self) -> str:
        """Get the current branch name."""
        try:
            return self.repo.active_branch.name
        except Exception as e:
            raise ArchyGitError(f"Failed to get current branch: {e}") from e

    def get_changed_files(
        self, base_branch: Optional[str] = None, path_filter: Optional[str] = None
    ) -> list[GitChange]:
        """
        Get files changed between base branch and current HEAD.

        Replaces bash: git diff --name-only "$DEFAULT_BRANCH...HEAD"
        """
        if not base_branch:
            base_branch = self.get_default_branch()

        try:
            changes = []

            # Get the diff between base branch and HEAD
            try:
                base_commit = self.repo.commit(f"origin/{base_branch}")
            except Exception:
                # Fallback to local branch if origin doesn't exist
                try:
                    base_commit = self.repo.commit(base_branch)
                except Exception:
                    # If branch doesn't exist, compare with HEAD~1
                    try:
                        base_commit = self.repo.commit("HEAD~1")
                    except Exception:
                        # Very first commit - no changes to analyze
                        return []

            head_commit = self.repo.head.commit

            # Get the diff
            diff = base_commit.diff(head_commit)

            for item in diff:
                path_str = item.a_path or item.b_path
                if not path_str:
                    continue  # Skip items with no path
                file_path = Path(path_str)

                # Apply path filter if specified
                if path_filter and not str(file_path).startswith(path_filter):
                    continue

                # Determine change type
                if item.new_file:
                    change_type = ChangeType.ADDED
                elif item.deleted_file:
                    change_type = ChangeType.DELETED
                elif item.renamed_file:
                    change_type = ChangeType.RENAMED
                else:
                    change_type = ChangeType.MODIFIED

                # Calculate line changes (simplified)
                lines_added = 0
                lines_removed = 0
                try:
                    if item.diff:
                        if isinstance(item.diff, bytes):
                            diff_text = item.diff.decode("utf-8", errors="ignore")
                        else:
                            diff_text = str(item.diff)
                        for line in diff_text.split("\n"):
                            if line.startswith("+") and not line.startswith("+++"):
                                lines_added += 1
                            elif line.startswith("-") and not line.startswith("---"):
                                lines_removed += 1
                except Exception:
                    # If we can't decode diff, just mark as having changes
                    lines_added = 1

                change = GitChange(
                    file_path=file_path,
                    change_type=change_type,
                    lines_added=lines_added,
                    lines_removed=lines_removed,
                    old_path=(
                        Path(item.a_path) if item.renamed_file and item.a_path else None
                    ),
                )
                changes.append(change)

            return changes

        except Exception as e:
            raise ArchyGitError(f"Failed to get changed files: {e}") from e

    def get_all_tracked_files(self, path_filter: Optional[str] = None) -> list[Path]:
        """
        Get all tracked files in the repository.

        Replaces bash: git ls-files
        """
        try:
            # Get all tracked files
            tracked_files = []

            for item in self.repo.git.ls_files().split("\n"):
                if not item.strip():
                    continue

                file_path = Path(item.strip())

                # Apply path filter if specified
                if path_filter and not str(file_path).startswith(path_filter):
                    continue

                # Check if file actually exists (might be deleted but still tracked)
                full_path = self.git_root / file_path
                if full_path.exists():
                    tracked_files.append(file_path)

            return tracked_files

        except Exception as e:
            raise ArchyGitError(f"Failed to get tracked files: {e}") from e

    def filter_excluded_patterns(
        self, files: list[Path], excluded_patterns: list[str]
    ) -> list[Path]:
        """
        Filter out files matching excluded patterns.

        Replaces bash pattern filtering logic.
        """
        filtered = []

        for file_path in files:
            file_str = str(file_path)
            should_exclude = False

            for pattern in excluded_patterns:
                # Simple pattern matching - could be enhanced with fnmatch
                if pattern in file_str:
                    should_exclude = True
                    break

            if not should_exclude:
                filtered.append(file_path)

        return filtered

    def analyze_repository(
        self,
        path_filter: Optional[str] = None,
        excluded_patterns: Optional[list[str]] = None,
    ) -> GitAnalysis:
        """
        Perform complete git analysis for architecture generation.

        Combines all git operations needed for both fresh and update modes.
        """
        if excluded_patterns is None:
            excluded_patterns = []

        # In dry-run mode, return mock git analysis
        if self.dry_run:
            return GitAnalysis(
                changed_files=[],
                all_tracked_files=[self.path / "mock_file.py"],
                default_branch="main",
                current_branch="main",
                git_root=self._git_root or self.path,
                total_changes=0,
                has_changes=False,
            )

        try:
            # Get basic git info
            default_branch = self.get_default_branch()
            current_branch = self.get_current_branch()

            # Get changed files for update mode
            changed_files = self.get_changed_files(default_branch, path_filter)

            # Filter excluded patterns from changes
            filtered_changes = []
            for change in changed_files:
                if not any(
                    pattern in str(change.file_path) for pattern in excluded_patterns
                ):
                    filtered_changes.append(change)

            # Get all tracked files for fresh mode
            all_tracked = self.get_all_tracked_files(path_filter)
            all_tracked_filtered = self.filter_excluded_patterns(
                all_tracked, excluded_patterns
            )

            return GitAnalysis(
                changed_files=filtered_changes,
                all_tracked_files=all_tracked_filtered,
                default_branch=default_branch,
                current_branch=current_branch,
                git_root=self.git_root,
                total_changes=len(filtered_changes),
                has_changes=len(filtered_changes) > 0,
            )

        except Exception as e:
            raise ArchyGitError(f"Git analysis failed: {e}") from e

    def get_commit_info(self, commit_hash: Optional[str] = None) -> dict[str, Any]:
        """Get information about a specific commit (default: HEAD)."""
        try:
            commit = (
                self.repo.head.commit
                if not commit_hash
                else self.repo.commit(commit_hash)
            )

            return {
                "hash": commit.hexsha[:8],
                "message": commit.message.strip(),
                "author": str(commit.author),
                "date": commit.committed_datetime.isoformat(),
                "files_changed": len(list(commit.stats.files.keys())),
            }
        except Exception as e:
            raise ArchyGitError(f"Failed to get commit info: {e}") from e

    def analyze_pull_requests(self, pr_specs: List[dict]) -> MultiPRAnalysis:
        """
        Analyze multiple PRs from different repositories for distributed system patterns.
        
        Args:
            pr_specs: List of dicts with keys: repo, number, description?, focus_areas?
            
        Returns:
            MultiPRAnalysis with aggregated cross-service patterns
        """
        if self.dry_run:
            return MultiPRAnalysis(
                pr_diffs=[
                    PRDiff(
                        repo="mock/service-1",
                        number=123,
                        changes=[],
                        total_changes=0,
                        summary="Mock PR for testing",
                        raw_diff="# Mock diff content for testing"
                    )
                ],
                total_services=1,
                total_changes=0,
                cross_service_patterns={},
                service_interactions={}
            )
        
        pr_diffs = []
        excluded_patterns = self._get_excluded_file_patterns()
        
        for pr_spec in pr_specs:
            repo = pr_spec["repo"]
            number = pr_spec["number"]
            description = pr_spec.get("description", "")
            focus_areas = pr_spec.get("focus_areas", [])
            
            try:
                # Fetch PR diff using gh CLI
                diff_content = self._fetch_pr_diff(repo, number)
                
                # Parse the diff into structured data
                pr_diff = self._parse_pr_diff(
                    diff_content, repo, number, 
                    description, focus_areas, excluded_patterns
                )
                pr_diffs.append(pr_diff)
            except ArchyGitError as e:
                # If PR fetch fails, create a minimal PRDiff with error info
                pr_diff = PRDiff(
                    repo=repo,
                    number=number,
                    changes=[],
                    total_changes=0,
                    summary=f"Failed to fetch PR: {e}",
                    description=description,
                    focus_areas=focus_areas,
                    raw_diff=""
                )
                pr_diffs.append(pr_diff)
        
        # Analyze cross-service patterns
        cross_service_patterns = self._detect_cross_service_patterns(pr_diffs)
        service_interactions = self._detect_service_interactions(pr_diffs)
        
        return MultiPRAnalysis(
            pr_diffs=pr_diffs,
            total_services=len(set(pr_diff.service_name for pr_diff in pr_diffs)),
            total_changes=sum(pr_diff.total_changes for pr_diff in pr_diffs),
            cross_service_patterns=cross_service_patterns,
            service_interactions=service_interactions
        )

    def _get_excluded_file_patterns(self) -> List[str]:
        """
        Get patterns for files that should be excluded from architectural analysis.
        These files typically don't provide valuable insights for system architecture.
        """
        return [
            # Lock files and dependency manifests
            r'.*\.lock$',
            r'yarn\.lock$', 
            r'package-lock\.json$',
            r'Pipfile\.lock$',
            r'poetry\.lock$',
            r'Gemfile\.lock$',
            r'composer\.lock$',
            r'go\.sum$',
            r'Cargo\.lock$',
            
            # Generated/compiled files
            r'.*\.min\.(js|css)$',
            r'.*\.bundle\.(js|css)$',
            r'.*\.d\.ts$',  # TypeScript declaration files
            r'.*\.map$',  # Source maps
            r'.*\.pyc$',
            r'.*\.pyo$',
            r'.*\.class$',
            r'.*\.o$',
            r'.*\.so$',
            r'.*\.dll$',
            
            # Note: We DO want swagger/openapi files for architectural analysis!
            
            # Binary/media files
            r'.*\.(png|jpg|jpeg|gif|ico|svg|pdf|zip|tar|gz)$',
            
            # IDE and editor files  
            r'.*\.(vscode|idea|eclipse)/.*',
            r'.*\.swp$',
            r'.*\.tmp$',
            
            # Test snapshots and fixtures
            r'.*/__snapshots__/.*',
            r'.*/fixtures/.*\.json$',
            r'.*/mocks/.*\.json$',
        ]

    def _fetch_pr_diff(self, repo: str, pr_number: int) -> str:
        """Fetch PR diff using GitHub CLI."""
        try:
            cmd = ["gh", "pr", "diff", str(pr_number), "-R", repo]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=30  # 30 second timeout
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise ArchyGitError(f"Failed to fetch PR {repo}#{pr_number}: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise ArchyGitError(f"Timeout fetching PR {repo}#{pr_number}")
        except FileNotFoundError:
            raise ArchyGitError("GitHub CLI (gh) not found. Please install it.")

    def _parse_pr_diff(
        self, 
        diff_content: str, 
        repo: str, 
        number: int, 
        description: str,
        focus_areas: List[str],
        excluded_patterns: List[str]
    ) -> PRDiff:
        """Parse git diff output into structured PRChange objects."""
        changes = []
        
        # Split diff by file changes (each starts with "diff --git")
        file_diffs = re.split(r'^diff --git', diff_content, flags=re.MULTILINE)
        
        for file_diff in file_diffs[1:]:  # Skip first empty split
            if not file_diff.strip():
                continue
                
            # Extract file paths
            file_match = re.match(r' a/(.*?) b/(.*?)$', file_diff.split('\n')[0])
            if not file_match:
                continue
                
            file_path = file_match.group(2)  # Use the "after" path
            old_path = file_match.group(1) if file_match.group(1) != file_match.group(2) else None
            
            # Skip excluded files
            if self._should_exclude_file(file_path, excluded_patterns):
                continue
            
            # Determine change type
            if file_diff.startswith(" /dev/null"):
                change_type = "Added"
            elif "/dev/null b/" in file_diff.split('\n')[0]:
                change_type = "Deleted"  
            elif old_path:
                change_type = "Renamed"
            else:
                change_type = "Modified"
            
            # Count lines added/removed
            lines_added = len(re.findall(r'^\+[^+]', file_diff, re.MULTILINE))
            lines_removed = len(re.findall(r'^-[^-]', file_diff, re.MULTILINE))
            
            changes.append(PRChange(
                file_path=file_path,
                change_type=change_type,
                lines_added=lines_added,
                lines_removed=lines_removed,
                pr_number=number,
                repo=repo,
                old_path=Path(old_path) if old_path else None
            ))
        
        service_name = repo.split('/')[-1]  # Extract service name from repo
        summary = f"Changes in {service_name}: {len(changes)} files modified"
        if description:
            summary = f"{description} ({len(changes)} files)"
            
        return PRDiff(
            repo=repo,
            number=number,
            changes=changes,
            total_changes=len(changes),
            summary=summary,
            description=description,
            focus_areas=focus_areas,
            raw_diff=diff_content  # Store the full diff content
        )

    def _should_exclude_file(self, file_path: str, excluded_patterns: List[str]) -> bool:
        """Check if file should be excluded from architectural analysis."""
        for pattern in excluded_patterns:
            if re.match(pattern, file_path, re.IGNORECASE):
                return True
        return False
    
    def _detect_cross_service_patterns(self, pr_diffs: List[PRDiff]) -> Dict[str, List[str]]:
        """Detect API calls, shared DBs, events across services."""
        patterns = {}
        
        # Look for API endpoints, database changes, etc.
        api_endpoints = []
        api_specifications = []
        database_changes = []
        config_changes = []
        
        for pr_diff in pr_diffs:
            service_name = pr_diff.service_name
            
            for change in pr_diff.changes:
                file_path = change.file_path.lower()
                
                # API Specifications (HIGH PRIORITY for distributed systems)
                if any(keyword in file_path for keyword in ['swagger', 'openapi', 'api-docs']) or file_path.endswith('.json') and 'api' in file_path:
                    lines_info = f"(+{change.lines_added}/-{change.lines_removed})" if change.lines_added or change.lines_removed else ""
                    api_specifications.append(f"{service_name}: {change.file_path} {lines_info}")
                
                # API endpoints and routes
                elif any(keyword in file_path for keyword in ['api', 'router', 'controller', 'endpoint', 'route']):
                    api_endpoints.append(f"{service_name}: {change.file_path}")
                
                # Database changes  
                elif any(keyword in file_path for keyword in ['model', 'schema', 'migration', 'db', 'sql']):
                    database_changes.append(f"{service_name}: {change.file_path}")
                
                # Config changes
                elif any(keyword in file_path for keyword in ['config', 'env', 'setting', 'constant']):
                    config_changes.append(f"{service_name}: {change.file_path}")
        
        # Prioritize API specifications first (most important for distributed systems)
        if api_specifications:
            patterns["api_specifications"] = api_specifications
        if api_endpoints:
            patterns["api_endpoints"] = api_endpoints
        if database_changes:
            patterns["database_changes"] = database_changes  
        if config_changes:
            patterns["config_changes"] = config_changes
            
        return patterns

    def _detect_service_interactions(self, pr_diffs: List[PRDiff]) -> Dict[str, Dict[str, List[str]]]:
        """Detect service-to-service interactions from code changes."""
        interactions = {}
        
        for pr_diff in pr_diffs:
            service_name = pr_diff.service_name
            service_interactions = {}
            
            # Analyze diff content for service calls
            for other_pr in pr_diffs:
                if other_pr.service_name == service_name:
                    continue
                    
                other_service = other_pr.service_name
                calls = []
                
                # Look for references to other services in the diff
                for change in pr_diff.changes:
                    if other_service.lower() in change.file_path.lower():
                        calls.append(f"File reference: {change.file_path}")
                
                # Look in raw diff content for API calls, imports, etc.
                if other_service.lower() in pr_diff.raw_diff.lower():
                    calls.append(f"Code references to {other_service}")
                
                if calls:
                    service_interactions[other_service] = calls
            
            if service_interactions:
                interactions[service_name] = service_interactions
                
        return interactions
