"""
Module: backend.business.llm_intent_classifier
==============================================
Classification d'intention métier à l'aide d'un LLM.

Le module analyse les formulations qui ne sont pas reconnues de manière
fiable par le classificateur déterministe. Il valide strictement la réponse
du modèle avant de transmettre une intention au reste du backend.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Awaitable, Callable


ALLOWED_INTENTS = {
    "CREATE_TIMESHEET",
    "ADD_TIME_ENTRY",
    "ADD_MULTIPLE_TIME_ENTRIES",
    "UPDATE_TIME_ENTRY",
    "DELETE_TIME_ENTRY",
    "CONSULT_TIMESHEET",
    "CONFIRM_ACTION",
    "CANCEL_ACTION",
    "UNKNOWN",
}


SYSTEM_PROMPT = """
Tu es le classificateur d'intentions métier de FDT Agent.

Ta seule responsabilité est de comprendre l'action demandée par
l'utilisateur, même lorsque son message contient :
- des fautes d'orthographe ;
- des synonymes ;
- une formulation informelle ;
- du français et de l'anglais ;
- des noms de projets ou de tâches contenant des verbes.

Choisis exactement une intention parmi :

- CREATE_TIMESHEET
- ADD_TIME_ENTRY
- ADD_MULTIPLE_TIME_ENTRIES
- UPDATE_TIME_ENTRY
- DELETE_TIME_ENTRY
- CONSULT_TIMESHEET
- CONFIRM_ACTION
- CANCEL_ACTION
- UNKNOWN

Définitions :

CREATE_TIMESHEET :
Créer, préparer, générer, ouvrir ou ajouter une ou plusieurs feuilles
de temps.

ADD_TIME_ENTRY :
Ajouter une seule saisie, ligne ou quantité d'heures dans une feuille.

ADD_MULTIPLE_TIME_ENTRIES :
Ajouter plusieurs saisies, plusieurs quantités d'heures, plusieurs jours,
plusieurs projets ou plusieurs tâches.

UPDATE_TIME_ENTRY :
Modifier ou corriger une saisie existante.

DELETE_TIME_ENTRY :
Supprimer une saisie existante.

CONSULT_TIMESHEET :
Afficher, lister ou consulter des feuilles, leurs détails, leurs heures
ou le total des heures.

CONFIRM_ACTION :
Confirmer explicitement une action proposée.

CANCEL_ACTION :
Annuler ou refuser explicitement une action proposée.

UNKNOWN :
La demande ne correspond à aucune intention disponible ou reste trop
ambiguë.

Attention :
- "Ajouter une feuille de temps" signifie CREATE_TIMESHEET.
- "Ajouter des heures dans une feuille" signifie ADD_TIME_ENTRY.
- Un nom de tâche comme "Prepare building permit documentation" ne signifie
  pas automatiquement CREATE_TIMESHEET.
- Ne crée aucune nouvelle valeur d'intention.

Réponds uniquement avec un objet JSON valide, sans Markdown :

{
  "intent": "CREATE_TIMESHEET",
  "confidence": 0.95,
  "reason": "Explication courte"
}
""".strip()


@dataclass(frozen=True)
class LLMIntentResult:
    """Résultat validé de la classification LLM."""

    intent: str
    confidence: float
    reason: str | None = None


class LLMIntentClassificationError(Exception):
    """Erreur produite lorsque la réponse du modèle est inutilisable."""


# Cette fonction représente ton appel LLM actuel.
# Elle recevra le system prompt et le message utilisateur.
LLMCallable = Callable[[str, str], Awaitable[str]]


async def classify_intent_with_llm(
    message: str,
    llm_call: LLMCallable,
) -> LLMIntentResult:
    """
    Classifie une demande utilisateur avec le LLM.

    Le client LLM est injecté afin que ce module reste indépendant
    du fournisseur utilisé et soit facilement testable avec un mock.
    """

    normalized_message = (message or "").strip()

    if not normalized_message:
        return LLMIntentResult(
            intent="UNKNOWN",
            confidence=0.0,
            reason="Le message utilisateur est vide.",
        )

    try:
        raw_response = await llm_call(
            SYSTEM_PROMPT,
            normalized_message,
        )
    except Exception as exc:
        raise LLMIntentClassificationError(
            "Échec de l'appel au modèle LLM."
        ) from exc

    return parse_llm_intent_response(raw_response)


def parse_llm_intent_response(raw_response: str) -> LLMIntentResult:
    """Analyse et valide strictement la réponse JSON du modèle."""

    cleaned_response = _remove_markdown_code_fence(raw_response)

    try:
        payload = json.loads(cleaned_response)
    except (json.JSONDecodeError, TypeError) as exc:
        raise LLMIntentClassificationError(
            "Le modèle n'a pas retourné un JSON valide."
        ) from exc

    if not isinstance(payload, dict):
        raise LLMIntentClassificationError(
            "La réponse du modèle doit être un objet JSON."
        )

    intent = str(payload.get("intent", "")).strip().upper()
    reason = payload.get("reason")

    if intent not in ALLOWED_INTENTS:
        raise LLMIntentClassificationError(
            f"Intention LLM non autorisée : {intent or '<vide>'}."
        )

    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError) as exc:
        raise LLMIntentClassificationError(
            "Le niveau de confiance doit être numérique."
        ) from exc

    confidence = max(0.0, min(confidence, 1.0))

    return LLMIntentResult(
        intent=intent,
        confidence=confidence,
        reason=str(reason).strip() if reason else None,
    )


def _remove_markdown_code_fence(value: str) -> str:
    """
    Retire les balises Markdown éventuellement ajoutées par le modèle.

    Même si le prompt interdit Markdown, cette protection évite qu'une
    réponse entourée de ```json provoque une erreur inutile.
    """

    text = (value or "").strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text