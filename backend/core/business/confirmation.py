"""
Module: backend.core.business.confirmation
======================================
Détection tolérante de confirmation / annulation / retry en langage naturel.
"""

import re

CONFIRMATION_WORDS = {
    "oui", "ok", "okay", "confirme", "confirmé", "confirmer",
    "continue", "continuer", "vas-y", "daccord", "yes", "go",
}

CANCEL_WORDS = {
    "non", "annule", "annuler", "annulé", "stop", "abandonner", "abandonne", "cancel",
}

NEGATION_GUARDS = {"pas", "jamais"}

RETRY_MARKERS = [
    "réessayer", "reessayer", "retente", "retenter", "ressaie", "réessaie",
    "essaie encore", "essaye encore", "recommence", "retry",
]

_WORD_RE = re.compile(r"[a-zà-öø-ÿ'-]+", re.IGNORECASE)


def _tokens(message: str) -> set[str]:
    normalized = (message or "").lower().replace("’", "'").replace("d'accord", "daccord")
    return set(_WORD_RE.findall(normalized))


def is_confirmation(message: str) -> bool:
    tokens = _tokens(message)
    if not tokens:
        return False
    if tokens & (CANCEL_WORDS | NEGATION_GUARDS):
        return False
    return bool(tokens & CONFIRMATION_WORDS)


def is_cancellation(message: str) -> bool:
    tokens = _tokens(message)
    return bool(tokens & CANCEL_WORDS)


def is_retry(message: str) -> bool:
    text = (message or "").lower().strip()
    if not text:
        return False
    return any(marker in text for marker in RETRY_MARKERS)