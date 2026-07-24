"""
Module: backend.core.datetime.date_resolver
===========================================

Résolution déterministe des expressions temporelles relatives.

Ce module fournit un contexte temporel cohérent à partir du fuseau horaire
de l'utilisateur et résout les expressions calendaires les plus fréquentes.

Le LLM peut reconnaître une expression temporelle, mais le calcul des dates
reste effectué par le backend afin de garantir un comportement testable,
stable et indépendant du modèle utilisé.
"""

from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_TIMEZONE = os.environ.get("FDT_TIMEZONE", "Europe/Paris")


@dataclass(frozen=True)
class RelativeDateContext:
    """Contexte calendaire utilisé par l'agent et les résolveurs métier."""

    timezone: str

    today: str
    yesterday: str
    tomorrow: str

    week_start: str
    week_end: str

    last_week_start: str
    last_week_end: str

    next_week_start: str
    next_week_end: str

    month_start: str
    month_end: str

    last_month_start: str
    last_month_end: str

    next_month_start: str
    next_month_end: str


def resolve_timezone(timezone: str | None = None) -> tuple[str, ZoneInfo]:
    """Retourne un fuseau valide avec un fallback explicite vers UTC."""

    requested_timezone = timezone or DEFAULT_TIMEZONE

    try:
        return requested_timezone, ZoneInfo(requested_timezone)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return "UTC", ZoneInfo("UTC")


def get_current_date(
    timezone: str | None = None,
    *,
    reference_date: date | None = None,
) -> date:
    """Retourne la date courante dans le fuseau demandé.

    ``reference_date`` permet d'obtenir des tests entièrement déterministes.
    """

    if reference_date is not None:
        return reference_date

    _, tz = resolve_timezone(timezone)
    return datetime.now(tz).date()


def build_relative_date_context(
    timezone: str | None = None,
    *,
    reference_date: date | None = None,
) -> RelativeDateContext:
    """Construit toutes les principales bornes temporelles relatives."""

    resolved_timezone, _ = resolve_timezone(timezone)
    today = get_current_date(
        resolved_timezone,
        reference_date=reference_date,
    )

    week_start, week_end = _week_bounds(today)

    last_week_start = week_start - timedelta(days=7)
    last_week_end = last_week_start + timedelta(days=6)

    next_week_start = week_start + timedelta(days=7)
    next_week_end = next_week_start + timedelta(days=6)

    month_start, month_end = _month_bounds(today)
    last_month_start, last_month_end = _previous_month_bounds(today)
    next_month_start, next_month_end = _next_month_bounds(today)

    return RelativeDateContext(
        timezone=resolved_timezone,
        today=today.isoformat(),
        yesterday=(today - timedelta(days=1)).isoformat(),
        tomorrow=(today + timedelta(days=1)).isoformat(),
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        last_week_start=last_week_start.isoformat(),
        last_week_end=last_week_end.isoformat(),
        next_week_start=next_week_start.isoformat(),
        next_week_end=next_week_end.isoformat(),
        month_start=month_start.isoformat(),
        month_end=month_end.isoformat(),
        last_month_start=last_month_start.isoformat(),
        last_month_end=last_month_end.isoformat(),
        next_month_start=next_month_start.isoformat(),
        next_month_end=next_month_end.isoformat(),
    )


def resolve_relative_date(
    text: str,
    timezone: str | None = None,
    *,
    reference_date: date | None = None,
) -> str | None:
    """Résout une expression désignant une journée précise.

    Exemples pris en charge :

    - aujourd'hui ;
    - hier ;
    - demain ;
    - today ;
    - yesterday ;
    - tomorrow.

    Les expressions représentant une période, comme ``cette semaine``,
    sont volontairement prises en charge par ``resolve_relative_period_mode``.
    """

    normalized = normalize_temporal_expression(text)

    if not normalized:
        return None

    context = build_relative_date_context(
        timezone,
        reference_date=reference_date,
    )

    if _contains_any(
        normalized,
        (
            "aujourd hui",
            "ce jour",
            "today",
        ),
    ):
        return context.today

    if _contains_any(
        normalized,
        (
            "hier",
            "yesterday",
        ),
    ):
        return context.yesterday

    if _contains_any(
        normalized,
        (
            "demain",
            "tomorrow",
        ),
    ):
        return context.tomorrow

    return None


def resolve_relative_period_mode(text: str) -> str | None:
    """Détermine le ``period_mode`` métier depuis une expression naturelle.

    Cette fonction ne calcule pas les bornes calendaires. Elle traduit
    uniquement l'expression vers le vocabulaire structuré du backend.
    """

    normalized = normalize_temporal_expression(text)

    if not normalized:
        return None

    # Les expressions longues doivent être testées avant les mots isolés.
    period_patterns: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "last_week",
            (
                "semaine derniere",
                "semaine precedente",
                "la semaine passee",
                "last week",
                "previous week",
            ),
        ),
        (
            "next_week",
            (
                "semaine prochaine",
                "semaine suivante",
                "next week",
                "following week",
            ),
        ),
        (
            "current_week",
            (
                "cette semaine",
                "semaine actuelle",
                "semaine courante",
                "current week",
                "this week",
            ),
        ),
        (
            "last_month",
            (
                "mois dernier",
                "mois precedent",
                "last month",
                "previous month",
            ),
        ),
        (
            "next_month",
            (
                "mois prochain",
                "mois suivant",
                "next month",
                "following month",
            ),
        ),
        (
            "current_month",
            (
                "ce mois",
                "mois actuel",
                "mois courant",
                "current month",
                "this month",
            ),
        ),
        (
            "today",
            (
                "aujourd hui",
                "ce jour",
                "today",
            ),
        ),
        (
            "yesterday",
            (
                "hier",
                "yesterday",
            ),
        ),
        (
            "tomorrow",
            (
                "demain",
                "tomorrow",
            ),
        ),
    )

    for period_mode, expressions in period_patterns:
        if _contains_any(normalized, expressions):
            return period_mode

    return None


def normalize_temporal_expression(value: str | None) -> str:
    """Normalise une expression pour permettre une comparaison robuste."""

    if not value:
        return ""

    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    normalized = normalized.casefold()

    punctuation = ("'", "’", "-", "_", "/", "\\", ",", ".", ";", ":")
    for character in punctuation:
        normalized = normalized.replace(character, " ")

    return " ".join(normalized.split())


def _contains_any(text: str, expressions: tuple[str, ...]) -> bool:
    """Indique si une des expressions normalisées apparaît dans le texte."""

    return any(expression in text for expression in expressions)


def _week_bounds(target_date: date) -> tuple[date, date]:
    """Retourne les bornes lundi-dimanche d'une semaine."""

    start_date = target_date - timedelta(days=target_date.weekday())
    end_date = start_date + timedelta(days=6)

    return start_date, end_date


def _month_bounds(target_date: date) -> tuple[date, date]:
    """Retourne le premier et le dernier jour du mois courant."""

    start_date = target_date.replace(day=1)

    if target_date.month == 12:
        next_month_start = date(target_date.year + 1, 1, 1)
    else:
        next_month_start = date(
            target_date.year,
            target_date.month + 1,
            1,
        )

    end_date = next_month_start - timedelta(days=1)

    return start_date, end_date


def _previous_month_bounds(target_date: date) -> tuple[date, date]:
    """Retourne le premier et le dernier jour du mois précédent."""

    current_month_start = target_date.replace(day=1)
    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)

    return previous_month_start, previous_month_end


def _next_month_bounds(target_date: date) -> tuple[date, date]:
    """Retourne le premier et le dernier jour du mois suivant."""

    if target_date.month == 12:
        next_month_start = date(target_date.year + 1, 1, 1)
    else:
        next_month_start = date(
            target_date.year,
            target_date.month + 1,
            1,
        )

    if next_month_start.month == 12:
        following_month_start = date(
            next_month_start.year + 1,
            1,
            1,
        )
    else:
        following_month_start = date(
            next_month_start.year,
            next_month_start.month + 1,
            1,
        )

    next_month_end = following_month_start - timedelta(days=1)

    return next_month_start, next_month_end