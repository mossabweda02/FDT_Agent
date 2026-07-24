"""
Module: tests.diagnostics.test_phase1_intent_classification
===========================================================

Tests de diagnostic de la classification des intentions métier.

Ces tests comparent le comportement actuel du classificateur déterministe
avec les intentions attendues dans le catalogue des scénarios.

Les cas actuellement incorrects sont marqués xfail afin de conserver une
trace explicite des écarts sans bloquer la phase de diagnostic.
"""

from __future__ import annotations

import pytest

from backend.core.business.intent_classifier import classify_business_intent
from tests.diagnostics.scenario_cases import (
    SCENARIO_CASES,
    ScenarioCase,
    ScenarioStatus,
)


@pytest.mark.parametrize(
    "case",
    SCENARIO_CASES,
    ids=lambda case: f"{case.case_id}-{case.expected_intent.lower()}",
)
def test_business_intent_matches_reference(case: ScenarioCase) -> None:
    """Vérifie l'intention détectée pour chaque formulation utilisateur."""

    actual_intent = classify_business_intent(case.prompt)

    if (
        case.status != ScenarioStatus.VALID
        and actual_intent != case.expected_intent
    ):
        pytest.xfail(
            "Écart connu de classification : "
            f"attendu={case.expected_intent}, obtenu={actual_intent}"
        )

    assert actual_intent == case.expected_intent