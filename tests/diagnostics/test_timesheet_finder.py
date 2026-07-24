"""
Tests de diagnostic de la recherche des feuilles de temps.

Ces tests valident le comportement déterministe de timesheet_finder.py
sans appeler réellement Integration Hub.

Les réponses du Hub sont simulées afin de couvrir :

- une feuille trouvée ;
- aucune feuille trouvée ;
- plusieurs feuilles trouvées ;
- plusieurs formats de réponse ;
- les périodes qui se chevauchent ;
- les erreurs Hub ;
- les réponses JSON invalides ;
- les feuilles incomplètes ou invalides ;
- la transmission correcte des paramètres au Hub.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

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


def build_period(
    *,
    start_date: date = date(2026, 7, 20),
    end_date: date = date(2026, 7, 26),
) -> ResolvedTimesheetPeriod:
    """Construit une période hebdomadaire utilisée dans les tests."""

    return ResolvedTimesheetPeriod(
        period_mode="current_week",
        start_date=start_date,
        end_date=end_date,
        working_dates=[
            date(2026, 7, 20),
            date(2026, 7, 21),
            date(2026, 7, 22),
            date(2026, 7, 23),
            date(2026, 7, 24),
        ],
        granularity=TimesheetPeriodGranularity.WEEK,
    )


def build_hub_response(
    *,
    ok: bool = True,
    data: Any = None,
    error: str | None = None,
    hint: str | None = None,
) -> str:
    """Construit une réponse JSON simulant le contrat du Hub."""

    return json.dumps(
        {
            "ok": ok,
            "data": data,
            "error": error,
            "hint": hint,
        }
    )


class FakeListTimesheets:
    """Fake enregistrant les paramètres reçus par le finder."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self,
        *,
        resource_id: str,
        limit: int,
        skip: int,
        auth_header: str,
    ) -> str:
        self.calls.append(
            {
                "resource_id": resource_id,
                "limit": limit,
                "skip": skip,
                "auth_header": auth_header,
            }
        )

        return self.response


class TestPeriodsOverlap:
    """Tests de la règle de chevauchement calendaire."""

    def test_identical_periods_overlap(self) -> None:
        assert periods_overlap(
            first_start=date(2026, 7, 20),
            first_end=date(2026, 7, 26),
            second_start=date(2026, 7, 20),
            second_end=date(2026, 7, 26),
        )

    def test_partial_overlap_at_start(self) -> None:
        assert periods_overlap(
            first_start=date(2026, 7, 18),
            first_end=date(2026, 7, 22),
            second_start=date(2026, 7, 20),
            second_end=date(2026, 7, 26),
        )

    def test_partial_overlap_at_end(self) -> None:
        assert periods_overlap(
            first_start=date(2026, 7, 24),
            first_end=date(2026, 7, 30),
            second_start=date(2026, 7, 20),
            second_end=date(2026, 7, 26),
        )

    def test_touching_boundaries_overlap(self) -> None:
        assert periods_overlap(
            first_start=date(2026, 7, 26),
            first_end=date(2026, 8, 1),
            second_start=date(2026, 7, 20),
            second_end=date(2026, 7, 26),
        )

    def test_period_before_does_not_overlap(self) -> None:
        assert not periods_overlap(
            first_start=date(2026, 7, 13),
            first_end=date(2026, 7, 19),
            second_start=date(2026, 7, 20),
            second_end=date(2026, 7, 26),
        )

    def test_period_after_does_not_overlap(self) -> None:
        assert not periods_overlap(
            first_start=date(2026, 7, 27),
            first_end=date(2026, 8, 2),
            second_start=date(2026, 7, 20),
            second_end=date(2026, 7, 26),
        )


class TestFindTimesheetsForPeriod:
    """Tests principaux de find_timesheets_for_period."""

    def test_finds_one_matching_timesheet(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                data=[
                    {
                        "timesheetNbr": "TS-2026-001",
                        "periodStart": "2026-07-20",
                        "periodEnd": "2026-07-26",
                        "status": "Open",
                    }
                ]
            )
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.found is True
        assert result.count == 1
        assert result.hub_error is None

        assert result.selected_timesheet is not None
        assert result.selected_timesheet.number == "TS-2026-001"
        assert result.selected_timesheet.start_date == date(2026, 7, 20)
        assert result.selected_timesheet.end_date == date(2026, 7, 26)
        assert result.selected_timesheet.status == "Open"

    def test_returns_no_match_when_list_is_empty(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.found is False
        assert result.count == 0
        assert result.selected_timesheet is None
        assert result.hub_error is None

    def test_ignores_timesheets_outside_requested_period(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                data=[
                    {
                        "timesheetNbr": "TS-PREVIOUS",
                        "periodStart": "2026-07-13",
                        "periodEnd": "2026-07-19",
                    },
                    {
                        "timesheetNbr": "TS-NEXT",
                        "periodStart": "2026-07-27",
                        "periodEnd": "2026-08-02",
                    },
                ]
            )
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.count == 0
        assert result.selected_timesheet is None

    def test_keeps_only_overlapping_timesheets(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                data=[
                    {
                        "timesheetNbr": "TS-PREVIOUS",
                        "periodStart": "2026-07-13",
                        "periodEnd": "2026-07-19",
                    },
                    {
                        "timesheetNbr": "TS-CURRENT",
                        "periodStart": "2026-07-20",
                        "periodEnd": "2026-07-26",
                    },
                    {
                        "timesheetNbr": "TS-NEXT",
                        "periodStart": "2026-07-27",
                        "periodEnd": "2026-08-02",
                    },
                ]
            )
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.count == 1
        assert result.matched_timesheets[0].number == "TS-CURRENT"

    def test_multiple_matches_do_not_select_automatically(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                data=[
                    {
                        "timesheetNbr": "TS-002",
                        "periodStart": "2026-07-20",
                        "periodEnd": "2026-07-26",
                    },
                    {
                        "timesheetNbr": "TS-001",
                        "periodStart": "2026-07-20",
                        "periodEnd": "2026-07-26",
                    },
                ]
            )
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.found is True
        assert result.count == 2
        assert result.selected_timesheet is None

        assert [
            item.number
            for item in result.matched_timesheets
        ] == [
            "TS-001",
            "TS-002",
        ]

    def test_sorts_matches_by_start_end_and_number(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                data=[
                    {
                        "timesheetNbr": "TS-C",
                        "periodStart": "2026-07-22",
                        "periodEnd": "2026-07-26",
                    },
                    {
                        "timesheetNbr": "TS-B",
                        "periodStart": "2026-07-20",
                        "periodEnd": "2026-07-26",
                    },
                    {
                        "timesheetNbr": "TS-A",
                        "periodStart": "2026-07-20",
                        "periodEnd": "2026-07-26",
                    },
                ]
            )
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert [
            item.number
            for item in result.matched_timesheets
        ] == [
            "TS-A",
            "TS-B",
            "TS-C",
        ]

    def test_transmits_parameters_to_hub_function(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-456",
            auth_header="Bearer abc",
            limit=25,
            skip=50,
            list_timesheets_fn=fake,
        )

        assert fake.calls == [
            {
                "resource_id": "RESOURCE-456",
                "limit": 25,
                "skip": 50,
                "auth_header": "Bearer abc",
            }
        ]

    def test_missing_resource_id_is_rejected(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        with pytest.raises(
            TimesheetFinderError,
            match="resource_id est obligatoire",
        ):
            find_timesheets_for_period(
                period=build_period(),
                resource_id="",
                auth_header="Bearer test-token",
                list_timesheets_fn=fake,
            )

        assert fake.calls == []


class TestHubResponseFormats:
    """Tests des différents formats connus de réponse Hub."""

    @pytest.mark.parametrize(
        "container_key",
        [
            "timesheets",
            "items",
            "results",
            "records",
            "data",
        ],
    )
    def test_supports_nested_list_formats(
        self,
        container_key: str,
    ) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                data={
                    container_key: [
                        {
                            "timesheetNbr": "TS-NESTED",
                            "periodStart": "2026-07-20",
                            "periodEnd": "2026-07-26",
                        }
                    ]
                }
            )
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.count == 1
        assert result.selected_timesheet is not None
        assert result.selected_timesheet.number == "TS-NESTED"

    def test_supports_single_timesheet_object(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                data={
                    "timesheetNumber": "TS-SINGLE",
                    "periodStartDate": "2026-07-20",
                    "periodEndDate": "2026-07-26",
                    "approvalStatus": "Approved",
                }
            )
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.count == 1
        assert result.selected_timesheet is not None
        assert result.selected_timesheet.number == "TS-SINGLE"
        assert result.selected_timesheet.status == "Approved"

    @pytest.mark.parametrize(
        (
            "raw_timesheet",
            "expected_number",
            "expected_status",
        ),
        [
            (
                {
                    "timesheetNbr": "TS-1",
                    "periodStart": "2026-07-20",
                    "periodEnd": "2026-07-26",
                    "status": "Open",
                },
                "TS-1",
                "Open",
            ),
            (
                {
                    "timesheetNumber": "TS-2",
                    "periodStartDate": "2026-07-20",
                    "periodEndDate": "2026-07-26",
                    "approvalStatus": "Approved",
                },
                "TS-2",
                "Approved",
            ),
            (
                {
                    "timesheet_nbr": "TS-3",
                    "start_date": "2026-07-20",
                    "end_date": "2026-07-26",
                    "workflowStatus": "Submitted",
                },
                "TS-3",
                "Submitted",
            ),
            (
                {
                    "number": "TS-4",
                    "fromDate": "2026-07-20",
                    "toDate": "2026-07-26",
                    "state": "Draft",
                },
                "TS-4",
                "Draft",
            ),
            (
                {
                    "id": 12345,
                    "dateFrom": "2026-07-20T00:00:00",
                    "dateTo": "2026-07-26T23:59:59",
                },
                "12345",
                None,
            ),
        ],
    )
    def test_normalizes_known_field_names(
        self,
        raw_timesheet: dict[str, Any],
        expected_number: str,
        expected_status: str | None,
    ) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[raw_timesheet])
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.count == 1
        assert result.matched_timesheets[0].number == expected_number
        assert result.matched_timesheets[0].status == expected_status


class TestInvalidHubData:
    """Tests des données Hub invalides ou incomplètes."""

    @pytest.mark.parametrize(
        "raw_timesheet",
        [
            {
                "periodStart": "2026-07-20",
                "periodEnd": "2026-07-26",
            },
            {
                "timesheetNbr": "TS-MISSING-START",
                "periodEnd": "2026-07-26",
            },
            {
                "timesheetNbr": "TS-MISSING-END",
                "periodStart": "2026-07-20",
            },
            {
                "timesheetNbr": "TS-BAD-START",
                "periodStart": "invalid-date",
                "periodEnd": "2026-07-26",
            },
            {
                "timesheetNbr": "TS-BAD-END",
                "periodStart": "2026-07-20",
                "periodEnd": "invalid-date",
            },
            {
                "timesheetNbr": "TS-REVERSED",
                "periodStart": "2026-07-26",
                "periodEnd": "2026-07-20",
            },
        ],
    )
    def test_ignores_invalid_timesheets(
        self,
        raw_timesheet: dict[str, Any],
    ) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[raw_timesheet])
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.count == 0
        assert result.selected_timesheet is None

    def test_ignores_non_dictionary_items(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                data=[
                    None,
                    "invalid",
                    42,
                    {
                        "timesheetNbr": "TS-VALID",
                        "periodStart": "2026-07-20",
                        "periodEnd": "2026-07-26",
                    },
                ]
            )
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.count == 1
        assert result.selected_timesheet is not None
        assert result.selected_timesheet.number == "TS-VALID"

    @pytest.mark.parametrize(
        "data",
        [
            None,
            "unexpected",
            123,
            True,
            {},
            {"items": "not-a-list"},
        ],
    )
    def test_unknown_data_formats_return_empty_result(
        self,
        data: Any,
    ) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=data)
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.count == 0
        assert result.hub_error is None


class TestHubErrors:
    """Tests des erreurs fonctionnelles et techniques du Hub."""

    def test_returns_hub_error_without_raising(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                ok=False,
                error="Timeout Integration Hub",
                hint="Réessayer ultérieurement",
            )
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.found is False
        assert result.count == 0
        assert result.selected_timesheet is None
        assert result.hub_error == (
            "Timeout Integration Hub — Réessayer ultérieurement"
        )

    def test_uses_default_hub_error_message(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                ok=False,
                data=None,
            )
        )

        result = find_timesheets_for_period(
            period=build_period(),
            resource_id="RESOURCE-123",
            auth_header="Bearer test-token",
            list_timesheets_fn=fake,
        )

        assert result.hub_error == (
            "La recherche des feuilles a échoué."
        )

    @pytest.mark.parametrize(
        "invalid_response",
        [
            "",
            "not-json",
            "{invalid}",
        ],
    )
    def test_invalid_json_response_is_rejected(
        self,
        invalid_response: str,
    ) -> None:
        fake = FakeListTimesheets(invalid_response)

        with pytest.raises(
            TimesheetFinderError,
            match="n'est pas un JSON valide",
        ):
            find_timesheets_for_period(
                period=build_period(),
                resource_id="RESOURCE-123",
                auth_header="Bearer test-token",
                list_timesheets_fn=fake,
            )

    @pytest.mark.parametrize(
        "non_object_response",
        [
            "[]",
            '"text"',
            "123",
            "true",
            "null",
        ],
    )
    def test_non_object_json_response_is_rejected(
        self,
        non_object_response: str,
    ) -> None:
        fake = FakeListTimesheets(non_object_response)

        with pytest.raises(
            TimesheetFinderError,
            match="doit être un objet JSON",
        ):
            find_timesheets_for_period(
                period=build_period(),
                resource_id="RESOURCE-123",
                auth_header="Bearer test-token",
                list_timesheets_fn=fake,
            )