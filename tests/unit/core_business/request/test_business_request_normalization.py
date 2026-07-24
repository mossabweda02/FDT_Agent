"""
Module: tests.diagnostics.test_business_request_normalization
================================================================

Tests de diagnostic de la normalisation des demandes métier.

Ce module teste la fonction normalize_business_request indépendamment
du LLM, de PydanticAI et des modèles métier complets.

Les objets utilisés dans les tests exposent uniquement les attributs
nécessaires à la normalisation :
- timesheet.explicit_date ;
- entries[].project ;
- entries[].task ;
- entries[].date.

Cette isolation permet d'identifier précisément les défauts de la logique
déterministe avant de diagnostiquer l'extraction structurée par le LLM.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from backend.core.business.structured_extractor import (
    normalize_business_request,
)


def make_entry(
    *,
    project: str | None = None,
    task: str | None = None,
    date: str | None = None,
) -> SimpleNamespace:
    """
    Construit une entrée minimale compatible avec le normaliseur.

    SimpleNamespace est utilisé volontairement afin de ne pas rendre ces
    tests dépendants de la structure complète du modèle BusinessRequest.
    """

    return SimpleNamespace(
        project=project,
        task=task,
        date=date,
    )


def make_business_request(
    *,
    explicit_date: str | None = None,
    entries: list[Any] | None = None,
) -> SimpleNamespace:
    """Construit une demande métier minimale pour les tests."""

    return SimpleNamespace(
        timesheet=SimpleNamespace(
            explicit_date=explicit_date,
        ),
        entries=entries or [],
    )


def test_normalizer_splits_combined_project_and_task_identifier() -> None:
    """
    Vérifie la séparation d'une référence PRJ-xxxxx/TSK-xxxxx.

    La partie projet doit être placée dans project et la partie tâche
    dans task.
    """

    entry = make_entry(
        project="PRJ-00042/TSK-00062",
        task=None,
    )
    request = make_business_request(entries=[entry])

    normalize_business_request(request)

    assert entry.project == "PRJ-00042"
    assert entry.task == "TSK-00062"


def test_normalizer_accepts_spaces_around_identifier_separator() -> None:
    """Vérifie que les espaces autour du séparateur sont tolérés."""

    entry = make_entry(
        project="prj-00042 / tsk-00062",
        task=None,
    )
    request = make_business_request(entries=[entry])

    normalize_business_request(request)

    assert entry.project == "PRJ-00042"
    assert entry.task == "TSK-00062"


def test_normalizer_propagates_common_explicit_date() -> None:
    """
    Vérifie la propagation de la date explicite commune.

    Une entrée sans date doit recevoir la date portée par le bloc
    timesheet de la demande.
    """

    first_entry = make_entry(
        project="PRJ-00042",
        task="TSK-00062",
        date=None,
    )
    second_entry = make_entry(
        project="PRJ-00051",
        task="TSK-00063",
        date=None,
    )
    request = make_business_request(
        explicit_date="2026-07-15",
        entries=[first_entry, second_entry],
    )

    normalize_business_request(request)

    assert first_entry.date == "2026-07-15"
    assert second_entry.date == "2026-07-15"


def test_normalizer_preserves_existing_entry_date() -> None:
    """
    Vérifie qu'une date propre à une entrée n'est pas écrasée.

    La date commune sert uniquement de valeur par défaut.
    """

    entry = make_entry(
        project="PRJ-00042",
        task="TSK-00062",
        date="2026-07-16",
    )
    request = make_business_request(
        explicit_date="2026-07-15",
        entries=[entry],
    )

    normalize_business_request(request)

    assert entry.date == "2026-07-16"


def test_normalizer_preserves_existing_task() -> None:
    """
    Vérifie qu'une tâche déjà renseignée n'est pas remplacée.

    Même si project contient un séparateur, le normaliseur actuel ne doit
    séparer la valeur que lorsque task est absente.
    """

    entry = make_entry(
        project="PRJ-00042/TSK-00062",
        task="TSK-00999",
    )
    request = make_business_request(entries=[entry])

    normalize_business_request(request)

    assert entry.project == "PRJ-00042/TSK-00062"
    assert entry.task == "TSK-00999"


@pytest.mark.parametrize(
    "project",
    [
        "Projet Alpha/Tâche Développement",
        "PRJ-ABC/TSK-XYZ",
        "PRJ-00042/",
        "/TSK-00062",
        "PRJ-00042/DEL-00010",
    ],
)
def test_normalizer_ignores_unsupported_combined_values(
    project: str,
) -> None:
    """
    Vérifie que les valeurs non conformes ne sont pas transformées.

    Le normaliseur ne doit pas inventer d'identifiant lorsque la chaîne
    ne correspond pas exactement à PRJ-nombres/TSK-nombres.
    """

    entry = make_entry(
        project=project,
        task=None,
    )
    request = make_business_request(entries=[entry])

    normalize_business_request(request)

    assert entry.project == project
    assert entry.task is None


def test_normalizer_handles_empty_entries() -> None:
    """Une demande sans entrée ne doit provoquer aucune erreur."""

    request = make_business_request(
        explicit_date="2026-07-15",
        entries=[],
    )

    normalize_business_request(request)

    assert request.entries == []


def test_normalizer_currently_mutates_request_in_place() -> None:
    """
    Documente le contrat actuel de la fonction.

    La fonction modifie directement l'objet reçu et ne retourne actuellement
    aucune valeur explicite.
    """

    entry = make_entry(
        project="PRJ-00042/TSK-00062",
        task=None,
    )
    request = make_business_request(entries=[entry])

    result = normalize_business_request(request)

    assert result is None
    assert request.entries[0].project == "PRJ-00042"
    assert request.entries[0].task == "TSK-00062"   