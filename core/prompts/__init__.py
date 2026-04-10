"""
core/prompts/__init__.py
=========================
Exports publics du package prompts.
Tout le reste du code importe UNIQUEMENT depuis ici.

Usage :
    from core.prompts import build_system_prompt, SYSTEM_PROMPT, TOOLS_DEFINITIONS
"""

from core.prompts.system_prompt     import build_system_prompt, SYSTEM_PROMPT
from core.prompts.tools_definitions import TOOLS_DEFINITIONS

__all__ = [
    "build_system_prompt",
    "SYSTEM_PROMPT",
    "TOOLS_DEFINITIONS",
]