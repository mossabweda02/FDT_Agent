"""
Module: backend.core.business.intent_service
============================================
Résout l'intention métier en combinant la classification déterministe
et un fallback LLM optionnel et sécurisé.
"""

from __future__ import annotations

import logging
from typing import Awaitable, Callable

from backend.core.business.intent_classifier import classify_business_intent
from backend.core.business.llm_intent_classifier import (
    LLMIntentClassificationError,
    classify_intent_with_llm,
)


LLMCallable = Callable[[str, str], Awaitable[str]]

logger = logging.getLogger(__name__)


async def resolve_business_intent(
    message: str,
    *,
    llm_call: LLMCallable | None = None,
    enable_llm_fallback: bool = False,
    minimum_confidence: float = 0.75,
) -> str | None:
    """
    Résout l'intention métier.

    Ordre de traitement :
    1. classification déterministe ;
    2. fallback LLM uniquement si aucun résultat n'est trouvé ;
    3. retour à None si le LLM est désactivé, indisponible ou incertain.
    """

    deterministic_intent = classify_business_intent(message)

    if deterministic_intent is not None:
        return deterministic_intent

    if not enable_llm_fallback or llm_call is None:
        return None

    logger.info(
        "Classification déterministe indéterminée, "
        "utilisation du fallback LLM."
    )

    try:
        result = await classify_intent_with_llm(
            message=message,
            llm_call=llm_call,
        )
    except LLMIntentClassificationError as exc:
        logger.warning(
            "Échec de la classification d'intention par le LLM : %s",
            exc,
        )
        return None

    if result.intent == "UNKNOWN":
        logger.info(
            "Le fallback LLM n'a identifié aucune intention métier."
        )
        return None

    if result.confidence < minimum_confidence:
        logger.info(
            "Intention LLM ignorée en raison d'une confiance insuffisante : "
            "intent=%s, confidence=%.2f, minimum=%.2f",
            result.intent,
            result.confidence,
            minimum_confidence,
        )
        return None

    logger.info(
        "Intention détectée par le LLM : %s, confiance : %.2f",
        result.intent,
        result.confidence,
    )

    return result.intent