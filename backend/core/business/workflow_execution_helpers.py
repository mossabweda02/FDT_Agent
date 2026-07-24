from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Iterable

logger = logging.getLogger(__name__)


def parse_hub_json(raw: str | None) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        logger.error("Hub JSON parse failed. Raw payload (truncated): %r", (raw or "")[:500])
        return {"ok": False, "error": "Invalid Hub response"}


def extract_data(payload: dict) -> dict:
    data = payload.get("data")
    return data if isinstance(data, dict) else {}


# ── Recherche tolérante aux formats Hub réels (casse/nommage/imbrication inconnus) ──

def _norm_key(key: str) -> str:
    return key.replace("_", "").replace("-", "").lower()


def _find_first(item: dict, candidate_names: Iterable[str]) -> Any:
    """Cherche la 1re valeur non vide parmi plusieurs noms de clé possibles,
    en comparant les clés indépendamment de la casse et des underscores."""
    if not isinstance(item, dict):
        return None
    normalized = {_norm_key(k): v for k, v in item.items()}
    for name in candidate_names:
        value = normalized.get(_norm_key(name))
        if value not in (None, ""):
            return value
    return None


def _iter_dict_lists(node: Any, depth: int = 0, max_depth: int = 4) -> Iterable[list[dict]]:
    """Parcourt récursivement le JSON et yield chaque liste de dicts trouvée,
    quel que soit le niveau d'imbrication (data.items, data.results.value,
    data.result.data, etc.)."""
    if depth > max_depth:
        return
    if isinstance(node, list):
        dict_items = [x for x in node if isinstance(x, dict)]
        if dict_items:
            yield dict_items
        return
    if isinstance(node, dict):
        for value in node.values():
            yield from _iter_dict_lists(value, depth + 1, max_depth)


_TIMESHEET_NUMBER_FIELDS = (
    "timesheetNbr", "timesheetNumber", "timesheetNo", "number",
    "TIMESHEETNBR", "TimesheetNbr", "recordId", "code", "id",
)

_PERIOD_START_FIELDS = (
    "periodStart", "periodFrom", "PERIODFROM", "fromDate", "startDate",
    "dateFrom", "start", "periodStartDate", "beginDate",
)

_PERIOD_END_FIELDS = (
    "periodEnd", "periodTo", "PERIODTO", "toDate", "endDate",
    "dateTo", "end", "periodEndDate", "finishDate",
)


def find_timesheet_in_list_payload(list_payload: dict, timesheet_nbr: str) -> dict:
    """Retrouve une feuille précise dans le payload de hub_list_timesheets,
    quel que soit le format exact (liste plate, data.items, data.results,
    data.value, pagination imbriquée...)."""
    if not timesheet_nbr:
        return {"ok": False, "error": "timesheet_nbr manquant"}

    wanted = timesheet_nbr.strip().upper()
    data = list_payload.get("data") or list_payload

    for candidates in _iter_dict_lists(data):
        for item in candidates:
            number = _find_first(item, _TIMESHEET_NUMBER_FIELDS)
            if isinstance(number, str) and number.strip().upper() == wanted:
                return {"ok": True, "data": item}

    return {"ok": False, "error": "Timesheet not found in list payload"}


def extract_timesheet_period(timesheet_payload: dict) -> tuple[str | None, str | None]:
    """Extrait periodStart/periodEnd, quel que soit le format Hub exact."""
    data = extract_data(timesheet_payload)
    if not data and isinstance(timesheet_payload, dict):
        data = timesheet_payload

    candidates = [data]
    for key in ("timesheet", "record", "result", "header", "period"):
        nested = data.get(key) if isinstance(data, dict) else None
        if isinstance(nested, dict):
            candidates.append(nested)

    for item in candidates:
        start = _find_first(item, _PERIOD_START_FIELDS)
        end = _find_first(item, _PERIOD_END_FIELDS)
        if start and end:
            return str(start)[:10], str(end)[:10]

    return None, None


def weekdays_between(start: str, end: str) -> list[str]:
    start_date = datetime.fromisoformat(start[:10]).date()
    end_date = datetime.fromisoformat(end[:10]).date()

    days: list[str] = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def format_date_fr(iso_date: str | None) -> str:
    """yyyy-mm-dd -> dd/mm/yyyy pour l'affichage utilisateur."""
    if not iso_date:
        return "?"
    try:
        return datetime.fromisoformat(iso_date[:10]).strftime("%d/%m/%Y")
    except ValueError:
        return iso_date


# ── Orchestration Hub (get_timesheet -> fallback list_timesheets) ──────────

def resolve_timesheet_period(
    hub_functions: dict,
    timesheet_nbr: str,
    resource_id: str | None,
    auth_header: str,
) -> tuple[str | None, str | None, dict]:
    """1. hub_get_timesheet  2. fallback hub_list_timesheets + recherche par numéro."""
    debug_info: dict[str, Any] = {"source": None}

    ts_raw = None
    try:
        ts_raw = hub_functions["get_timesheet"](
            timesheet_nbr=timesheet_nbr,
            resource_id=resource_id,
            auth_header=auth_header,
        )
    except Exception as exc:
        logger.warning("hub_get_timesheet exception: %s", exc)

    if ts_raw:
        logger.debug("hub_get_timesheet raw (truncated): %s", ts_raw[:800])
        ts_payload = parse_hub_json(ts_raw)
        if ts_payload.get("ok"):
            start, end = extract_timesheet_period(ts_payload)
            if start and end:
                debug_info["source"] = "get_timesheet"
                return start, end, debug_info

    list_raw = None
    try:
        list_raw = hub_functions["list_timesheets"](
            resource_id=resource_id,
            limit=50,
            skip=0,
            auth_header=auth_header,
        )
    except Exception as exc:
        logger.warning("hub_list_timesheets exception: %s", exc)
        debug_info["source"] = "list_timesheets_exception"
        return None, None, debug_info

    logger.debug("hub_list_timesheets raw (truncated): %s", (list_raw or "")[:800])
    logger.debug("resource_id utilisé: %s", resource_id)
    list_payload = parse_hub_json(list_raw)

    found = find_timesheet_in_list_payload(list_payload, timesheet_nbr)
    if not found.get("ok"):
        debug_info["source"] = "list_timesheets_not_found"
        return None, None, debug_info

    start, end = extract_timesheet_period(found)
    debug_info["source"] = "list_timesheets"
    return start, end, debug_info


def create_repeat_entries(
    hub_functions: dict,
    timesheet_nbr: str,
    resource_id: str | None,
    base_entry: dict,
    period_start: str,
    period_end: str,
    auth_header: str,
) -> tuple[int, int]:
    """Crée une ligne par jour ouvré. Retourne (créées, échouées)."""
    created = 0
    failed = 0

    for date in weekdays_between(period_start, period_end):
        try:
            result = hub_functions["create_timesheet_line"](
                timesheet_nbr=timesheet_nbr,
                proj_id=base_entry.get("project"),
                activity_number=base_entry.get("task"),
                category_id=base_entry.get("category"),
                resource_id=resource_id,
                date=date,
                qty=base_entry.get("hours"),
                internal_note="",
                external_note="",
                auth_header=auth_header,
            )
            payload = parse_hub_json(result)
        except Exception as exc:
            logger.warning("hub_create_timesheet_line exception (%s): %s", date, exc)
            payload = {"ok": False}

        if payload.get("ok"):
            created += 1
        else:
            failed += 1

    return created, failed

def all_days_between(start: str, end: str) -> list[str]:
    """Comme weekdays_between, mais inclut samedi/dimanche (repeat_type='daily_range')."""
    start_date = datetime.fromisoformat(start[:10]).date()
    end_date = datetime.fromisoformat(end[:10]).date()

    days: list[str] = []
    current = start_date
    while current <= end_date:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days