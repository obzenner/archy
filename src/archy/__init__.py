"""
Archy: AI-powered architecture documentation generator.

A modern CLI tool for automatically generating and updating software architecture
documentation using AI backends like cursor-agent and fabric.
"""

__version__ = "0.1.0"
__author__ = "Archy Development Team"
__email__ = "support@archy.dev"
__license__ = "MIT"

# Re-export main classes for easier imports
from .core.analyzer import ArchitectureAnalyzer
from .core.config import ArchyConfig
from .exceptions import ArchyConfigError, ArchyError, ArchyGitError

__all__ = [
    "ArchitectureAnalyzer",
    "ArchyConfig",
    "ArchyError",
    "ArchyConfigError",
    "ArchyGitError",
    "__version__",
]
