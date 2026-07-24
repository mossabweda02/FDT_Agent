"""
Module: backend.core.business.timesheet_resolution.period_resolver
=================================================================

Résolution déterministe des périodes de feuilles de temps.

Ce fichier transforme un mode temporel structuré du BusinessRequest
en bornes calendaires absolues.

Il ne recherche aucune feuille et n'appelle aucune API externe.
"""

from __future__ import annotations

from datetime import date, timedelta

from backend.core.business.timesheet_resolution.models import (
    ResolvedTimesheetPeriod,
    TimesheetPeriodGranularity,
)


_FRENCH_MONTHS = {
    1: "janvier",
    2: "février",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "août",
    9: "septembre",
    10: "octobre",
    11: "novembre",
    12: "décembre",
}


class TimesheetPeriodResolutionError(ValueError):
    """Erreur levée lorsque la période ne peut pas être résolue."""


def resolve_timesheet_period(
    *,
    period_mode: str,
    explicit_date: str | None = None,
    explicit_start_date: str | None = None,
    explicit_end_date: str | None = None,
    reference_date: date | None = None,
    source_expression: str | None = None,
) -> ResolvedTimesheetPeriod:
    """Résout une référence temporelle structurée en période calendaire."""

    current_date = reference_date or date.today()
    normalized_mode = (period_mode or "").strip().casefold()

    if normalized_mode == "today":
        return _build_day_period(
            period_mode=normalized_mode,
            target_date=current_date,
            source_expression=source_expression,
        )

    if normalized_mode == "yesterday":
        return _build_day_period(
            period_mode=normalized_mode,
            target_date=current_date - timedelta(days=1),
            source_expression=source_expression,
        )

    if normalized_mode == "tomorrow":
        return _build_day_period(
            period_mode=normalized_mode,
            target_date=current_date + timedelta(days=1),
            source_expression=source_expression,
        )

    if normalized_mode == "current_week":
        start_date, end_date = _week_bounds(current_date)

        return _build_period(
            period_mode=normalized_mode,
            start_date=start_date,
            end_date=end_date,
            granularity=TimesheetPeriodGranularity.WEEK,
            source_expression=source_expression,
        )

    if normalized_mode == "last_week":
        current_week_start, _ = _week_bounds(current_date)
        start_date = current_week_start - timedelta(days=7)
        end_date = start_date + timedelta(days=6)

        return _build_period(
            period_mode=normalized_mode,
            start_date=start_date,
            end_date=end_date,
            granularity=TimesheetPeriodGranularity.WEEK,
            source_expression=source_expression,
        )

    if normalized_mode == "next_week":
        current_week_start, _ = _week_bounds(current_date)
        start_date = current_week_start + timedelta(days=7)
        end_date = start_date + timedelta(days=6)

        return _build_period(
            period_mode=normalized_mode,
            start_date=start_date,
            end_date=end_date,
            granularity=TimesheetPeriodGranularity.WEEK,
            source_expression=source_expression,
        )

    if normalized_mode == "current_month":
        start_date, end_date = _month_bounds(current_date)

        return _build_period(
            period_mode=normalized_mode,
            start_date=start_date,
            end_date=end_date,
            granularity=TimesheetPeriodGranularity.MONTH,
            expects_multiple=_spans_multiple_weeks(
                start_date,
                end_date,
            ),
            source_expression=source_expression,
        )

    if normalized_mode == "last_month":
        start_date, end_date = _previous_month_bounds(current_date)

        return _build_period(
            period_mode=normalized_mode,
            start_date=start_date,
            end_date=end_date,
            granularity=TimesheetPeriodGranularity.MONTH,
            expects_multiple=_spans_multiple_weeks(
                start_date,
                end_date,
            ),
            source_expression=source_expression,
        )

    if normalized_mode == "next_month":
        start_date, end_date = _next_month_bounds(current_date)

        return _build_period(
            period_mode=normalized_mode,
            start_date=start_date,
            end_date=end_date,
            granularity=TimesheetPeriodGranularity.MONTH,
            expects_multiple=_spans_multiple_weeks(
                start_date,
                end_date,
            ),
            source_expression=source_expression,
        )

    if normalized_mode == "explicit_date":
        resolved_date = _parse_iso_date(
            explicit_date,
            field_name="explicit_date",
        )

        week_start, week_end = _week_bounds(resolved_date)

        return _build_period(
            period_mode=normalized_mode,
            start_date=week_start,
            end_date=week_end,
            granularity=TimesheetPeriodGranularity.DAY,
            explicit_date=resolved_date,
            source_expression=source_expression,
        )

    if normalized_mode == "explicit_range":
        start_date = _parse_iso_date(
            explicit_start_date,
            field_name="explicit_start_date",
        )
        end_date = _parse_iso_date(
            explicit_end_date,
            field_name="explicit_end_date",
        )

        if end_date < start_date:
            raise TimesheetPeriodResolutionError(
                "La date de fin ne peut pas précéder la date de début."
            )

        return _build_period(
            period_mode=normalized_mode,
            start_date=start_date,
            end_date=end_date,
            granularity=TimesheetPeriodGranularity.CUSTOM,
            expects_multiple=_spans_multiple_weeks(
                start_date,
                end_date,
            ),
            source_expression=source_expression,
        )

    if normalized_mode == "timesheet_number":
        raise TimesheetPeriodResolutionError(
            "Une référence par numéro de feuille ne nécessite pas "
            "de résolution calendaire."
        )

    if normalized_mode == "unknown":
        raise TimesheetPeriodResolutionError(
            "La période demandée n'a pas pu être identifiée."
        )

    raise TimesheetPeriodResolutionError(
        f"Mode de période non pris en charge : {period_mode!r}."
    )


def _build_day_period(
    *,
    period_mode: str,
    target_date: date,
    source_expression: str | None,
) -> ResolvedTimesheetPeriod:
    """Construit la période de feuille contenant une journée précise."""

    week_start, week_end = _week_bounds(target_date)

    return _build_period(
        period_mode=period_mode,
        start_date=week_start,
        end_date=week_end,
        granularity=TimesheetPeriodGranularity.DAY,
        explicit_date=target_date,
        source_expression=source_expression,
    )


def _build_period(
    *,
    period_mode: str,
    start_date: date,
    end_date: date,
    granularity: TimesheetPeriodGranularity,
    explicit_date: date | None = None,
    expects_multiple: bool = False,
    requires_clarification: bool = False,
    clarification_question: str | None = None,
    source_expression: str | None = None,
) -> ResolvedTimesheetPeriod:
    """Construit une période résolue avec ses jours ouvrables."""

    return ResolvedTimesheetPeriod(
        period_mode=period_mode,
        start_date=start_date,
        end_date=end_date,
        working_dates=_working_dates_between(
            start_date,
            end_date,
        ),
        granularity=granularity,
        explicit_date=explicit_date,
        expects_multiple=expects_multiple,
        requires_clarification=requires_clarification,
        clarification_question=clarification_question,
        source_expression=source_expression,
    )


def _week_bounds(target_date: date) -> tuple[date, date]:
    """Retourne le lundi et le dimanche de la semaine ciblée."""

    start_date = target_date - timedelta(days=target_date.weekday())
    end_date = start_date + timedelta(days=6)

    return start_date, end_date


def _month_bounds(reference_date: date) -> tuple[date, date]:
    """Retourne les bornes du mois contenant la date de référence."""

    start_date = reference_date.replace(day=1)

    if reference_date.month == 12:
        next_month_start = date(
            reference_date.year + 1,
            1,
            1,
        )
    else:
        next_month_start = date(
            reference_date.year,
            reference_date.month + 1,
            1,
        )

    end_date = next_month_start - timedelta(days=1)

    return start_date, end_date


def _previous_month_bounds(reference_date: date) -> tuple[date, date]:
    """Retourne les bornes du mois précédent."""

    current_month_start = reference_date.replace(day=1)
    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)

    return previous_month_start, previous_month_end


def _next_month_bounds(reference_date: date) -> tuple[date, date]:
    """Retourne les bornes du mois suivant."""

    if reference_date.month == 12:
        next_month_start = date(
            reference_date.year + 1,
            1,
            1,
        )
    else:
        next_month_start = date(
            reference_date.year,
            reference_date.month + 1,
            1,
        )

    return _month_bounds(next_month_start)


def _working_dates_between(
    start_date: date,
    end_date: date,
) -> list[date]:
    """Retourne les jours ouvrables du lundi au vendredi."""

    current_date = start_date
    working_dates: list[date] = []

    while current_date <= end_date:
        if current_date.weekday() < 5:
            working_dates.append(current_date)

        current_date += timedelta(days=1)

    return working_dates


def _parse_iso_date(
    value: str | None,
    *,
    field_name: str,
) -> date:
    """Convertit une chaîne ISO YYYY-MM-DD en date."""

    if not value:
        raise TimesheetPeriodResolutionError(
            f"Le champ {field_name} est obligatoire."
        )

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise TimesheetPeriodResolutionError(
            f"Le champ {field_name} doit respecter le format YYYY-MM-DD."
        ) from exc


def _spans_multiple_weeks(
    start_date: date,
    end_date: date,
) -> bool:
    """Indique si une période couvre plusieurs semaines."""

    start_week, _ = _week_bounds(start_date)
    end_week, _ = _week_bounds(end_date)

    return start_week != end_week


def format_french_date(value: date) -> str:
    """Formate une date dans un format lisible en français."""

    return (
        f"{value.day} "
        f"{_FRENCH_MONTHS[value.month]} "
        f"{value.year}"
    )


def format_french_period(
    start_date: date,
    end_date: date,
) -> str:
    """Formate une période dans un format lisible en français."""

    if (
        start_date.month == end_date.month
        and start_date.year == end_date.year
    ):
        return (
            f"du {start_date.day} au {end_date.day} "
            f"{_FRENCH_MONTHS[end_date.month]} "
            f"{end_date.year}"
        )

    return (
        f"du {format_french_date(start_date)} "
        f"au {format_french_date(end_date)}"
    )