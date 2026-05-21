"""
tests/scrubbing/conftest.py
===========================
ce fichier contient des fixtures et des helpers pour les tests de scrubbing dans observability.py. 

Stratégie : simuler un ScrubMatch sans dépendre du runtime Logfire.
On importe directement les structures de données et le callback depuis
observability.py, et on fabrique des ScrubMatch synthétiques.

"""

from __future__ import annotations

import re
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

# ── Résolution de chemin ────────────────────────────────────────────
# Structure attendue :
#   project_root/
#     agent/observability.py
#     tests/scrubbing/conftest.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = PROJECT_ROOT / "agent"
sys.path.insert(0, str(AGENT_DIR))
sys.path.insert(0, str(PROJECT_ROOT))


# ── Stub logfire minimal ─────────────────────────────────────────────
# Permet d'importer observability.py sans démarrer Logfire.

def _make_logfire_stub() -> types.ModuleType:
    mod = types.ModuleType("logfire")

    @dataclass
    class ScrubMatch:
        path: list[str | int]
        value: Any
        pattern_match: re.Match | None = None

    class ScrubbingOptions:
        def __init__(self, extra_patterns=None, callback=None):
            self.extra_patterns = extra_patterns or []
            self.callback = callback

    class ConsoleOptions:
        def __init__(self, **kwargs): pass

    mod.ScrubMatch = ScrubMatch
    mod.ScrubbingOptions = ScrubbingOptions
    mod.ConsoleOptions = ConsoleOptions
    mod.configure = lambda **kw: None
    mod.instrument_pydantic_ai = lambda **kw: None
    mod.instrument_fastapi = lambda app, **kw: None
    mod.span = lambda *a, **kw: __import__("contextlib").nullcontext()
    mod.info = lambda *a, **kw: None
    return mod


# Injecter le stub avant tout import de observability
if "logfire" not in sys.modules:
    sys.modules["logfire"] = _make_logfire_stub()

# Stub fastapi si absent
if "fastapi" not in sys.modules:
    fastapi_mod = types.ModuleType("fastapi")
    fastapi_mod.FastAPI = object
    sys.modules["fastapi"] = fastapi_mod


from backend.agent.scrubbing.observability import (  # noqa: E402
    FDT_SENSITIVE_PATTERNS,
    SAFE_TELEMETRY_EXACT_KEYS_LOWER,
    SAFE_TELEMETRY_PATH_PARTS_LOWER,
    fdt_scrub_callback,
)

# ── ScrubMatch local (identique au stub) ────────────────────────────
ScrubMatch = sys.modules["logfire"].ScrubMatch


# ════════════════════════════════════════════════════════════════════
# HELPERS PUBLICS
# ════════════════════════════════════════════════════════════════════

def make_match(path: list[str | int], value: Any = "sensitive_value") -> ScrubMatch:
    """Fabrique un ScrubMatch synthétique avec pattern_match simulé."""
    key = str(path[-1]) if path else ""
    # Chercher quel pattern match cette clé
    pat_match = None
    for raw_pattern in FDT_SENSITIVE_PATTERNS:
        m = re.search(raw_pattern, key, re.IGNORECASE)
        if m:
            pat_match = m
            break
    return ScrubMatch(path=path, value=value, pattern_match=pat_match)


def should_be_scrubbed(key: str, value: Any = "sensitive_value") -> bool:
    """Retourne True si fdt_scrub_callback retourne None (= scrubbed)."""
    match = make_match([key], value)
    result = fdt_scrub_callback(match)
    return result is None


def should_be_visible(key: str, value: Any = "safe_value") -> bool:
    """Retourne True si fdt_scrub_callback retourne la valeur (= visible)."""
    match = make_match([key], value)
    result = fdt_scrub_callback(match)
    return result == value


# ── Fixtures partagées ───────────────────────────────────────────────

@pytest.fixture(scope="session")
def patterns():
    return FDT_SENSITIVE_PATTERNS

@pytest.fixture(scope="session")
def safe_exact_keys():
    return SAFE_TELEMETRY_EXACT_KEYS_LOWER

@pytest.fixture(scope="session")
def safe_path_parts():
    return SAFE_TELEMETRY_PATH_PARTS_LOWER
