"""
Module: backend.core.business.executors
======================================
Traduit un scénario métier CONFIRMÉ en appels Integration Hub réels.

Chaque executor retourne toujours :
  {"answer": str, "ok": bool, "recoverable": bool}
- ok=False + recoverable=True  -> aucune écriture n'a eu lieu, "réessayer" est sûr.
- ok=False + recoverable=False -> une écriture partielle a peut-être eu lieu,
  retenter automatiquement est interdit (risque de doublon).

V1 : utilise un stockage mémoire (In-Memory Workflow Store), non persistant et l'état est perdu après un redémarrage du serveur et n'est pas partagé entre plusieurs instances FastAPI. 
- Acceptée pour la V1 afin de privilégier une architecture simple
- Une solution distribuée (Redis ou base de données) pourra être intégrée ultérieurement sans modifier la logique métier des exécuteurs.

"""

from __future__ import annotations

import logging
from typing import Any, Callable

from backend.core.business.business_types import BusinessScenario
from backend.core.business.workflow_execution_helpers import (
    parse_hub_json,
    resolve_timesheet_period,
    weekdays_between,
    all_days_between,
    format_date_fr,
)
from backend.tools.hub_functions import HUB_FUNCTIONS

logger = logging.getLogger(__name__)

ExecutorFn = Callable[[dict, Any, str], dict]


def _create_line(entry: dict, timesheet_nbr: str, user_context: Any, auth_header: str) -> dict:
    result = HUB_FUNCTIONS["create_timesheet_line"](
        timesheet_nbr=timesheet_nbr,
        proj_id=entry.get("project"),
        activity_number=entry.get("task"),
        category_id=entry.get("category"),
        resource_id=user_context.resource_id,
        date=entry.get("date"),
        qty=entry.get("hours"),
        internal_note="",
        external_note="",
        auth_header=auth_header,
    )
    logger.debug(
        "create_timesheet_line: timesheet=%s project=%s task=%s date=%s hours=%s",
        timesheet_nbr, entry.get("project"), entry.get("task"), entry.get("date"), entry.get("hours"),
    )
    print(
        "CREATE_LINE_DEBUG:",
        {
            "timesheet_nbr": timesheet_nbr,
            "project": entry.get("project"),
            "task": entry.get("task"),
            "category": entry.get("category"),
            "date": entry.get("date"),
            "hours": entry.get("hours"),
            "resource_id": user_context.resource_id,
        },
    )
    return parse_hub_json(result)


# ── 1. CREATE_EMPTY_TIMESHEET ───────────────────────────────────────────────

def execute_create_empty_timesheet(business_request: dict, user_context: Any, auth_header: str) -> dict:
    result = HUB_FUNCTIONS["create_timesheet"](
        resource_id=user_context.resource_id,
        period_start=None,
        description="",
        auth_header=auth_header,
    )
    payload = parse_hub_json(result)

    if payload.get("ok") and payload.get("data", {}).get("success"):
        record_id = payload["data"].get("recordId")
        return {
            "answer": f"C’est fait. Votre feuille de temps **{record_id}** a été créée avec succès.",
            "ok": True,
            "recoverable": False,
        }

    logger.warning("execute_create_empty_timesheet failed: %s", payload)
    # Aucune écriture n'a réussi (le create est un appel POST unique) -> récupérable.
    return {
        "answer": "Je n’ai pas pu créer la feuille de temps. Veuillez vérifier la période ou réessayer.",
        "ok": False,
        "recoverable": True,
    }


# ── 2. SINGLE_TIME_ENTRY ────────────────────────────────────────────────────

def execute_single_time_entry(business_request: dict, user_context: Any, auth_header: str) -> dict:
    entries = business_request.get("entries") or []
    timesheet_nbr = (business_request.get("timesheet") or {}).get("number")

    if not entries:
        return {"answer": "Je n’ai pas assez d’informations pour ajouter cette ligne de temps.", "ok": False, "recoverable": False}
    if not timesheet_nbr:
        return {"answer": "Il me manque le numéro de la feuille de temps pour ajouter cette ligne.", "ok": False, "recoverable": False}

    entry = entries[0]
    if not entry.get("date"):
        return {"answer": "Il me manque la date exacte pour ajouter cette ligne de temps.", "ok": False, "recoverable": False}

    payload = _create_line(entry, timesheet_nbr, user_context, auth_header)

    if payload.get("ok"):
        return {
            "answer": (
                f"C’est fait. **{entry.get('hours'):g}h** ont été ajoutées à la feuille "
                f"**{timesheet_nbr}** le **{format_date_fr(entry['date'])}**."
            ),
            "ok": True,
            "recoverable": False,
        }

    logger.warning("execute_single_time_entry failed: %s", payload)
    # Un seul appel POST, jamais exécuté avec succès -> récupérable.
    return {
        "answer": f"Je n’ai pas pu ajouter la ligne à la feuille **{timesheet_nbr}**. Veuillez réessayer.",
        "ok": False,
        "recoverable": True,
    }


# ── 3. Entry Dates  ─────────────────────────────────────────

def _resolve_entry_dates(
    entry: dict,
    timesheet_nbr: str,
    resource_id: str,
    auth_header: str,
) -> tuple[list[str], str | None]:
    """Détermine les dates réelles pour UNE entrée, selon son propre repeat_type.
    Retourne (dates, error_code). error_code vaut :
      - None                : succès
      - 'missing_date'      : repeat_type='none' mais aucune date fournie
      - 'period_unresolved' : range demandé mais la période Hub n'a pas pu être lue
      - 'unsupported_repeat': repeat_type non géré en V1 et pas de date de repli
    """
    repeat_type = entry.get("repeat_type") or "none"
    explicit_date = entry.get("date")

    if repeat_type == "none":
        if explicit_date:
            return [explicit_date], None
        return [], "missing_date"

    if repeat_type in {"weekday_range", "daily_range"}:
        period_start, period_end, debug_info = resolve_timesheet_period(
            hub_functions=HUB_FUNCTIONS,
            timesheet_nbr=timesheet_nbr,
            resource_id=resource_id,
            auth_header=auth_header,
        )
        if not period_start or not period_end:
            logger.warning(
                "Résolution de période échouée pour entry repeat_type=%s: debug=%s",
                repeat_type, debug_info,
            )
            return [], "period_unresolved"

        if repeat_type == "weekday_range":
            return weekdays_between(period_start, period_end), None
        return all_days_between(period_start, period_end), None

    # same_entry_multiple_days / unknown : pas assez d'information structurée en V1
    # pour déduire un intervalle sans ambiguïté -> on retombe sur la date explicite
    # si elle existe, sinon on échoue proprement plutôt que d'inventer une période.
    if explicit_date:
        return [explicit_date], None
    return [], "unsupported_repeat"


# ── Executor générique : couvre entrée unique, plusieurs entrées le même jour,
# répétition sur une période, ET la combinaison des deux (plusieurs projets
# sur plusieurs jours) — chaque entrée est expansée indépendamment selon son
# propre repeat_type, sans dépendre du scénario détecté en amont. ───────────

def execute_multi_entries(business_request: dict, user_context: Any, auth_header: str) -> dict:
    entries = business_request.get("entries") or []
    timesheet_nbr = (business_request.get("timesheet") or {}).get("number")

    if not entries or not timesheet_nbr:
        return {"answer": "Il me manque le numéro de feuille ou les lignes à ajouter.", "ok": False, "recoverable": False}

    created = 0
    failed = 0
    period_error_only = True  # reste True tant qu'aucune ligne n'a été écrite ET
                               # que tous les échecs sont des period_unresolved

    for entry in entries:
        dates, error = _resolve_entry_dates(entry, timesheet_nbr, user_context.resource_id, auth_header)

        if error:
            failed += 1
            if error != "period_unresolved":
                period_error_only = False
            continue

        for date in dates:
            entry_with_date = {**entry, "date": date}
            payload = _create_line(entry_with_date, timesheet_nbr, user_context, auth_header)
            if payload.get("ok"):
                created += 1
                period_error_only = False
            else:
                failed += 1
                period_error_only = False
                logger.warning("Ligne échouée pour entry=%s date=%s: %s", entry, date, payload)

    if created == 0 and failed > 0 and period_error_only:
        # Rien n'a été écrit, l'unique cause est une période introuvable -> récupérable.
        return {
            "answer": (
                f"Je n’ai pas pu récupérer la feuille **{timesheet_nbr}**. "
                "Veuillez réessayer dans quelques instants."
            ),
            "ok": False,
            "recoverable": True,
        }

    if failed == 0:
        return {
            "answer": f"C’est fait. **{created} lignes** ont été ajoutées à la feuille **{timesheet_nbr}**.",
            "ok": True,
            "recoverable": False,
        }

    # Écriture partielle (au moins une ligne créée, ou échecs mixtes) -> retry interdit.
    return {
        "answer": (
            f"Action partiellement réalisée : **{created} lignes ajoutées**, "
            f"**{failed} échecs** sur la feuille **{timesheet_nbr}**."
        ),
        "ok": False,
        "recoverable": False,
    }


# ── Registre central ─────────────────────────────────────────────────────

SCENARIO_EXECUTORS: dict[str, ExecutorFn] = {
    str(BusinessScenario.CREATE_EMPTY_TIMESHEET): execute_create_empty_timesheet,
    str(BusinessScenario.SINGLE_TIME_ENTRY): execute_single_time_entry,
    str(BusinessScenario.REPEAT_ENTRY_OVER_DATE_RANGE): execute_multi_entries,
    str(BusinessScenario.MULTI_PROJECT_SAME_DAY): execute_multi_entries,
    str(BusinessScenario.MULTI_TASK_SAME_PROJECT): execute_multi_entries,
}


def execute_confirmed_scenario(
    scenario: str | None,
    business_request: dict,
    user_context: Any,
    auth_header: str,
) -> dict:
    logger.debug("execute_confirmed_scenario scenario=%s", scenario)
    executor = SCENARIO_EXECUTORS.get(scenario)
    print("EXECUTOR_SELECTED:", executor.__name__)
    if not executor:
        logger.warning("Aucun executor enregistré pour le scénario '%s'.", scenario)
        return {
            "answer": "Action confirmée, mais aucun exécuteur disponible pour ce scénario.",
            "ok": False,
            "recoverable": False,
        }
    print("EXECUTOR_DEBUG_SCENARIO:", scenario)
    print("EXECUTOR_DEBUG_BUSINESS_REQUEST:", business_request)
    return executor(business_request, user_context, auth_header)