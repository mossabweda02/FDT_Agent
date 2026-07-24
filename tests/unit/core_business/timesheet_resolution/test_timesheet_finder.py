"""
Tests du moteur de recherche des feuilles de temps.

Ces tests vérifient la normalisation des réponses Integration Hub,
le filtrage par chevauchement de périodes et l'utilisation obligatoire
de la ressource de l'utilisateur connecté.
"""

import json
from datetime import date

import pytest

from backend.core.business.timesheet_resolution.models import (
    ResolvedTimesheetPeriod,
    TimesheetPeriodGranularity,
)
from backend.core.business.timesheet_resolution.timesheet_finder import (
    TimesheetFinderError,
    find_timesheets_for_period,
    periods_overlap,
)


def _period(
    start_date: date = date(2026, 7, 13),
    end_date: date = date(2026, 7, 19),
) -> ResolvedTimesheetPeriod:
    return ResolvedTimesheetPeriod(
        period_mode="current_week",
        start_date=start_date,
        end_date=end_date,
        working_dates=[],
        granularity=TimesheetPeriodGranularity.WEEK,
    )


def _hub_response(items: list[dict]) -> str:
    return json.dumps(
        {
            "ok": True,
            "data": {
                "count": len(items),
                "timesheets": items,
            },
        }
    )


class TestPeriodsOverlap:
    def test_identical_periods_overlap(self):
        assert periods_overlap(
            first_start=date(2026, 7, 13),
            first_end=date(2026, 7, 19),
            second_start=date(2026, 7, 13),
            second_end=date(2026, 7, 19),
        )

    def test_period_inside_another_overlaps(self):
        assert periods_overlap(
            first_start=date(2026, 7, 13),
            first_end=date(2026, 7, 19),
            second_start=date(2026, 7, 15),
            second_end=date(2026, 7, 15),
        )

    def test_boundary_date_overlaps(self):
        assert periods_overlap(
            first_start=date(2026, 7, 13),
            first_end=date(2026, 7, 19),
            second_start=date(2026, 7, 19),
            second_end=date(2026, 7, 25),
        )

    def test_period_before_does_not_overlap(self):
        assert not periods_overlap(
            first_start=date(2026, 7, 6),
            first_end=date(2026, 7, 12),
            second_start=date(2026, 7, 13),
            second_end=date(2026, 7, 19),
        )

    def test_period_after_does_not_overlap(self):
        assert not periods_overlap(
            first_start=date(2026, 7, 20),
            first_end=date(2026, 7, 26),
            second_start=date(2026, 7, 13),
            second_end=date(2026, 7, 19),
        )


class TestFindTimesheets:
    def test_single_matching_timesheet(self):
        def fake_list_timesheets(**kwargs):
            return _hub_response(
                [
                    {
                        "timesheetNbr": "TS-0000318",
                        "periodStart": "2026-07-13",
                        "periodEnd": "2026-07-19",
                        "status": "Draft",
                    }
                ]
            )

        result = find_timesheets_for_period(
            period=_period(),
            resource_id="RES-3988",
            auth_header="Bearer x",
            list_timesheets_fn=fake_list_timesheets,
        )

        assert result.found is True
        assert result.count == 1
        assert result.selected_timesheet is not None
        assert result.selected_timesheet.number == "TS-0000318"
        assert result.selected_timesheet.status == "Draft"

    def test_no_matching_timesheet(self):
        def fake_list_timesheets(**kwargs):
            return _hub_response(
                [
                    {
                        "timesheetNbr": "TS-OLD",
                        "periodStart": "2026-07-06",
                        "periodEnd": "2026-07-12",
                    }
                ]
            )

        result = find_timesheets_for_period(
            period=_period(),
            resource_id="RES-3988",
            auth_header="Bearer x",
            list_timesheets_fn=fake_list_timesheets,
        )

        assert result.found is False
        assert result.count == 0
        assert result.selected_timesheet is None

    def test_multiple_matching_timesheets(self):
        def fake_list_timesheets(**kwargs):
            return _hub_response(
                [
                    {
                        "timesheetNbr": "TS-1",
                        "periodStart": "2026-07-13",
                        "periodEnd": "2026-07-19",
                    },
                    {
                        "timesheetNbr": "TS-2",
                        "periodStart": "2026-07-15",
                        "periodEnd": "2026-07-21",
                    },
                ]
            )

        result = find_timesheets_for_period(
            period=_period(),
            resource_id="RES-3988",
            auth_header="Bearer x",
            list_timesheets_fn=fake_list_timesheets,
        )

        assert result.count == 2
        assert result.selected_timesheet is None
        assert [
            item.number
            for item in result.matched_timesheets
        ] == ["TS-1", "TS-2"]

    def test_filters_timesheets_outside_requested_period(self):
        def fake_list_timesheets(**kwargs):
            return _hub_response(
                [
                    {
                        "timesheetNbr": "TS-BEFORE",
                        "periodStart": "2026-07-06",
                        "periodEnd": "2026-07-12",
                    },
                    {
                        "timesheetNbr": "TS-MATCH",
                        "periodStart": "2026-07-13",
                        "periodEnd": "2026-07-19",
                    },
                    {
                        "timesheetNbr": "TS-AFTER",
                        "periodStart": "2026-07-20",
                        "periodEnd": "2026-07-26",
                    },
                ]
            )

        result = find_timesheets_for_period(
            period=_period(),
            resource_id="RES-3988",
            auth_header="Bearer x",
            list_timesheets_fn=fake_list_timesheets,
        )

        assert result.count == 1
        assert result.matched_timesheets[0].number == "TS-MATCH"

    def test_passes_authenticated_resource_to_hub(self):
        captured = {}

        def fake_list_timesheets(**kwargs):
            captured.update(kwargs)
            return _hub_response([])

        find_timesheets_for_period(
            period=_period(),
            resource_id="RES-3988",
            auth_header="Bearer user-token",
            limit=75,
            skip=10,
            list_timesheets_fn=fake_list_timesheets,
        )

        assert captured == {
            "resource_id": "RES-3988",
            "limit": 75,
            "skip": 10,
            "auth_header": "Bearer user-token",
        }

    def test_empty_hub_payload_returns_no_match(self):
        def fake_list_timesheets(**kwargs):
            return json.dumps(
                {
                    "ok": True,
                    "data": {
                        "count": 0,
                        "timesheets": [],
                    },
                }
            )

        result = find_timesheets_for_period(
            period=_period(),
            resource_id="RES-3988",
            auth_header="Bearer x",
            list_timesheets_fn=fake_list_timesheets,
        )

        assert result.found is False
        assert result.hub_error is None

    def test_invalid_timesheet_records_are_ignored(self):
        def fake_list_timesheets(**kwargs):
            return _hub_response(
                [
                    {
                        "timesheetNbr": "TS-NO-DATES",
                    },
                    {
                        "timesheetNbr": "TS-BAD-DATE",
                        "periodStart": "invalid",
                        "periodEnd": "2026-07-19",
                    },
                    {
                        "timesheetNbr": "TS-VALID",
                        "periodStart": "2026-07-13T00:00:00",
                        "periodEnd": "2026-07-19T23:59:59",
                    },
                ]
            )

        result = find_timesheets_for_period(
            period=_period(),
            resource_id="RES-3988",
            auth_header="Bearer x",
            list_timesheets_fn=fake_list_timesheets,
        )

        assert result.count == 1
        assert result.matched_timesheets[0].number == "TS-VALID"

    def test_hub_error_is_returned_without_exception(self):
        def fake_list_timesheets(**kwargs):
            return json.dumps(
                {
                    "ok": False,
                    "status": 500,
                    "error": "Erreur Hub",
                    "hint": "Réessayer plus tard.",
                }
            )

        result = find_timesheets_for_period(
            period=_period(),
            resource_id="RES-3988",
            auth_header="Bearer x",
            list_timesheets_fn=fake_list_timesheets,
        )

        assert result.found is False
        assert result.hub_error == (
            "Erreur Hub — Réessayer plus tard."
        )

    def test_missing_resource_id_is_rejected(self):
        with pytest.raises(
            TimesheetFinderError,
            match="resource_id",
        ):
            find_timesheets_for_period(
                period=_period(),
                resource_id="",
                auth_header="Bearer x",
                list_timesheets_fn=lambda **kwargs: _hub_response([]),
            )

    def test_invalid_json_response_is_rejected(self):
        with pytest.raises(
            TimesheetFinderError,
            match="JSON valide",
        ):
            find_timesheets_for_period(
                period=_period(),
                resource_id="RES-3988",
                auth_header="Bearer x",
                list_timesheets_fn=lambda **kwargs: "not-json",
            )