"""
Module: tests.diagnostics.test_scenario_detection
=================================================

Tests de diagnostic de la détection des scénarios métier.

Ce module vérifie le comportement du détecteur de scénarios indépendamment
du classificateur d'intentions. L'intention attendue est fournie directement
à detect_business_scenario afin d'isoler précisément cette couche.

Seuls les scénarios actuellement définis dans BusinessScenario sont testés.
Les écarts fonctionnels connus sont marqués xfail pendant la phase de
diagnostic et seront corrigés dans les phases suivantes.
"""

from __future__ import annotations

import pytest

from backend.core.business.business_types import BusinessScenario
from backend.core.business.scenario_detector import detect_business_scenario
from tests.diagnostics.scenario_cases import (
    SCENARIO_CASES,
    ScenarioCase,
    ScenarioStatus,
)


# La phase 1 mesure uniquement les scénarios déjà représentés dans le modèle
# de production. Les futurs scénarios, comme LIST_TIMESHEETS ou
# GET_TIMESHEET_TOTAL, seront ajoutés lors de leur phase fonctionnelle.
SUPPORTED_SCENARIOS = {
    scenario.value
    for scenario in BusinessScenario
    if scenario is not BusinessScenario.UNKNOWN_SCENARIO
}


SCENARIO_DETECTION_CASES = tuple(
    case
    for case in SCENARIO_CASES
    if case.expected_scenario in SUPPORTED_SCENARIOS
)


@pytest.mark.parametrize(
    "case",
    SCENARIO_DETECTION_CASES,
    ids=lambda case: f"{case.case_id}-{case.expected_scenario.lower()}",
)
def test_scenario_detection_matches_reference(case: ScenarioCase) -> None:
    """
    Vérifie le scénario détecté à partir de l'intention attendue.

    L'utilisation de case.expected_intent est volontaire : elle empêche
    qu'une erreur du classificateur masque une erreur du détecteur.
    """

    result = detect_business_scenario(
        message=case.prompt,
        intent=case.expected_intent,
    )

    actual_scenario = result.scenario.value

    if (
        case.status != ScenarioStatus.VALID
        and actual_scenario != case.expected_scenario
    ):
        pytest.xfail(
            "Écart connu de détection du scénario : "
            f"attendu={case.expected_scenario}, "
            f"obtenu={actual_scenario}, "
            f"raison={result.reason}"
        )

    assert actual_scenario == case.expected_scenario
    assert result.reason.strip(), (
        "Le détecteur doit fournir une raison exploitable "
        f"pour le scénario {case.case_id}."
    )


def test_unknown_intent_returns_unknown_scenario() -> None:
    """Une intention inconnue ne doit produire aucun scénario d'écriture."""

    result = detect_business_scenario(
        message="Effectue une opération inconnue.",
        intent=None,
    )

    assert result.scenario is BusinessScenario.UNKNOWN_SCENARIO
    assert result.reason.strip()


def test_unsupported_consultation_returns_unknown_scenario() -> None:
    """
    Documente le comportement actuel des consultations.

    CONSULT_TIMESHEET est une intention reconnue par le classificateur,
    mais aucun scénario de consultation n'est encore défini dans
    BusinessScenario.
    """

    result = detect_business_scenario(
        message="Affiche la liste de mes feuilles de temps.",
        intent="CONSULT_TIMESHEET",
    )

    assert result.scenario is BusinessScenario.UNKNOWN_SCENARIO
    assert result.reason.strip()