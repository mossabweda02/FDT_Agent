"""
Tests de diagnostic de la résolution des dates et périodes.

Ces tests vérifient exclusivement la logique calendaire déterministe.
"""

from datetime import date

import pytest

from backend.core.business.timesheet_resolution.models import (
    TimesheetPeriodGranularity,
)
from backend.core.business.timesheet_resolution.period_resolver import (
    TimesheetPeriodResolutionError,
    resolve_timesheet_period,
)
from backend.core.datetime.date_resolver import (
    build_relative_date_context,
    resolve_relative_date,
    resolve_relative_period_mode,
)


REFERENCE_DATE = date(2026, 7, 21)  # mardi


class TestRelativeDateContext:
    """Tests du contexte temporel."""

    def test_builds_complete_context(self) -> None:
        context = build_relative_date_context(
            "Europe/Paris",
            reference_date=REFERENCE_DATE,
        )

        assert context.timezone == "Europe/Paris"

        assert context.today == "2026-07-21"
        assert context.yesterday == "2026-07-20"
        assert context.tomorrow == "2026-07-22"

        assert context.week_start == "2026-07-20"
        assert context.week_end == "2026-07-26"

        assert context.last_week_start == "2026-07-13"
        assert context.last_week_end == "2026-07-19"

        assert context.next_week_start == "2026-07-27"
        assert context.next_week_end == "2026-08-02"

        assert context.month_start == "2026-07-01"
        assert context.month_end == "2026-07-31"

        assert context.last_month_start == "2026-06-01"
        assert context.last_month_end == "2026-06-30"

        assert context.next_month_start == "2026-08-01"
        assert context.next_month_end == "2026-08-31"

    def test_invalid_timezone_falls_back_to_utc(self) -> None:
        context = build_relative_date_context(
            "Invalid/Timezone",
            reference_date=REFERENCE_DATE,
        )

        assert context.timezone == "UTC"
        assert context.today == "2026-07-21"


@pytest.mark.parametrize(
    ("expression", "expected_date"),
    [
        ("aujourd'hui", "2026-07-21"),
        ("Aujourd’hui", "2026-07-21"),
        ("today", "2026-07-21"),
        ("hier", "2026-07-20"),
        ("yesterday", "2026-07-20"),
        ("demain", "2026-07-22"),
        ("tomorrow", "2026-07-22"),
        ("Ajoute 8 heures aujourd'hui", "2026-07-21"),
    ],
)
def test_resolve_relative_date(
    expression: str,
    expected_date: str,
) -> None:
    result = resolve_relative_date(
        expression,
        reference_date=REFERENCE_DATE,
    )

    assert result == expected_date


def test_unknown_relative_date_returns_none() -> None:
    result = resolve_relative_date(
        "un jour quelconque",
        reference_date=REFERENCE_DATE,
    )

    assert result is None


@pytest.mark.parametrize(
    ("expression", "expected_mode"),
    [
        ("aujourd'hui", "today"),
        ("hier", "yesterday"),
        ("demain", "tomorrow"),
        ("cette semaine", "current_week"),
        ("la semaine dernière", "last_week"),
        ("la semaine prochaine", "next_week"),
        ("ce mois-ci", "current_month"),
        ("le mois précédent", "last_month"),
        ("le mois prochain", "next_month"),
        ("this week", "current_week"),
        ("next month", "next_month"),
    ],
)
def test_resolve_relative_period_mode(
    expression: str,
    expected_mode: str,
) -> None:
    assert resolve_relative_period_mode(expression) == expected_mode


@pytest.mark.parametrize(
    ("period_mode", "expected_date"),
    [
        ("today", date(2026, 7, 21)),
        ("yesterday", date(2026, 7, 20)),
        ("tomorrow", date(2026, 7, 22)),
    ],
)
def test_resolve_day_modes(
    period_mode: str,
    expected_date: date,
) -> None:
    period = resolve_timesheet_period(
        period_mode=period_mode,
        reference_date=REFERENCE_DATE,
    )

    assert period.start_date == date(2026, 7, 20)
    assert period.end_date == date(2026, 7, 26)
    assert period.explicit_date == expected_date
    assert period.granularity == TimesheetPeriodGranularity.DAY
    assert period.requires_clarification is False


@pytest.mark.parametrize(
    (
        "period_mode",
        "expected_start",
        "expected_end",
    ),
    [
        (
            "current_week",
            date(2026, 7, 20),
            date(2026, 7, 26),
        ),
        (
            "last_week",
            date(2026, 7, 13),
            date(2026, 7, 19),
        ),
        (
            "next_week",
            date(2026, 7, 27),
            date(2026, 8, 2),
        ),
    ],
)
def test_resolve_week_modes(
    period_mode: str,
    expected_start: date,
    expected_end: date,
) -> None:
    period = resolve_timesheet_period(
        period_mode=period_mode,
        reference_date=REFERENCE_DATE,
    )

    assert period.start_date == expected_start
    assert period.end_date == expected_end
    assert period.granularity == TimesheetPeriodGranularity.WEEK
    assert len(period.working_dates) == 5


@pytest.mark.parametrize(
    (
        "period_mode",
        "expected_start",
        "expected_end",
    ),
    [
        (
            "current_month",
            date(2026, 7, 1),
            date(2026, 7, 31),
        ),
        (
            "last_month",
            date(2026, 6, 1),
            date(2026, 6, 30),
        ),
        (
            "next_month",
            date(2026, 8, 1),
            date(2026, 8, 31),
        ),
    ],
)
def test_resolve_month_modes(
    period_mode: str,
    expected_start: date,
    expected_end: date,
) -> None:
    period = resolve_timesheet_period(
        period_mode=period_mode,
        reference_date=REFERENCE_DATE,
    )

    assert period.start_date == expected_start
    assert period.end_date == expected_end
    assert period.granularity == TimesheetPeriodGranularity.MONTH
    assert period.expects_multiple is True


def test_explicit_date_resolves_containing_week_without_clarification() -> None:
    period = resolve_timesheet_period(
        period_mode="explicit_date",
        explicit_date="2026-07-22",
        reference_date=REFERENCE_DATE,
        source_expression="le 22 juillet",
    )

    assert period.start_date == date(2026, 7, 20)
    assert period.end_date == date(2026, 7, 26)
    assert period.explicit_date == date(2026, 7, 22)
    assert period.requires_clarification is False
    assert period.clarification_question is None
    assert period.source_expression == "le 22 juillet"


def test_explicit_range_inside_one_week() -> None:
    period = resolve_timesheet_period(
        period_mode="explicit_range",
        explicit_start_date="2026-07-20",
        explicit_end_date="2026-07-24",
        reference_date=REFERENCE_DATE,
    )

    assert period.start_date == date(2026, 7, 20)
    assert period.end_date == date(2026, 7, 24)
    assert period.expects_multiple is False
    assert len(period.working_dates) == 5


def test_explicit_range_spanning_multiple_weeks() -> None:
    period = resolve_timesheet_period(
        period_mode="explicit_range",
        explicit_start_date="2026-07-20",
        explicit_end_date="2026-08-07",
        reference_date=REFERENCE_DATE,
    )

    assert period.expects_multiple is True


def test_invalid_explicit_range_is_rejected() -> None:
    with pytest.raises(
        TimesheetPeriodResolutionError,
        match="La date de fin ne peut pas précéder",
    ):
        resolve_timesheet_period(
            period_mode="explicit_range",
            explicit_start_date="2026-07-24",
            explicit_end_date="2026-07-20",
            reference_date=REFERENCE_DATE,
        )


def test_invalid_iso_date_is_rejected() -> None:
    with pytest.raises(
        TimesheetPeriodResolutionError,
        match="format YYYY-MM-DD",
    ):
        resolve_timesheet_period(
            period_mode="explicit_date",
            explicit_date="22/07/2026",
            reference_date=REFERENCE_DATE,
        )


def test_unknown_period_is_rejected() -> None:
    with pytest.raises(
        TimesheetPeriodResolutionError,
        match="n'a pas pu être identifiée",
    ):
        resolve_timesheet_period(
            period_mode="unknown",
            reference_date=REFERENCE_DATE,
        )


def test_timesheet_number_does_not_trigger_calendar_resolution() -> None:
    with pytest.raises(
        TimesheetPeriodResolutionError,
        match="numéro de feuille",
    ):
        resolve_timesheet_period(
            period_mode="timesheet_number",
            reference_date=REFERENCE_DATE,
        )