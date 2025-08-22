"""
AI backend integrations for Archy.

This module provides abstraction layer for different AI backends:
- cursor-agent: Cursor IDE integration
- fabric: Local AI model integration
- Base classes for extensibility
"""

from .base import AIBackend, AIBackendConfig
from .cursor_agent import CursorAgentBackend
from .fabric import FabricBackend

__all__ = ["AIBackend", "AIBackendConfig", "CursorAgentBackend", "FabricBackend"]
