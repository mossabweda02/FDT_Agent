"""
Tests de diagnostic du Project Finder.

Cette suite valide le composant chargé de récupérer et normaliser
les projets associés à une ressource.

Aucun appel réel à Integration Hub n'est effectué.

Les tests couvrent :

- la transmission des paramètres au Hub ;
- les différents formats de réponse ;
- la normalisation des projets ;
- le tri déterministe ;
- la suppression des doublons ;
- les données invalides ou incomplètes ;
- les erreurs fonctionnelles du Hub ;
- les réponses JSON invalides.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from backend.core.business.project_resolution.project_finder import (
    ProjectFinderError,
    find_resource_projects,
)


def build_hub_response(
    *,
    ok: bool = True,
    data: Any = None,
    error: str | None = None,
    hint: str | None = None,
) -> str:
    """Construit une réponse JSON simulant le contrat Integration Hub."""

    return json.dumps(
        {
            "ok": ok,
            "data": data,
            "error": error,
            "hint": hint,
        }
    )


class FakeGetResourceProjects:
    """Fake Hub enregistrant les paramètres reçus."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self,
        *,
        resource_id: str,
        data_area_id: str | None,
        limit: int,
        skip: int,
        auth_header: str,
    ) -> str:
        self.calls.append(
            {
                "resource_id": resource_id,
                "data_area_id": data_area_id,
                "limit": limit,
                "skip": skip,
                "auth_header": auth_header,
            }
        )

        return self.response


class TestFindResourceProjects:
    """Tests principaux de find_resource_projects."""

    def test_returns_normalized_projects(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(
                data=[
                    {
                        "projId": "PRJ-001",
                        "name": "Projet Atlas",
                        "description": "Migration du système Atlas",
                        "status": "Active",
                    },
                    {
                        "projId": "PRJ-002",
                        "name": "Projet Orion",
                        "description": "Développement Orion",
                        "status": "Active",
                    },
                ]
            )
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.hub_error is None
        assert result.count == 2

        assert result.projects[0].project_id == "PRJ-001"
        assert result.projects[0].name == "Projet Atlas"
        assert result.projects[0].description == (
            "Migration du système Atlas"
        )
        assert result.projects[0].status == "Active"

        assert result.projects[1].project_id == "PRJ-002"
        assert result.projects[1].name == "Projet Orion"

    def test_returns_empty_result_when_no_project_exists(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(data=[])
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.count == 0
        assert result.projects == []
        assert result.hub_error is None

    def test_transmits_parameters_to_hub(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(data=[])
        )

        find_resource_projects(
            resource_id="  RESOURCE-456  ",
            auth_header="Bearer abc",
            data_area_id="LUNAI",
            limit=25,
            skip=50,
            get_projects_fn=fake,
        )

        assert fake.calls == [
            {
                "resource_id": "RESOURCE-456",
                "data_area_id": "LUNAI",
                "limit": 25,
                "skip": 50,
                "auth_header": "Bearer abc",
            }
        ]

    def test_sorts_projects_by_name_then_identifier(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(
                data=[
                    {
                        "projId": "PRJ-003",
                        "name": "Zulu",
                    },
                    {
                        "projId": "PRJ-002",
                        "name": "atlas",
                    },
                    {
                        "projId": "PRJ-001",
                        "name": "Atlas",
                    },
                ]
            )
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert [
            project.project_id
            for project in result.projects
        ] == [
            "PRJ-001",
            "PRJ-002",
            "PRJ-003",
        ]

    def test_preserves_raw_data_internally(self) -> None:
        raw_project = {
            "projId": "PRJ-001",
            "name": "Projet Atlas",
            "customField": "custom-value",
        }

        fake = FakeGetResourceProjects(
            build_hub_response(data=[raw_project])
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.projects[0].raw_data == raw_project

    def test_missing_resource_id_is_rejected(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(data=[])
        )

        with pytest.raises(
            ProjectFinderError,
            match="resource_id est obligatoire",
        ):
            find_resource_projects(
                resource_id="   ",
                auth_header="Bearer token",
                get_projects_fn=fake,
            )

        assert fake.calls == []

    def test_missing_auth_header_is_rejected(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(data=[])
        )

        with pytest.raises(
            ProjectFinderError,
            match="jeton d'authentification est obligatoire",
        ):
            find_resource_projects(
                resource_id="RESOURCE-123",
                auth_header="   ",
                get_projects_fn=fake,
            )

        assert fake.calls == []


class TestHubResponseFormats:
    """Tests des formats de réponse Hub supportés."""

    @pytest.mark.parametrize(
        "container_key",
        [
            "projects",
            "items",
            "results",
            "records",
            "data",
            "value",
        ],
    )
    def test_supports_nested_project_lists(
        self,
        container_key: str,
    ) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(
                data={
                    container_key: [
                        {
                            "projId": "PRJ-NESTED",
                            "name": "Projet imbriqué",
                        }
                    ]
                }
            )
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.count == 1
        assert result.projects[0].project_id == "PRJ-NESTED"
        assert result.projects[0].name == "Projet imbriqué"

    def test_supports_single_project_object(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(
                data={
                    "projectId": "PRJ-SINGLE",
                    "projectName": "Projet unique",
                    "projectDescription": "Description unique",
                    "projectStatus": "Active",
                }
            )
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.count == 1
        assert result.projects[0].project_id == "PRJ-SINGLE"
        assert result.projects[0].name == "Projet unique"
        assert result.projects[0].description == "Description unique"
        assert result.projects[0].status == "Active"

    @pytest.mark.parametrize(
        (
            "raw_project",
            "expected_id",
            "expected_name",
            "expected_description",
            "expected_status",
        ),
        [
            (
                {
                    "projId": "PRJ-1",
                    "name": "Atlas",
                    "description": "Projet Atlas",
                    "status": "Active",
                },
                "PRJ-1",
                "Atlas",
                "Projet Atlas",
                "Active",
            ),
            (
                {
                    "projectId": "PRJ-2",
                    "projectName": "Orion",
                    "projectDescription": "Projet Orion",
                    "projectStatus": "Open",
                },
                "PRJ-2",
                "Orion",
                "Projet Orion",
                "Open",
            ),
            (
                {
                    "project_id": "PRJ-3",
                    "project_name": "Nova",
                    "project_description": "Projet Nova",
                    "state": "Draft",
                },
                "PRJ-3",
                "Nova",
                "Projet Nova",
                "Draft",
            ),
            (
                {
                    "id": 1234,
                    "title": "Projet numérique",
                },
                "1234",
                "Projet numérique",
                None,
                None,
            ),
            (
                {
                    "number": "PRJ-5",
                    "description": "Projet par description",
                },
                "PRJ-5",
                "Projet par description",
                "Projet par description",
                None,
            ),
        ],
    )
    def test_normalizes_known_field_names(
        self,
        raw_project: dict[str, Any],
        expected_id: str,
        expected_name: str,
        expected_description: str | None,
        expected_status: str | None,
    ) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(data=[raw_project])
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.count == 1

        project = result.projects[0]

        assert project.project_id == expected_id
        assert project.name == expected_name
        assert project.description == expected_description
        assert project.status == expected_status


class TestProjectDeduplication:
    """Tests de suppression des doublons techniques."""

    def test_removes_projects_with_same_identifier(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(
                data=[
                    {
                        "projId": "PRJ-001",
                        "name": "Atlas",
                    },
                    {
                        "projId": "prj-001",
                        "name": "Atlas dupliqué",
                    },
                    {
                        "projId": "PRJ-002",
                        "name": "Orion",
                    },
                ]
            )
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.count == 2

        assert [
            project.project_id
            for project in result.projects
        ] == [
            "PRJ-001",
            "PRJ-002",
        ]

    def test_keeps_first_project_when_duplicate_exists(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(
                data=[
                    {
                        "projId": "PRJ-001",
                        "name": "Premier nom",
                    },
                    {
                        "projId": "PRJ-001",
                        "name": "Deuxième nom",
                    },
                ]
            )
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.count == 1
        assert result.projects[0].name == "Premier nom"


class TestInvalidProjectData:
    """Tests des projets invalides ou incomplets."""

    @pytest.mark.parametrize(
        "raw_project",
        [
            {
                "name": "Projet sans identifiant",
            },
            {
                "projId": "PRJ-NO-NAME",
            },
            {
                "projId": "",
                "name": "Projet identifiant vide",
            },
            {
                "projId": "PRJ-EMPTY-NAME",
                "name": "",
            },
            {
                "projId": "   ",
                "name": "Projet identifiant espaces",
            },
            {
                "projId": "PRJ-WHITESPACE-NAME",
                "name": "   ",
            },
        ],
    )
    def test_ignores_invalid_projects(
        self,
        raw_project: dict[str, Any],
    ) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(data=[raw_project])
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.count == 0

    def test_ignores_non_dictionary_items(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(
                data=[
                    None,
                    "invalid",
                    42,
                    True,
                    {
                        "projId": "PRJ-VALID",
                        "name": "Projet valide",
                    },
                ]
            )
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.count == 1
        assert result.projects[0].project_id == "PRJ-VALID"

    @pytest.mark.parametrize(
        "data",
        [
            None,
            "unexpected",
            123,
            True,
            {},
            {"projects": "not-a-list"},
        ],
    )
    def test_unknown_data_formats_return_empty_result(
        self,
        data: Any,
    ) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(data=data)
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.count == 0
        assert result.hub_error is None


class TestHubErrors:
    """Tests des erreurs fonctionnelles et techniques du Hub."""

    def test_returns_hub_error_without_raising(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(
                ok=False,
                error="Timeout Integration Hub",
                hint="Réessayer ultérieurement",
            )
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.count == 0
        assert result.hub_error == (
            "Timeout Integration Hub — Réessayer ultérieurement"
        )

    def test_uses_error_only_when_hint_is_missing(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(
                ok=False,
                error="Service indisponible",
            )
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.hub_error == "Service indisponible"

    def test_uses_hint_only_when_error_is_missing(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(
                ok=False,
                hint="Vérifier la ressource",
            )
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.hub_error == "Vérifier la ressource"

    def test_uses_default_error_message(self) -> None:
        fake = FakeGetResourceProjects(
            build_hub_response(
                ok=False,
            )
        )

        result = find_resource_projects(
            resource_id="RESOURCE-123",
            auth_header="Bearer token",
            get_projects_fn=fake,
        )

        assert result.hub_error == (
            "La recherche des projets de la ressource a échoué."
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
        fake = FakeGetResourceProjects(invalid_response)

        with pytest.raises(
            ProjectFinderError,
            match="n'est pas un JSON valide",
        ):
            find_resource_projects(
                resource_id="RESOURCE-123",
                auth_header="Bearer token",
                get_projects_fn=fake,
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
        fake = FakeGetResourceProjects(non_object_response)

        with pytest.raises(
            ProjectFinderError,
            match="doit être un objet JSON",
        ):
            find_resource_projects(
                resource_id="RESOURCE-123",
                auth_header="Bearer token",
                get_projects_fn=fake,
            )