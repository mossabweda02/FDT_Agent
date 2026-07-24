"""
Tests de diagnostic du service de résolution des feuilles de temps.

Ces tests décrivent le contrat attendu de resolution_service.py avant
son implémentation.

Le service doit orchestrer :

1. la référence de feuille extraite dans BusinessRequest ;
2. la résolution déterministe de la période ;
3. la recherche des feuilles correspondantes ;
4. la décision métier à transmettre au workflow.

Aucun appel réel au LLM ou à Integration Hub n'est effectué.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import pytest

from backend.core.business.business_request import (
    ActionContext,
    BusinessRequest,
    TimesheetReference,
)
from backend.core.business.timesheet_resolution.resolution_service import (
    TimesheetResolutionDecision,
    TimesheetResolutionStatus,
    resolve_timesheet_reference,
)


REFERENCE_DATE = date(2026, 7, 21)


def build_request(
    *,
    intent: str = "ADD_TIME_ENTRY",
    period_mode: str = "current_week",
    number: str | None = None,
    explicit_date: str | None = None,
    explicit_start_date: str | None = None,
    explicit_end_date: str | None = None,
) -> BusinessRequest:
    """Construit une demande métier minimale pour les tests."""

    return BusinessRequest(
        action=ActionContext(
            intent=intent,
            scenario="SINGLE_TIME_ENTRY",
            requires_confirmation=True,
            user_confirmation_detected=False,
        ),
        timesheet=TimesheetReference(
            number=number,
            period_mode=period_mode,
            explicit_date=explicit_date,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
        ),
    )


def build_hub_response(
    *,
    ok: bool = True,
    data: Any = None,
    error: str | None = None,
    hint: str | None = None,
) -> str:
    """Construit une réponse Hub JSON simulée."""

    return json.dumps(
        {
            "ok": ok,
            "data": data,
            "error": error,
            "hint": hint,
        }
    )


class FakeListTimesheets:
    """Fonction Hub simulée enregistrant les appels reçus."""

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


class TestProvidedTimesheetNumber:
    """Tests de la résolution directe par numéro de feuille."""

    def test_uses_explicit_timesheet_number_without_hub_search(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        request = build_request(
            number="TS-0000319",
            period_mode="timesheet_number",
        )

        result = resolve_timesheet_reference(
            business_request=request,
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.USE_PROVIDED_TIMESHEET
        )
        assert result.selected_timesheet_number == "TS-0000319"
        assert result.resolved_period is None
        assert result.lookup_result is None
        assert result.requires_user_input is False
        assert result.can_continue is True
        assert fake.calls == []

    def test_number_has_priority_over_period_mode(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        request = build_request(
            number="TS-0000456",
            period_mode="current_week",
        )

        result = resolve_timesheet_reference(
            business_request=request,
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.USE_PROVIDED_TIMESHEET
        )
        assert result.selected_timesheet_number == "TS-0000456"
        assert fake.calls == []

    def test_blank_number_does_not_count_as_explicit_reference(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        request = build_request(
            number="   ",
            period_mode="current_week",
        )

        result = resolve_timesheet_reference(
            business_request=request,
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.CREATE_NEW_TIMESHEET
        )
        assert len(fake.calls) == 1


class TestSingleTimesheetFound:
    """Tests du cas où une seule feuille correspond à la période."""

    def test_selects_unique_existing_timesheet(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                data=[
                    {
                        "timesheetNbr": "TS-CURRENT",
                        "periodStart": "2026-07-20",
                        "periodEnd": "2026-07-26",
                        "status": "Open",
                    }
                ]
            )
        )

        result = resolve_timesheet_reference(
            business_request=build_request(),
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.USE_EXISTING_TIMESHEET
        )
        assert result.selected_timesheet_number == "TS-CURRENT"
        assert result.selected_timesheet is not None
        assert result.selected_timesheet.status == "Open"

        assert result.resolved_period is not None
        assert result.resolved_period.start_date == date(2026, 7, 20)
        assert result.resolved_period.end_date == date(2026, 7, 26)

        assert result.lookup_result is not None
        assert result.lookup_result.count == 1

        assert result.requires_user_input is False
        assert result.can_continue is True
        assert result.message is not None

    @pytest.mark.parametrize(
        (
            "period_mode",
            "expected_start",
            "expected_end",
        ),
        [
            (
                "today",
                date(2026, 7, 20),
                date(2026, 7, 26),
            ),
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
    def test_resolves_supported_period_before_search(
        self,
        period_mode: str,
        expected_start: date,
        expected_end: date,
    ) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                data=[
                    {
                        "timesheetNbr": "TS-MATCH",
                        "periodStart": expected_start.isoformat(),
                        "periodEnd": expected_end.isoformat(),
                    }
                ]
            )
        )

        result = resolve_timesheet_reference(
            business_request=build_request(
                period_mode=period_mode,
            ),
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.USE_EXISTING_TIMESHEET
        )
        assert result.resolved_period is not None
        assert result.resolved_period.start_date == expected_start
        assert result.resolved_period.end_date == expected_end


class TestNoTimesheetFound:
    """Tests du cas où aucune feuille ne correspond à la période."""

    @pytest.mark.parametrize(
        "intent",
        [
            "CREATE_TIMESHEET",
            "ADD_TIME_ENTRY",
            "ADD_MULTIPLE_TIME_ENTRIES",
            "UPDATE_TIME_ENTRY",
            "CONSULT_TIMESHEET",
        ],
    )
    def test_proposes_creation_when_no_timesheet_exists(
        self,
        intent: str,
    ) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        result = resolve_timesheet_reference(
            business_request=build_request(intent=intent),
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.CREATE_NEW_TIMESHEET
        )
        assert result.selected_timesheet is None
        assert result.selected_timesheet_number is None

        assert result.resolved_period is not None
        assert result.lookup_result is not None
        assert result.lookup_result.count == 0

        assert result.requires_user_input is True
        assert result.can_continue is False
        assert result.message is not None

    def test_does_not_create_anything_automatically(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        result = resolve_timesheet_reference(
            business_request=build_request(
                intent="CREATE_TIMESHEET",
            ),
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.CREATE_NEW_TIMESHEET
        )
        assert result.can_continue is False
        assert result.requires_user_input is True


class TestMultipleTimesheetsFound:
    """Tests du cas où plusieurs feuilles correspondent à la période."""

    def test_requires_user_choice_when_multiple_timesheets_match(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                data=[
                    {
                        "timesheetNbr": "TS-001",
                        "periodStart": "2026-07-20",
                        "periodEnd": "2026-07-26",
                    },
                    {
                        "timesheetNbr": "TS-002",
                        "periodStart": "2026-07-20",
                        "periodEnd": "2026-07-26",
                    },
                ]
            )
        )

        result = resolve_timesheet_reference(
            business_request=build_request(),
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.ASK_USER_TO_CHOOSE
        )
        assert result.selected_timesheet is None
        assert result.selected_timesheet_number is None

        assert result.lookup_result is not None
        assert result.lookup_result.count == 2

        assert result.requires_user_input is True
        assert result.can_continue is False
        assert result.message is not None

        assert [
            timesheet.number
            for timesheet in result.candidate_timesheets
        ] == [
            "TS-001",
            "TS-002",
        ]


class TestHubFailures:
    """Tests de propagation contrôlée des erreurs Integration Hub."""

    def test_returns_retry_later_when_hub_returns_error(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                ok=False,
                error="Timeout Integration Hub",
                hint="Le service ne répond pas",
            )
        )

        result = resolve_timesheet_reference(
            business_request=build_request(),
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == TimesheetResolutionStatus.RETRY_LATER
        assert result.hub_error == (
            "Timeout Integration Hub — Le service ne répond pas"
        )
        assert result.selected_timesheet is None
        assert result.requires_user_input is False
        assert result.can_continue is False
        assert result.message is not None

    def test_does_not_convert_hub_error_into_no_match(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(
                ok=False,
                error="Service indisponible",
            )
        )

        result = resolve_timesheet_reference(
            business_request=build_request(),
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status != (
            TimesheetResolutionStatus.CREATE_NEW_TIMESHEET
        )
        assert result.status == TimesheetResolutionStatus.RETRY_LATER


class TestInvalidRequests:
    """Tests des références temporelles absentes ou invalides."""

    def test_unknown_period_returns_invalid_request(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        result = resolve_timesheet_reference(
            business_request=build_request(
                period_mode="unknown",
            ),
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.INVALID_REQUEST
        )
        assert result.resolved_period is None
        assert result.lookup_result is None
        assert result.requires_user_input is True
        assert result.can_continue is False
        assert result.message is not None
        assert fake.calls == []

    def test_explicit_date_requires_a_date_value(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        result = resolve_timesheet_reference(
            business_request=build_request(
                period_mode="explicit_date",
                explicit_date=None,
            ),
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.INVALID_REQUEST
        )
        assert result.can_continue is False
        assert fake.calls == []

    def test_invalid_explicit_date_returns_invalid_request(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        result = resolve_timesheet_reference(
            business_request=build_request(
                period_mode="explicit_date",
                explicit_date="21/07/2026",
            ),
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.INVALID_REQUEST
        )
        assert result.can_continue is False
        assert fake.calls == []

    def test_invalid_explicit_range_returns_invalid_request(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        result = resolve_timesheet_reference(
            business_request=build_request(
                period_mode="explicit_range",
                explicit_start_date="2026-07-24",
                explicit_end_date="2026-07-20",
            ),
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.INVALID_REQUEST
        )
        assert result.can_continue is False
        assert fake.calls == []

    def test_missing_resource_id_returns_invalid_request(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        result = resolve_timesheet_reference(
            business_request=build_request(),
            resource_id="",
            auth_header="Bearer token",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.INVALID_REQUEST
        )
        assert result.can_continue is False
        assert fake.calls == []

    def test_missing_auth_header_returns_invalid_request(self) -> None:
        fake = FakeListTimesheets(
            build_hub_response(data=[])
        )

        result = resolve_timesheet_reference(
            business_request=build_request(),
            resource_id="RESOURCE-123",
            auth_header="",
            reference_date=REFERENCE_DATE,
            list_timesheets_fn=fake,
        )

        assert result.status == (
            TimesheetResolutionStatus.INVALID_REQUEST
        )
        assert result.can_continue is False
        assert fake.calls == []


class TestServiceResultContract:
    """Tests du contrat de sortie commun à toutes les décisions."""

    @pytest.mark.parametrize(
        (
            "status",
            "requires_user_input",
            "can_continue",
        ),
        [
            (
                TimesheetResolutionStatus.USE_PROVIDED_TIMESHEET,
                False,
                True,
            ),
            (
                TimesheetResolutionStatus.USE_EXISTING_TIMESHEET,
                False,
                True,
            ),
            (
                TimesheetResolutionStatus.CREATE_NEW_TIMESHEET,
                True,
                False,
            ),
            (
                TimesheetResolutionStatus.ASK_USER_TO_CHOOSE,
                True,
                False,
            ),
            (
                TimesheetResolutionStatus.RETRY_LATER,
                False,
                False,
            ),
            (
                TimesheetResolutionStatus.REQUIRES_CLARIFICATION,
                True,
                False,
            ),
            (
                TimesheetResolutionStatus.INVALID_REQUEST,
                True,
                False,
            ),
        ],
    )
    def test_decision_model_accepts_all_supported_statuses(
        self,
        status: TimesheetResolutionStatus,
        requires_user_input: bool,
        can_continue: bool,
    ) -> None:
        decision = TimesheetResolutionDecision(
            status=status,
            requires_user_input=requires_user_input,
            can_continue=can_continue,
            message="Message de test.",
        )

        assert decision.status == status
        assert decision.requires_user_input is requires_user_input
        assert decision.can_continue is can_continue
        assert decision.candidate_timesheets == []  