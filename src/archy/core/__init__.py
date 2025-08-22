"""
Core functionality for Archy architecture documentation generator.

This module contains the main business logic including:
- Configuration management
- Architecture analysis engine
- Git operations
- File operations and security validation
"""

from .analyzer import ArchitectureAnalyzer
from .config import ArchyConfig

__all__ = ["ArchitectureAnalyzer", "ArchyConfig"]
