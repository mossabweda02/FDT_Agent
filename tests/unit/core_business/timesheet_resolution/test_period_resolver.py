"""
Tests du résolveur de périodes de feuilles de temps.

Ces tests vérifient les semaines lundi-dimanche, les jours ouvrables,
le mois précédent et la clarification d'une date explicite.
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


REFERENCE_DATE = date(2026, 7, 14)


class TestCurrentWeek:
    def test_current_week_resolves_monday_to_sunday(self):
        result = resolve_timesheet_period(
            period_mode="current_week",
            reference_date=REFERENCE_DATE,
            source_expression="cette semaine",
        )

        assert result.start_date == date(2026, 7, 13)
        assert result.end_date == date(2026, 7, 19)
        assert result.granularity == TimesheetPeriodGranularity.WEEK
        assert result.requires_clarification is False

    def test_current_week_contains_only_working_dates(self):
        result = resolve_timesheet_period(
            period_mode="current_week",
            reference_date=REFERENCE_DATE,
        )

        assert result.working_dates == [
            date(2026, 7, 13),
            date(2026, 7, 14),
            date(2026, 7, 15),
            date(2026, 7, 16),
            date(2026, 7, 17),
        ]


class TestPreviousWeek:
    def test_previous_week_resolves_monday_to_sunday(self):
        result = resolve_timesheet_period(
            period_mode="last_week",
            reference_date=REFERENCE_DATE,
        )

        assert result.start_date == date(2026, 7, 6)
        assert result.end_date == date(2026, 7, 12)

    def test_previous_week_contains_only_working_dates(self):
        result = resolve_timesheet_period(
            period_mode="last_week",
            reference_date=REFERENCE_DATE,
        )

        assert result.working_dates == [
            date(2026, 7, 6),
            date(2026, 7, 7),
            date(2026, 7, 8),
            date(2026, 7, 9),
            date(2026, 7, 10),
        ]


class TestPreviousMonth:
    def test_previous_month_resolves_first_to_last_day(self):
        result = resolve_timesheet_period(
            period_mode="last_month",
            reference_date=REFERENCE_DATE,
        )

        assert result.start_date == date(2026, 6, 1)
        assert result.end_date == date(2026, 6, 30)
        assert result.expects_multiple is True
        assert result.granularity == TimesheetPeriodGranularity.MONTH

    def test_previous_month_handles_january_transition(self):
        result = resolve_timesheet_period(
            period_mode="last_month",
            reference_date=date(2026, 1, 10),
        )

        assert result.start_date == date(2025, 12, 1)
        assert result.end_date == date(2025, 12, 31)

    def test_previous_month_handles_leap_year(self):
        result = resolve_timesheet_period(
            period_mode="last_month",
            reference_date=date(2024, 3, 15),
        )

        assert result.start_date == date(2024, 2, 1)
        assert result.end_date == date(2024, 2, 29)


class TestExplicitDate:
    def test_explicit_monday_uses_week_without_clarification(self):
        result = resolve_timesheet_period(
            period_mode="explicit_date",
            explicit_date="2026-07-13",
            reference_date=REFERENCE_DATE,
        )

        assert result.start_date == date(2026, 7, 13)
        assert result.end_date == date(2026, 7, 19)
        assert result.explicit_date == date(2026, 7, 13)
        assert result.requires_clarification is False
        assert result.clarification_question is None

    def test_explicit_midweek_date_requires_clarification(self):
        result = resolve_timesheet_period(
            period_mode="explicit_date",
            explicit_date="2026-07-15",
            reference_date=REFERENCE_DATE,
            source_expression="la feuille du 15/07",
        )

        assert result.start_date == date(2026, 7, 13)
        assert result.end_date == date(2026, 7, 19)
        assert result.explicit_date == date(2026, 7, 15)
        assert result.requires_clarification is True
        assert result.source_expression == "la feuille du 15/07"
        assert result.clarification_question == (
            "Le 15 juillet 2026 appartient à la semaine "
            "du 13 au 19 juillet 2026. "
            "Souhaitez-vous utiliser cette feuille de temps ?"
        )

    def test_explicit_date_working_days_cover_monday_to_friday(self):
        result = resolve_timesheet_period(
            period_mode="explicit_date",
            explicit_date="2026-07-15",
        )

        assert result.working_dates == [
            date(2026, 7, 13),
            date(2026, 7, 14),
            date(2026, 7, 15),
            date(2026, 7, 16),
            date(2026, 7, 17),
        ]


class TestExplicitRange:
    def test_explicit_range_is_resolved(self):
        result = resolve_timesheet_period(
            period_mode="explicit_range",
            explicit_start_date="2026-07-13",
            explicit_end_date="2026-07-19",
        )

        assert result.start_date == date(2026, 7, 13)
        assert result.end_date == date(2026, 7, 19)
        assert result.expects_multiple is False
        assert result.granularity == TimesheetPeriodGranularity.CUSTOM

    def test_range_spanning_multiple_weeks_expects_multiple(self):
        result = resolve_timesheet_period(
            period_mode="explicit_range",
            explicit_start_date="2026-07-13",
            explicit_end_date="2026-07-31",
        )

        assert result.expects_multiple is True

    def test_invalid_range_is_rejected(self):
        with pytest.raises(
            TimesheetPeriodResolutionError,
            match="date de fin",
        ):
            resolve_timesheet_period(
                period_mode="explicit_range",
                explicit_start_date="2026-07-20",
                explicit_end_date="2026-07-13",
            )


class TestInvalidInput:
    def test_missing_explicit_date_is_rejected(self):
        with pytest.raises(
            TimesheetPeriodResolutionError,
            match="explicit_date",
        ):
            resolve_timesheet_period(
                period_mode="explicit_date",
            )

    def test_invalid_iso_date_is_rejected(self):
        with pytest.raises(
            TimesheetPeriodResolutionError,
            match="YYYY-MM-DD",
        ):
            resolve_timesheet_period(
                period_mode="explicit_date",
                explicit_date="15/07/2026",
            )

    def test_unknown_mode_is_rejected(self):
        with pytest.raises(
            TimesheetPeriodResolutionError,
            match="non pris en charge",
        ):
            resolve_timesheet_period(
                period_mode="unknown",
            )