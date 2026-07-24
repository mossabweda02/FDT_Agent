"""
Module: backend.business.structured_extractor
======================================
Extraction structurée d'une demande métier.

Le LLM interprète le langage naturel.
Le backend reçoit un BusinessRequest validé par Pydantic.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic_ai import Agent

from backend.core.business.business_request import BusinessRequest


STRUCTURED_EXTRACTION_PROMPT = """
Tu extrais une demande métier FDT Agent sous forme structurée.

Règles :
- Retourner uniquement un objet compatible avec BusinessRequest.
- Ne pas répondre à l'utilisateur.
- Ne pas inventer d'identifiants.
- Si une information manque, la mettre dans missing_information.
- Si une période est ambiguë, l'ajouter dans ambiguity_notes.
- Respecter l'intention et le scénario déjà détectés.
- Pour une action d'écriture, requires_confirmation doit être true.
- Pour "oui", "confirmer", "continuer", user_confirmation_detected doit être true.

Règle obligatoire :
Si une feuille TS-xxxx est fournie et que l'utilisateur demande une répétition
comme "du lundi au vendredi" :

- créer UNE seule entrée dans entries
- mettre date = null
- mettre repeat_type = "weekday_range"
- mettre dates_must_be_resolved_from_timesheet = true
- ne jamais générer les dates exactes
- ne jamais utiliser le contexte temporel courant pour calculer les dates

Règles d’extraction des identifiants :

- Une valeur au format PRJ-xxxxx/TSK-xxxxx contient deux identifiants distincts.
- La partie PRJ-xxxxx doit être placée dans entry.project.
- La partie TSK-xxxxx doit être placée dans entry.task.
- Ne jamais placer la chaîne complète PRJ-xxxxx/TSK-xxxxx dans entry.project.

Règle de date commune :

- Si une date est fournie une seule fois pour plusieurs saisies, cette date s’applique à toutes les entries concernées.
- Exemple :
  "Le 15 juillet 2026, ajoute 1h sur PRJ-1/TSK-1 et 3h sur PRJ-2/TSK-2"
  doit produire deux entries avec date = "2026-07-15".

  Règle de date commune :

Si une date est mentionnée une seule fois avant plusieurs saisies,
elle s'applique à toutes les entries concernées.

Exemple :
"Le 15 juillet 2026, ajoute 1h sur PRJ-00042/TSK-00062
et 3h sur PRJ-00051/TSK-00063"

doit produire :
- timesheet.period_mode = "explicit_date"
- timesheet.explicit_date = "2026-07-15"
- entries[0].date = "2026-07-15"
- entries[1].date = "2026-07-15"
""".strip()


async def extract_business_request(
    *,
    message: str,
    intent: str | None,
    scenario: str,
    model: Any,
    user_context: dict[str, Any] | None = None,
    date_context: dict[str, Any] | None = None,
) -> BusinessRequest:
    """Extrait un BusinessRequest depuis le message utilisateur."""

    extractor = Agent(
        model=model,
        system_prompt=STRUCTURED_EXTRACTION_PROMPT,
        output_type=BusinessRequest,
    )

    prompt = f"""
Message utilisateur :
{message}

Intention détectée :
{intent or "UNKNOWN"}

Scénario détecté :
{scenario}

Contexte utilisateur :
{user_context or {}}

Contexte temporel :
{date_context or {}}
""".strip()

    result = await extractor.run(prompt)
    request = result.output

    if request.action.intent == "UNKNOWN" and intent:
        request.action.intent = intent

    if request.action.scenario == "UNKNOWN_SCENARIO" and scenario:
        request.action.scenario = scenario

    return request

def normalize_business_request(business_request):
    common_date = business_request.timesheet.explicit_date

    for entry in business_request.entries:
        if entry.project and "/" in entry.project and not entry.task:
            match = re.fullmatch(
                r"(PRJ-\d+)\s*/\s*(TSK-\d+)",
                entry.project,
                flags=re.IGNORECASE,
            )
            if match:
                entry.project = match.group(1).upper()
                entry.task = match.group(2).upper()

        if not entry.date and common_date:
            entry.date = common_date