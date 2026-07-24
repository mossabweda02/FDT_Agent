"""
Module: backend.core.business.timesheet_resolution.timesheet_finder
==================================================================

Recherche des feuilles de temps correspondant à une période.

Ce fichier appelle Integration Hub avec la ressource de l'utilisateur,
normalise les feuilles retournées et conserve uniquement celles dont
la période chevauche la période métier demandée.

Il ne crée aucune feuille et ne prend aucune décision conversationnelle.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Callable

from backend.core.business.timesheet_resolution.models import (
    ResolvedTimesheetPeriod,
    TimesheetLookupResult,
    TimesheetSummary,
)
from backend.tools.hub_functions import hub_list_timesheets


class TimesheetFinderError(ValueError):
    """Erreur de normalisation ou de recherche des feuilles de temps."""


ListTimesheetsCallable = Callable[..., str]


def find_timesheets_for_period(
    *,
    period: ResolvedTimesheetPeriod,
    resource_id: str,
    auth_header: str,
    limit: int = 100,
    skip: int = 0,
    list_timesheets_fn: ListTimesheetsCallable = hub_list_timesheets,
) -> TimesheetLookupResult:
    """Recherche les feuilles de l'utilisateur qui chevauchent la période."""

    if not resource_id:
        raise TimesheetFinderError(
            "Le resource_id est obligatoire pour rechercher les feuilles."
        )

    raw_response = list_timesheets_fn(
        resource_id=resource_id,
        limit=limit,
        skip=skip,
        auth_header=auth_header,
    )

    payload = _parse_json_response(raw_response)

    if not payload.get("ok"):
        return TimesheetLookupResult(
            requested_start_date=period.start_date,
            requested_end_date=period.end_date,
            hub_error=_extract_hub_error(payload),
        )

    raw_timesheets = _extract_timesheet_items(payload.get("data"))

    normalized_timesheets: list[TimesheetSummary] = []

    for raw_timesheet in raw_timesheets:
        summary = _normalize_timesheet(raw_timesheet)

        if summary is None:
            continue

        if periods_overlap(
            first_start=summary.start_date,
            first_end=summary.end_date,
            second_start=period.start_date,
            second_end=period.end_date,
        ):
            normalized_timesheets.append(summary)

    normalized_timesheets.sort(
        key=lambda item: (item.start_date, item.end_date, item.number)
    )

    return TimesheetLookupResult(
        requested_start_date=period.start_date,
        requested_end_date=period.end_date,
        matched_timesheets=normalized_timesheets,
    )


def periods_overlap(
    *,
    first_start: date,
    first_end: date,
    second_start: date,
    second_end: date,
) -> bool:
    """Indique si deux intervalles calendaires se chevauchent."""

    return first_start <= second_end and first_end >= second_start


def _parse_json_response(raw_response: str) -> dict[str, Any]:
    """Convertit la réponse Hub standardisée en dictionnaire."""

    try:
        payload = json.loads(raw_response)
    except (TypeError, json.JSONDecodeError) as exc:
        raise TimesheetFinderError(
            "La réponse de list_timesheets n'est pas un JSON valide."
        ) from exc

    if not isinstance(payload, dict):
        raise TimesheetFinderError(
            "La réponse de list_timesheets doit être un objet JSON."
        )

    return payload


def _extract_hub_error(payload: dict[str, Any]) -> str:
    """Construit un message d'erreur exploitable à partir de la réponse Hub."""

    error = payload.get("error")
    hint = payload.get("hint")

    if error and hint:
        return f"{error} — {hint}"

    return str(error or hint or "La recherche des feuilles a échoué.")


def _extract_timesheet_items(data: Any) -> list[dict[str, Any]]:
    """Extrait la liste des feuilles depuis les formats Hub connus."""

    if data is None:
        return []

    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if not isinstance(data, dict):
        return []

    candidate_keys = (
        "timesheets",
        "items",
        "results",
        "records",
        "data",
    )

    for key in candidate_keys:
        candidate = data.get(key)

        if isinstance(candidate, list):
            return [
                item
                for item in candidate
                if isinstance(item, dict)
            ]

    if _looks_like_timesheet(data):
        return [data]

    return []


def _normalize_timesheet(
    raw_timesheet: dict[str, Any],
) -> TimesheetSummary | None:
    """Normalise une feuille brute retournée par Integration Hub."""

    number = _first_non_empty(
        raw_timesheet,
        (
            "timesheetNbr",
            "timesheetNumber",
            "timesheet_nbr",
            "number",
            "id",
        ),
    )

    start_value = _first_non_empty(
        raw_timesheet,
        (
            "periodStart",
            "periodStartDate",
            "startDate",
            "start_date",
            "fromDate",
            "dateFrom",
        ),
    )

    end_value = _first_non_empty(
        raw_timesheet,
        (
            "periodEnd",
            "periodEndDate",
            "endDate",
            "end_date",
            "toDate",
            "dateTo",
        ),
    )

    if not number or not start_value or not end_value:
        return None

    start_date = _parse_date_value(start_value)
    end_date = _parse_date_value(end_value)

    if start_date is None or end_date is None:
        return None

    if end_date < start_date:
        return None

    status = _first_non_empty(
        raw_timesheet,
        (
            "status",
            "approvalStatus",
            "workflowStatus",
            "state",
        ),
    )

    return TimesheetSummary(
        number=str(number),
        start_date=start_date,
        end_date=end_date,
        status=str(status) if status is not None else None,
        raw_data=raw_timesheet,
    )


def _first_non_empty(
    data: dict[str, Any],
    keys: tuple[str, ...],
) -> Any:
    """Retourne la première valeur non vide parmi plusieurs clés possibles."""

    for key in keys:
        value = data.get(key)

        if value not in (None, ""):
            return value

    return None


def _parse_date_value(value: Any) -> date | None:
    """Convertit une date Hub ISO en objet date."""

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        return None

    normalized = value.strip()

    if not normalized:
        return None

    try:
        return date.fromisoformat(normalized[:10])
    except ValueError:
        return None


def _looks_like_timesheet(data: dict[str, Any]) -> bool:
    """Indique si un objet unique semble représenter une feuille."""

    identifier_keys = {
        "timesheetNbr",
        "timesheetNumber",
        "timesheet_nbr",
        "number",
    }

    return any(key in data for key in identifier_keys)