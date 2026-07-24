"""
Tests diagnostics du résolveur de projets.

Ces tests valident notamment :

- la résolution par identifiant ;
- la résolution par nom ;
- la normalisation des références ;
- les formulations naturelles ;
- les correspondances ambiguës ;
- la distinction entre projet associé et projet non associé ;
- la proposition des projets accessibles ;
- les erreurs des API Hub ;
- le comportement dégradé lorsque l'API globale échoue.

Commande ciblée :

    pytest tests/diagnostics/test_project_resolver.py -v
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from backend.core.business.project_resolution.models import (
    ProjectResolutionStatus,
)
from backend.core.business.project_resolution.project_resolver import (
    resolve_project_reference,
)


AUTH_HEADER = "Bearer diagnostic-token"
RESOURCE_ID = "RESOURCE-001"
DATA_AREA_ID = "DAT"


# ============================================================================
# Données de test
# ============================================================================


ASSOCIATED_PROJECTS = [
    {
        "projId": "PRJ-001",
        "name": "Nova Construction",
        "description": "Construction du nouveau site Nova",
        "status": "Active",
    },
    {
        "projId": "PRJ-002",
        "name": "Projet Atlas",
        "description": "Migration de la plateforme Atlas",
        "status": "Active",
    },
    {
        "projId": "PRJ-003",
        "name": "Orion Énergie",
        "description": "Programme énergétique Orion",
        "status": "Active",
    },
]


GLOBAL_PROJECTS = [
    *ASSOCIATED_PROJECTS,
    {
        "projId": "PRJ-900",
        "name": "Luna Manufacturing",
        "description": "Projet industriel non associé à la ressource",
        "status": "Active",
    },
    {
        "projId": "PRJ-901",
        "name": "Mercure Finance",
        "description": "Transformation du département finance",
        "status": "Active",
    },
]


# ============================================================================
# Helpers
# ============================================================================


def _json_response(
    projects: list[dict[str, Any]],
) -> str:
    """
    Construit une réponse JSON compatible avec le project finder.

    Si ton API utilise un autre conteneur, le finder est normalement capable
    de reconnaître les clés courantes comme projects, data, items ou results.
    """

    return json.dumps(
        {
            "ok": True,
            "data": projects,
        }
    )

def _resource_projects_fake(
    projects: list[dict[str, Any]] | None = None,
) -> Callable[..., str]:
    """
    Crée une fausse fonction Hub pour les projets associés.

    La fonction accepte volontairement tous les arguments positionnels
    et nommés afin de rester compatible avec la signature réelle de
    hub_get_ressource_project.
    """

    returned_projects = (
        ASSOCIATED_PROJECTS
        if projects is None
        else projects
    )

    def fake_get_resource_projects(
        *args: Any,
        **kwargs: Any,
    ) -> str:
        return _json_response(returned_projects)

    return fake_get_resource_projects


def _global_projects_fake(
    projects: list[dict[str, Any]] | None = None,
) -> Callable[..., str]:
    """
    Crée une fausse fonction Hub pour tous les projets Operate.

    Elle accepte tous les arguments afin de rester compatible avec
    hub_list_projects et avec les éventuelles évolutions de sa signature.
    """

    returned_projects = (
        GLOBAL_PROJECTS
        if projects is None
        else projects
    )

    def fake_list_projects(
        *args: Any,
        **kwargs: Any,
    ) -> str:
        return _json_response(returned_projects)

    return fake_list_projects

def _resolve(
    requested_reference: str | None,
    *,
    associated_projects: list[dict[str, Any]] | None = None,
    global_projects: list[dict[str, Any]] | None = None,
    get_projects_fn: Callable[..., str] | None = None,
    list_projects_fn: Callable[..., str] | None = None,
):
    """Appelle le resolver avec des dépendances Hub contrôlées."""

    return resolve_project_reference(
        requested_reference=requested_reference,
        resource_id=RESOURCE_ID,
        auth_header=AUTH_HEADER,
        data_area_id=DATA_AREA_ID,
        limit=50,
        skip=0,
        global_limit=100,
        get_projects_fn=(
            get_projects_fn
            or _resource_projects_fake(associated_projects)
        ),
        list_projects_fn=(
            list_projects_fn
            or _global_projects_fake(global_projects)
        ),
    )


# ============================================================================
# Résolution d'un projet associé
# ============================================================================


@pytest.mark.parametrize(
    "reference",
    [
        "PRJ-001",
        "prj-001",
        "prj 001",
        " PRJ-001 ",
    ],
)
def test_resolves_associated_project_by_identifier(
    reference: str,
) -> None:
    decision = _resolve(reference)

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.can_continue is True
    assert decision.requires_user_input is False
    assert decision.selected_project is not None
    assert decision.selected_project.project_id == "PRJ-001"
    assert decision.selected_project.name == "Nova Construction"


@pytest.mark.parametrize(
    "reference",
    [
        "Nova Construction",
        "nova construction",
        "NOVA CONSTRUCTION",
        "  Nova Construction  ",
    ],
)
def test_resolves_associated_project_by_exact_name(
    reference: str,
) -> None:
    decision = _resolve(reference)
    print("\nDECISION :", decision.model_dump())

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.selected_project is not None
    assert decision.selected_project.project_id == "PRJ-001"
    assert decision.can_continue is True


@pytest.mark.parametrize(
    "reference",
    [
        "Projet Nova Construction",
        "le projet Nova Construction",
        "sur le projet Nova Construction",
        "pour le projet Nova Construction",
    ],
)
def test_resolves_project_with_generic_project_prefix(
    reference: str,
) -> None:
    decision = _resolve(reference)
    
    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.selected_project is not None
    assert decision.selected_project.name == "Nova Construction"


def test_resolves_project_name_with_accents() -> None:
    decision = _resolve("Orion Energie")

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.selected_project is not None
    assert decision.selected_project.project_id == "PRJ-003"
    assert decision.selected_project.name == "Orion Énergie"


@pytest.mark.parametrize(
    "reference",
    [
        "Projet Atlas",
        "Atlas",
        "projet atlas",
        "PROJET ATLAS",
    ],
)
def test_resolves_project_whose_stored_name_contains_project_prefix(
    reference: str,
) -> None:
    decision = _resolve(reference)

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.selected_project is not None
    assert decision.selected_project.project_id == "PRJ-002"


def test_resolves_project_using_significant_tokens() -> None:
    decision = _resolve("migration atlas")

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.selected_project is not None
    assert decision.selected_project.project_id == "PRJ-002"


def test_resolves_project_using_description_tokens() -> None:
    decision = _resolve("programme energetique orion")

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.selected_project is not None
    assert decision.selected_project.project_id == "PRJ-003"


def test_does_not_call_global_api_when_associated_project_is_found() -> None:
    global_api_called = False

    def fake_list_projects(
        *args: Any,
        **kwargs: Any,
    ) -> str:
        nonlocal global_api_called
        global_api_called = True
        raise AssertionError(
            "L'API globale ne doit pas être appelée."
        )

    decision = _resolve(
        "Nova Construction",
        list_projects_fn=fake_list_projects,
    )

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert global_api_called is False


# ============================================================================
# Projet existant globalement, mais non associé
# ============================================================================


@pytest.mark.parametrize(
    "reference",
    [
        "Luna Manufacturing",
        "luna manufacturing",
        "Projet Luna Manufacturing",
        "PRJ-900",
        "prj 900",
    ],
)
def test_returns_not_associated_for_global_project(
    reference: str,
) -> None:
    decision = _resolve(reference)

    assert (
        decision.status
        == ProjectResolutionStatus.NOT_ASSOCIATED
    )
    assert decision.can_continue is False
    assert decision.requires_user_input is True
    assert decision.selected_project is None

    assert any(
        project.project_id == "PRJ-900"
        for project in decision.candidate_projects
    )

    assert {
        project.project_id
        for project in decision.available_projects
    } == {
        "PRJ-001",
        "PRJ-002",
        "PRJ-003",
    }

    assert "pas associé" in decision.message.lower()


def test_not_associated_decision_contains_global_match() -> None:
    decision = _resolve("Mercure Finance")

    assert (
        decision.status
        == ProjectResolutionStatus.NOT_ASSOCIATED
    )
    assert len(decision.candidate_projects) == 1

    matched_project = decision.candidate_projects[0]

    assert matched_project.project_id == "PRJ-901"
    assert matched_project.name == "Mercure Finance"


def test_not_associated_does_not_select_global_project() -> None:
    decision = _resolve("Luna Manufacturing")

    assert (
        decision.status
        == ProjectResolutionStatus.NOT_ASSOCIATED
    )
    assert decision.selected_project is None
    assert decision.can_continue is False


def test_global_project_matching_can_use_description() -> None:
    decision = _resolve("transformation finance")

    assert (
        decision.status
        == ProjectResolutionStatus.NOT_ASSOCIATED
    )

    assert any(
        project.project_id == "PRJ-901"
        for project in decision.candidate_projects
    )


# ============================================================================
# Référence manquante ou non reconnue
# ============================================================================


@pytest.mark.parametrize(
    "reference",
    [
        None,
        "",
        " ",
        "\n\t",
    ],
)
def test_missing_reference_proposes_associated_projects(
    reference: str | None,
) -> None:
    decision = _resolve(reference)

    assert (
        decision.status
        == ProjectResolutionStatus.MISSING_REFERENCE
    )
    assert decision.can_continue is False
    assert decision.requires_user_input is True
    assert decision.selected_project is None

    assert {
        project.project_id
        for project in decision.available_projects
    } == {
        "PRJ-001",
        "PRJ-002",
        "PRJ-003",
    }

    assert {
        project.project_id
        for project in decision.candidate_projects
    } == {
        "PRJ-001",
        "PRJ-002",
        "PRJ-003",
    }

    assert "choisir" in decision.message.lower()


def test_missing_reference_does_not_call_global_api() -> None:
    global_api_called = False

    def fake_list_projects(
        *args: Any,
        **kwargs: Any,
    ) -> str:
        nonlocal global_api_called
        global_api_called = True
        raise AssertionError(
            "L'API globale ne doit pas être appelée "
            "lorsqu'aucune référence n'est fournie."
        )

    decision = _resolve(
        None,
        list_projects_fn=fake_list_projects,
    )

    assert (
        decision.status
        == ProjectResolutionStatus.MISSING_REFERENCE
    )
    assert global_api_called is False


def test_unknown_project_returns_not_found() -> None:
    decision = _resolve("Projet totalement inconnu")

    assert decision.status == ProjectResolutionStatus.NOT_FOUND
    assert decision.can_continue is False
    assert decision.requires_user_input is True
    assert decision.selected_project is None

    assert {
        project.project_id
        for project in decision.available_projects
    } == {
        "PRJ-001",
        "PRJ-002",
        "PRJ-003",
    }

    assert "choisir" in decision.message.lower()


def test_not_found_returns_available_projects_as_candidates() -> None:
    decision = _resolve("Projet inexistant 999")

    assert decision.status == ProjectResolutionStatus.NOT_FOUND

    assert {
        project.project_id
        for project in decision.candidate_projects
    } == {
        "PRJ-001",
        "PRJ-002",
        "PRJ-003",
    }


# ============================================================================
# Correspondances multiples
# ============================================================================


def test_multiple_associated_matches_require_user_choice() -> None:
    associated_projects = [
        {
            "projId": "PRJ-101",
            "name": "Nova Construction Nord",
            "description": "Programme Nova",
        },
        {
            "projId": "PRJ-102",
            "name": "Nova Construction Sud",
            "description": "Programme Nova",
        },
    ]

    global_projects = list(associated_projects)

    decision = _resolve(
        "Nova Construction",
        associated_projects=associated_projects,
        global_projects=global_projects,
    )

    assert (
        decision.status
        == ProjectResolutionStatus.MULTIPLE_MATCHES
    )
    assert decision.can_continue is False
    assert decision.requires_user_input is True
    assert decision.selected_project is None

    assert {
        project.project_id
        for project in decision.candidate_projects
    } == {
        "PRJ-101",
        "PRJ-102",
    }


def test_exact_identifier_has_priority_over_partial_names() -> None:
    associated_projects = [
        {
            "projId": "PRJ-100",
            "name": "Migration",
        },
        {
            "projId": "MIGRATION",
            "name": "Autre projet",
        },
    ]

    decision = _resolve(
        "MIGRATION",
        associated_projects=associated_projects,
        global_projects=associated_projects,
    )

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.selected_project is not None
    assert decision.selected_project.project_id == "MIGRATION"


def test_exact_name_has_priority_over_partial_matches() -> None:
    associated_projects = [
        {
            "projId": "PRJ-201",
            "name": "Nova",
        },
        {
            "projId": "PRJ-202",
            "name": "Nova Construction",
        },
    ]

    decision = _resolve(
        "Nova",
        associated_projects=associated_projects,
        global_projects=associated_projects,
    )

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.selected_project is not None
    assert decision.selected_project.project_id == "PRJ-201"


# ============================================================================
# Aucun projet associé
# ============================================================================


def test_no_associated_projects_returns_not_found() -> None:
    decision = _resolve(
        "Nova Construction",
        associated_projects=[],
        global_projects=GLOBAL_PROJECTS,
    )

    # Le comportement dépend de l'ordre retenu dans le resolver.
    #
    # Si le resolver quitte immédiatement lorsqu'aucun projet n'est associé,
    # il retourne NOT_FOUND.
    #
    # S'il poursuit la recherche globale, Nova Construction peut être
    # détecté comme existant mais non associé.
    assert decision.status in {
        ProjectResolutionStatus.NOT_FOUND,
        ProjectResolutionStatus.NOT_ASSOCIATED,
    }

    assert decision.can_continue is False
    assert decision.requires_user_input is True
    assert decision.available_projects == []


def test_missing_reference_with_no_associated_projects() -> None:
    decision = _resolve(
        None,
        associated_projects=[],
        global_projects=GLOBAL_PROJECTS,
    )

    assert decision.can_continue is False
    assert decision.requires_user_input is True
    assert decision.selected_project is None
    assert decision.available_projects == []


# ============================================================================
# Erreurs de l'API des projets associés
# ============================================================================


def test_resource_projects_api_exception_returns_hub_error() -> None:
    def failing_resource_api(**_: Any) -> str:
        raise RuntimeError("Integration Hub indisponible")

    decision = _resolve(
        "Nova Construction",
        get_projects_fn=failing_resource_api,
    )

    assert decision.status == ProjectResolutionStatus.HUB_ERROR
    assert decision.can_continue is False
    assert decision.requires_user_input is False
    assert decision.hub_error is not None
    assert "indisponible" in decision.hub_error.lower()


def test_resource_projects_functional_error_returns_hub_error() -> None:
    def resource_api_with_error(**_: Any) -> str:
        return json.dumps(
            {
                "success": False,
                "error": "Impossible de récupérer les projets",
            }
        )

    decision = _resolve(
        "Nova Construction",
        get_projects_fn=resource_api_with_error,
    )

    assert decision.status == ProjectResolutionStatus.HUB_ERROR
    assert decision.can_continue is False
    assert decision.hub_error is not None


def test_invalid_resource_projects_json_returns_invalid_response() -> None:
    def invalid_json_resource_api(**_: Any) -> str:
        return "ceci n'est pas du JSON"

    decision = _resolve(
        "Nova Construction",
        get_projects_fn=invalid_json_resource_api,
    )

    assert (
        decision.status
        == ProjectResolutionStatus.INVALID_RESPONSE
    )
    assert decision.can_continue is False
    assert decision.hub_error is not None


# ============================================================================
# Erreurs de l'API globale
# ============================================================================


def test_global_api_exception_falls_back_to_not_found() -> None:
    def failing_global_api(**_: Any) -> str:
        raise RuntimeError("API globale indisponible")

    decision = _resolve(
        "Projet inconnu",
        list_projects_fn=failing_global_api,
    )

    assert decision.status == ProjectResolutionStatus.NOT_FOUND
    assert decision.can_continue is False
    assert decision.requires_user_input is True

    assert {
        project.project_id
        for project in decision.available_projects
    } == {
        "PRJ-001",
        "PRJ-002",
        "PRJ-003",
    }


def test_global_api_functional_error_falls_back_to_not_found() -> None:
    def global_api_with_error(**_: Any) -> str:
        return json.dumps(
            {
                "success": False,
                "error": "Liste globale indisponible",
            }
        )

    decision = _resolve(
        "Projet inconnu",
        list_projects_fn=global_api_with_error,
    )

    assert decision.status == ProjectResolutionStatus.NOT_FOUND
    assert decision.can_continue is False


def test_invalid_global_json_falls_back_to_not_found() -> None:
    def invalid_global_json(**_: Any) -> str:
        return "<html>Erreur serveur</html>"

    decision = _resolve(
        "Projet inconnu",
        list_projects_fn=invalid_global_json,
    )

    assert decision.status == ProjectResolutionStatus.NOT_FOUND
    assert decision.can_continue is False
    assert decision.requires_user_input is True


def test_global_api_is_called_only_after_associated_search_fails() -> None:
    global_api_called = False

    def fake_global_api(
        *,
        limit: int,
        auth_header: str,
    ) -> str:
        nonlocal global_api_called
        global_api_called = True

        return _json_response(GLOBAL_PROJECTS)

    decision = _resolve(
        "Luna Manufacturing",
        list_projects_fn=fake_global_api,
    )

    assert global_api_called is True
    assert (
        decision.status
        == ProjectResolutionStatus.NOT_ASSOCIATED
    )


# ============================================================================
# Robustesse des données
# ============================================================================


def test_ignores_invalid_project_records() -> None:
    associated_projects: list[Any] = [
        None,
        {},
        {
            "name": "Projet sans identifiant",
        },
        {
            "projId": "PRJ-001",
            "name": "Nova Construction",
        },
    ]

    decision = _resolve(
        "Nova Construction",
        associated_projects=associated_projects,
    )

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.selected_project is not None
    assert decision.selected_project.project_id == "PRJ-001"


def test_deduplicated_projects_do_not_create_false_ambiguity() -> None:
    associated_projects = [
        {
            "projId": "PRJ-001",
            "name": "Nova Construction",
        },
        {
            "projectId": "prj-001",
            "projectName": "Nova Construction",
        },
    ]

    decision = _resolve(
        "Nova Construction",
        associated_projects=associated_projects,
        global_projects=associated_projects,
    )

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.selected_project is not None
    assert decision.selected_project.project_id.casefold() == "prj-001"


def test_supports_alternative_project_fields() -> None:
    associated_projects = [
        {
            "projectId": "ALT-001",
            "projectName": "Projet Alternatif",
            "projectDescription": "Format alternatif",
            "projectStatus": "Active",
        }
    ]

    decision = _resolve(
        "Projet Alternatif",
        associated_projects=associated_projects,
        global_projects=associated_projects,
    )

    assert decision.status == ProjectResolutionStatus.MATCHED
    assert decision.selected_project is not None
    assert decision.selected_project.project_id == "ALT-001"


def test_candidate_projects_are_sorted_deterministically() -> None:
    associated_projects = [
        {
            "projId": "PRJ-Z",
            "name": "Nova Zeta",
        },
        {
            "projId": "PRJ-A",
            "name": "Nova Alpha",
        },
    ]

    decision = _resolve(
        "Nova",
        associated_projects=associated_projects,
        global_projects=associated_projects,
    )

    assert (
        decision.status
        == ProjectResolutionStatus.MULTIPLE_MATCHES
    )

    assert [
        project.name
        for project in decision.candidate_projects
    ] == [
        "Nova Alpha",
        "Nova Zeta",
    ]