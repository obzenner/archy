"""
Git operations for Archy using GitPython.

This module replaces all bash git commands with proper Python GitPython calls,
providing better error handling and cross-platform compatibility.
"""

from pathlib import Path
from typing import List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

import git
from git import Repo, InvalidGitRepositoryError

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
    changed_files: List[GitChange]
    all_tracked_files: List[Path]
    default_branch: str
    current_branch: str
    git_root: Path
    total_changes: int
    has_changes: bool


class GitRepository:
    """
    Git operations wrapper using GitPython.
    
    Replaces bash git commands with proper Python API calls.
    """
    
    def __init__(self, path: Path):
        """Initialize git repository interface."""
        self.path = path
        self._repo = None
        self._git_root = None
        self._default_branch = None
        
        self._initialize_repo()
    
    def _initialize_repo(self) -> None:
        """Initialize the git repository and find root."""
        try:
            # Find git repository root starting from given path
            current = self.path.resolve()
            while current != current.parent:
                if (current / '.git').exists():
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
            # Try to get the default branch from origin/HEAD
            try:
                origin_head = self.repo.refs['origin/HEAD']
                self._default_branch = origin_head.reference.name.split('/')[-1]
                return self._default_branch
            except (KeyError, AttributeError):
                pass
            
            # Fallback: check common default branches
            for branch_name in ['main', 'master', 'develop']:
                try:
                    if f'refs/heads/{branch_name}' in [ref.name for ref in self.repo.refs]:
                        self._default_branch = branch_name
                        return self._default_branch
                except Exception:
                    continue
            
            # Final fallback: use current branch
            try:
                self._default_branch = self.repo.active_branch.name
                return self._default_branch
            except Exception:
                self._default_branch = 'main'  # Ultimate fallback
                return self._default_branch
                
        except Exception as e:
            raise ArchyGitError(f"Failed to detect default branch: {e}") from e
    
    def get_current_branch(self) -> str:
        """Get the current branch name."""
        try:
            return self.repo.active_branch.name
        except Exception as e:
            raise ArchyGitError(f"Failed to get current branch: {e}") from e
    
    def get_changed_files(self, base_branch: Optional[str] = None, 
                         path_filter: Optional[str] = None) -> List[GitChange]:
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
                base_commit = self.repo.commit(f'origin/{base_branch}')
            except Exception:
                # Fallback to local branch if origin doesn't exist
                try:
                    base_commit = self.repo.commit(base_branch)
                except Exception:
                    # If branch doesn't exist, compare with HEAD~1
                    try:
                        base_commit = self.repo.commit('HEAD~1')
                    except Exception:
                        # Very first commit - no changes to analyze
                        return []
            
            head_commit = self.repo.head.commit
            
            # Get the diff
            diff = base_commit.diff(head_commit)
            
            for item in diff:
                file_path = Path(item.a_path if item.a_path else item.b_path)
                
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
                        diff_text = item.diff.decode('utf-8', errors='ignore')
                        for line in diff_text.split('\n'):
                            if line.startswith('+') and not line.startswith('+++'):
                                lines_added += 1
                            elif line.startswith('-') and not line.startswith('---'):
                                lines_removed += 1
                except Exception:
                    # If we can't decode diff, just mark as having changes
                    lines_added = 1
                
                change = GitChange(
                    file_path=file_path,
                    change_type=change_type,
                    lines_added=lines_added,
                    lines_removed=lines_removed,
                    old_path=Path(item.a_path) if item.renamed_file and item.a_path else None
                )
                changes.append(change)
            
            return changes
            
        except Exception as e:
            raise ArchyGitError(f"Failed to get changed files: {e}") from e
    
    def get_all_tracked_files(self, path_filter: Optional[str] = None) -> List[Path]:
        """
        Get all tracked files in the repository.
        
        Replaces bash: git ls-files
        """
        try:
            # Get all tracked files
            tracked_files = []
            
            for item in self.repo.git.ls_files().split('\n'):
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
    
    def filter_excluded_patterns(self, files: List[Path], 
                                excluded_patterns: List[str]) -> List[Path]:
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
    
    def analyze_repository(self, path_filter: Optional[str] = None,
                          excluded_patterns: Optional[List[str]] = None) -> GitAnalysis:
        """
        Perform complete git analysis for architecture generation.
        
        Combines all git operations needed for both fresh and update modes.
        """
        if excluded_patterns is None:
            excluded_patterns = []
        
        try:
            # Get basic git info
            default_branch = self.get_default_branch()
            current_branch = self.get_current_branch()
            
            # Get changed files for update mode
            changed_files = self.get_changed_files(default_branch, path_filter)
            
            # Filter excluded patterns from changes
            filtered_changes = []
            for change in changed_files:
                if not any(pattern in str(change.file_path) for pattern in excluded_patterns):
                    filtered_changes.append(change)
            
            # Get all tracked files for fresh mode
            all_tracked = self.get_all_tracked_files(path_filter)
            all_tracked_filtered = self.filter_excluded_patterns(all_tracked, excluded_patterns)
            
            return GitAnalysis(
                changed_files=filtered_changes,
                all_tracked_files=all_tracked_filtered,
                default_branch=default_branch,
                current_branch=current_branch,
                git_root=self.git_root,
                total_changes=len(filtered_changes),
                has_changes=len(filtered_changes) > 0
            )
            
        except Exception as e:
            raise ArchyGitError(f"Git analysis failed: {e}") from e
    
    def get_commit_info(self, commit_hash: Optional[str] = None) -> dict:
        """Get information about a specific commit (default: HEAD)."""
        try:
            commit = self.repo.head.commit if not commit_hash else self.repo.commit(commit_hash)
            
            return {
                'hash': commit.hexsha[:8],
                'message': commit.message.strip(),
                'author': str(commit.author),
                'date': commit.committed_datetime.isoformat(),
                'files_changed': len(list(commit.stats.files.keys()))
            }
        except Exception as e:
            raise ArchyGitError(f"Failed to get commit info: {e}") from e
