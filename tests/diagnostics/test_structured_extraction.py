"""
Module: tests.diagnostics.test_structured_extraction
====================================================

Tests déterministes de l'extraction structurée des demandes métier.

Ce module vérifie le contrat technique de extract_business_request sans
effectuer d'appel réel à un modèle LLM. La classe pydantic_ai.Agent est
remplacée par un faux agent contrôlé par les tests.

Les tests valident notamment :
- la configuration de l'agent ;
- la construction du prompt d'extraction ;
- la récupération du BusinessRequest ;
- le complément de l'intention et du scénario lorsqu'ils restent inconnus ;
- la conservation des données structurées produites par l'extracteur.

La qualité sémantique réelle du modèle sera vérifiée séparément dans des
tests d'intégration LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

import pytest

from backend.core.business.business_request import (
    ActionContext,
    BusinessRequest,
    TimeEntryRequest,
    TimesheetReference,
)
from backend.core.business import structured_extractor


@pytest.fixture
def anyio_backend() -> str:
    """
    Force pytest-anyio à utiliser asyncio.

    Le projet utilise déjà le plugin anyio. Cette fixture évite que les tests
    soient également exécutés avec un backend asynchrone non installé.
    """

    return "asyncio"


@dataclass
class FakeRunResult:
    """Résultat minimal reproduisant l'interface retournée par Agent.run."""

    output: BusinessRequest


class FakeAgent:
    """
    Faux agent PydanticAI utilisé pour isoler extract_business_request.

    Le BusinessRequest retourné est défini avant chaque test via
    configure_output(). Les paramètres reçus par le constructeur et le prompt
    transmis à run() sont conservés pour permettre leur vérification.
    """

    configured_output: ClassVar[BusinessRequest | None] = None
    last_model: ClassVar[Any] = None
    last_system_prompt: ClassVar[str | None] = None
    last_output_type: ClassVar[type[Any] | None] = None
    last_run_prompt: ClassVar[str | None] = None

    def __init__(
        self,
        *,
        model: Any,
        system_prompt: str,
        output_type: type[Any],
    ) -> None:
        self.__class__.last_model = model
        self.__class__.last_system_prompt = system_prompt
        self.__class__.last_output_type = output_type

    async def run(self, prompt: str) -> FakeRunResult:
        """Retourne le résultat configuré sans appeler de modèle externe."""

        self.__class__.last_run_prompt = prompt

        if self.__class__.configured_output is None:
            raise AssertionError(
                "FakeAgent.configure_output() doit être appelé avant "
                "extract_business_request()."
            )

        return FakeRunResult(output=self.__class__.configured_output)

    @classmethod
    def configure_output(cls, output: BusinessRequest) -> None:
        """Configure le BusinessRequest qui sera retourné par run()."""

        cls.configured_output = output

    @classmethod
    def reset(cls) -> None:
        """Réinitialise l'état partagé entre les tests."""

        cls.configured_output = None
        cls.last_model = None
        cls.last_system_prompt = None
        cls.last_output_type = None
        cls.last_run_prompt = None


@pytest.fixture(autouse=True)
def replace_pydantic_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Remplace Agent par FakeAgent pendant chaque test.

    Le patch cible structured_extractor.Agent, car Agent est importé
    directement dans ce module de production.
    """

    FakeAgent.reset()

    monkeypatch.setattr(
        structured_extractor,
        "Agent",
        FakeAgent,
    )


@pytest.mark.anyio
async def test_extractor_configures_agent_for_business_request() -> None:
    """Vérifie la configuration du contrat de sortie de l'agent."""

    expected_request = BusinessRequest(
        action=ActionContext(
            intent="CREATE_TIMESHEET",
            scenario="CREATE_EMPTY_TIMESHEET",
            requires_confirmation=True,
        ),
        timesheet=TimesheetReference(
            period_mode="today",
        ),
    )
    FakeAgent.configure_output(expected_request)

    fake_model = object()

    result = await structured_extractor.extract_business_request(
        message="Crée ma feuille de temps pour aujourd'hui.",
        intent="CREATE_TIMESHEET",
        scenario="CREATE_EMPTY_TIMESHEET",
        model=fake_model,
    )

    assert result is expected_request
    assert FakeAgent.last_model is fake_model
    assert FakeAgent.last_output_type is BusinessRequest
    assert (
        FakeAgent.last_system_prompt
        == structured_extractor.STRUCTURED_EXTRACTION_PROMPT
    )


@pytest.mark.anyio
async def test_extractor_includes_detection_and_context_in_prompt() -> None:
    """
    Vérifie que toutes les informations disponibles sont transmises au LLM.

    Le contexte utilisateur et le contexte temporel doivent être présents dans
    le prompt d'extraction afin de permettre une interprétation cohérente.
    """

    expected_request = BusinessRequest()
    FakeAgent.configure_output(expected_request)

    await structured_extractor.extract_business_request(
        message=(
            "Ajoute 3h sur PRJ-00042/TSK-00062 "
            "dans la feuille TS-0000318."
        ),
        intent="ADD_TIME_ENTRY",
        scenario="SINGLE_TIME_ENTRY",
        model=object(),
        user_context={
            "resource_id": "RES-00125",
            "display_name": "Utilisateur Test",
        },
        date_context={
            "today": "2026-07-21",
            "current_week_start": "2026-07-20",
        },
    )

    prompt = FakeAgent.last_run_prompt

    assert prompt is not None
    assert "Ajoute 3h sur PRJ-00042/TSK-00062" in prompt
    assert "ADD_TIME_ENTRY" in prompt
    assert "SINGLE_TIME_ENTRY" in prompt
    assert "RES-00125" in prompt
    assert "Utilisateur Test" in prompt
    assert "2026-07-21" in prompt
    assert "2026-07-20" in prompt


@pytest.mark.anyio
async def test_extractor_backfills_unknown_intent() -> None:
    """
    Vérifie le complément de l'intention détectée en amont.

    Lorsque le modèle laisse action.intent à UNKNOWN, l'intention déjà
    déterminée par le classificateur doit être réutilisée.
    """

    extracted_request = BusinessRequest(
        action=ActionContext(
            intent="UNKNOWN",
            scenario="SINGLE_TIME_ENTRY",
        ),
        entries=[
            TimeEntryRequest(
                project="PRJ-00042",
                task="TSK-00062",
                hours=3,
            )
        ],
    )
    FakeAgent.configure_output(extracted_request)

    result = await structured_extractor.extract_business_request(
        message="Ajoute 3h sur PRJ-00042/TSK-00062.",
        intent="ADD_TIME_ENTRY",
        scenario="SINGLE_TIME_ENTRY",
        model=object(),
    )

    assert result.action.intent == "ADD_TIME_ENTRY"
    assert result.action.scenario == "SINGLE_TIME_ENTRY"


@pytest.mark.anyio
async def test_extractor_backfills_unknown_scenario() -> None:
    """
    Vérifie le complément du scénario détecté en amont.

    Lorsque le modèle laisse le scénario inconnu, le scénario déterminé par
    scenario_detector doit être conservé dans le résultat.
    """

    extracted_request = BusinessRequest(
        action=ActionContext(
            intent="ADD_TIME_ENTRY",
            scenario="UNKNOWN_SCENARIO",
        ),
        entries=[
            TimeEntryRequest(
                project="PRJ-00042",
                task="TSK-00062",
                hours=3,
            )
        ],
    )
    FakeAgent.configure_output(extracted_request)

    result = await structured_extractor.extract_business_request(
        message="Ajoute 3h sur PRJ-00042/TSK-00062.",
        intent="ADD_TIME_ENTRY",
        scenario="SINGLE_TIME_ENTRY",
        model=object(),
    )

    assert result.action.intent == "ADD_TIME_ENTRY"
    assert result.action.scenario == "SINGLE_TIME_ENTRY"


@pytest.mark.anyio
async def test_extractor_preserves_existing_action_values() -> None:
    """
    Vérifie que les valeurs non inconnues produites par le modèle sont gardées.

    La logique actuelle ne remplace l'intention et le scénario que lorsqu'ils
    possèdent leurs valeurs UNKNOWN respectives.
    """

    extracted_request = BusinessRequest(
        action=ActionContext(
            intent="ADD_MULTIPLE_TIME_ENTRIES",
            scenario="MULTI_TASK_SAME_PROJECT",
        ),
    )
    FakeAgent.configure_output(extracted_request)

    result = await structured_extractor.extract_business_request(
        message="Ajoute plusieurs lignes.",
        intent="ADD_TIME_ENTRY",
        scenario="SINGLE_TIME_ENTRY",
        model=object(),
    )

    assert result.action.intent == "ADD_MULTIPLE_TIME_ENTRIES"
    assert result.action.scenario == "MULTI_TASK_SAME_PROJECT"


@pytest.mark.anyio
async def test_extractor_preserves_complete_single_entry() -> None:
    """Vérifie la conservation d'une ligne de temps complètement extraite."""

    extracted_request = BusinessRequest(
        action=ActionContext(
            intent="ADD_TIME_ENTRY",
            scenario="SINGLE_TIME_ENTRY",
            requires_confirmation=True,
        ),
        timesheet=TimesheetReference(
            number="TS-0000318",
            period_mode="timesheet_number",
        ),
        entries=[
            TimeEntryRequest(
                project="PRJ-00042",
                task="TSK-00062",
                category="Development",
                deliverable="API Timesheet",
                hours=3.5,
                date="2026-07-21",
            )
        ],
    )
    FakeAgent.configure_output(extracted_request)

    result = await structured_extractor.extract_business_request(
        message=(
            "Dans la feuille TS-0000318, ajoute 3,5h le 21 juillet 2026 "
            "sur PRJ-00042/TSK-00062, catégorie Development, "
            "livrable API Timesheet."
        ),
        intent="ADD_TIME_ENTRY",
        scenario="SINGLE_TIME_ENTRY",
        model=object(),
    )

    assert result.timesheet.number == "TS-0000318"
    assert result.timesheet.period_mode == "timesheet_number"
    assert len(result.entries) == 1

    entry = result.entries[0]

    assert entry.project == "PRJ-00042"
    assert entry.task == "TSK-00062"
    assert entry.category == "Development"
    assert entry.deliverable == "API Timesheet"
    assert entry.hours == 3.5
    assert entry.date == "2026-07-21"
    assert result.action.requires_confirmation is True


@pytest.mark.anyio
async def test_extractor_preserves_multiple_entries() -> None:
    """Vérifie la conservation de plusieurs lignes structurées."""

    extracted_request = BusinessRequest(
        action=ActionContext(
            intent="ADD_MULTIPLE_TIME_ENTRIES",
            scenario="MULTI_TASK_SAME_PROJECT",
            requires_confirmation=True,
        ),
        timesheet=TimesheetReference(
            number="TS-0000318",
            period_mode="timesheet_number",
        ),
        entries=[
            TimeEntryRequest(
                project="PRJ-00042",
                task="TSK-00062",
                hours=2,
                date="2026-07-21",
            ),
            TimeEntryRequest(
                project="PRJ-00042",
                task="TSK-00063",
                hours=3,
                date="2026-07-21",
            ),
        ],
    )
    FakeAgent.configure_output(extracted_request)

    result = await structured_extractor.extract_business_request(
        message=(
            "Dans la feuille TS-0000318, ajoute 2h sur "
            "PRJ-00042/TSK-00062 et 3h sur PRJ-00042/TSK-00063."
        ),
        intent="ADD_MULTIPLE_TIME_ENTRIES",
        scenario="MULTI_TASK_SAME_PROJECT",
        model=object(),
    )

    assert len(result.entries) == 2
    assert result.entries[0].task == "TSK-00062"
    assert result.entries[0].hours == 2
    assert result.entries[1].task == "TSK-00063"
    assert result.entries[1].hours == 3


@pytest.mark.anyio
async def test_extractor_preserves_timesheet_based_repetition() -> None:
    """
    Vérifie le contrat d'une répétition liée à la période réelle d'une feuille.

    Les dates exactes ne doivent pas être inventées lorsque la répétition doit
    être calculée après récupération de la feuille.
    """

    extracted_request = BusinessRequest(
        action=ActionContext(
            intent="ADD_MULTIPLE_TIME_ENTRIES",
            scenario="REPEAT_ENTRY_OVER_DATE_RANGE",
            requires_confirmation=True,
        ),
        timesheet=TimesheetReference(
            number="TS-0000318",
            period_mode="timesheet_number",
        ),
        entries=[
            TimeEntryRequest(
                project="PRJ-00042",
                task="TSK-00062",
                hours=2,
                date=None,
                repeat_type="weekday_range",
                dates_must_be_resolved_from_timesheet=True,
            )
        ],
    )
    FakeAgent.configure_output(extracted_request)

    result = await structured_extractor.extract_business_request(
        message=(
            "Dans la feuille TS-0000318, ajoute 2h du lundi au vendredi "
            "sur PRJ-00042/TSK-00062."
        ),
        intent="ADD_MULTIPLE_TIME_ENTRIES",
        scenario="REPEAT_ENTRY_OVER_DATE_RANGE",
        model=object(),
    )

    assert len(result.entries) == 1

    entry = result.entries[0]

    assert entry.date is None
    assert entry.repeat_type == "weekday_range"
    assert entry.dates_must_be_resolved_from_timesheet is True


@pytest.mark.anyio
async def test_extractor_preserves_missing_information() -> None:
    """Vérifie la conservation des informations nécessaires mais absentes."""

    extracted_request = BusinessRequest(
        action=ActionContext(
            intent="ADD_TIME_ENTRY",
            scenario="SINGLE_TIME_ENTRY",
        ),
        entries=[
            TimeEntryRequest(
                project="PRJ-00042",
                task="TSK-00062",
                hours=3,
                category=None,
            )
        ],
        missing_information=["category"],
    )
    FakeAgent.configure_output(extracted_request)

    result = await structured_extractor.extract_business_request(
        message="Ajoute 3h sur PRJ-00042/TSK-00062.",
        intent="ADD_TIME_ENTRY",
        scenario="SINGLE_TIME_ENTRY",
        model=object(),
    )

    assert result.missing_information == ["category"]
    assert result.entries[0].category is None


@pytest.mark.anyio
async def test_extractor_preserves_ambiguity_notes() -> None:
    """Vérifie la conservation des ambiguïtés détectées dans la demande."""

    extracted_request = BusinessRequest(
        action=ActionContext(
            intent="CREATE_TIMESHEET",
            scenario="CREATE_EMPTY_TIMESHEET",
        ),
        timesheet=TimesheetReference(
            period_mode="unknown",
        ),
        ambiguity_notes=[
            "La période demandée n'est pas suffisamment précise."
        ],
    )
    FakeAgent.configure_output(extracted_request)

    result = await structured_extractor.extract_business_request(
        message="Crée ma prochaine feuille de temps.",
        intent="CREATE_TIMESHEET",
        scenario="CREATE_EMPTY_TIMESHEET",
        model=object(),
    )

    assert result.timesheet.period_mode == "unknown"
    assert result.ambiguity_notes == [
        "La période demandée n'est pas suffisamment précise."
    ]


@pytest.mark.anyio
async def test_extractor_preserves_confirmation_detection() -> None:
    """Vérifie la conservation d'une confirmation utilisateur détectée."""

    extracted_request = BusinessRequest(
        action=ActionContext(
            intent="CONFIRM_ACTION",
            scenario="UNKNOWN_SCENARIO",
            requires_confirmation=False,
            user_confirmation_detected=True,
        ),
    )
    FakeAgent.configure_output(extracted_request)

    result = await structured_extractor.extract_business_request(
        message="Oui, je confirme.",
        intent="CONFIRM_ACTION",
        scenario="UNKNOWN_SCENARIO",
        model=object(),
    )

    assert result.action.intent == "CONFIRM_ACTION"
    assert result.action.user_confirmation_detected is True
    assert result.action.requires_confirmation is False