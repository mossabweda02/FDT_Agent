"""
Module: backend.core.business.project_resolution.project_finder
===============================================================

Récupération et normalisation des projets associés à une ressource.

Ce composant :

1. appelle Integration Hub ;
2. valide la réponse JSON standardisée ;
3. extrait les projets depuis plusieurs structures possibles ;
4. normalise les champs d'identifiant, de nom, de statut et de description.

Il ne choisit aucun projet et ne réalise aucune correspondance textuelle.
Cette décision appartient à project_resolver.py.
"""

from __future__ import annotations

import json
from typing import Any, Callable
from collections.abc import Callable


from backend.core.business.project_resolution.models import (
    ProjectLookupResult,
    ProjectSummary,
)
from backend.tools.hub_functions import hub_get_ressource_project, hub_list_projects


class ProjectFinderError(ValueError):
    """Erreur de structure ou de normalisation de la réponse projet."""


GetResourceProjectsCallable = Callable[..., str]
ListProjectsCallable = Callable[..., str]

def find_resource_projects(
    *,
    resource_id: str,
    auth_header: str,
    limit: int = 50,
    skip: int = 0,
    data_area_id: str | None = None,
    get_projects_fn: GetResourceProjectsCallable = hub_get_ressource_project,
) -> ProjectLookupResult:
    """
    Récupère les projets associés à une ressource.

    Les erreurs fonctionnelles Hub sont retournées dans ProjectLookupResult.
    Les réponses non JSON ou structurellement invalides lèvent
    ProjectFinderError.
    """

    if not resource_id or not resource_id.strip():
        raise ProjectFinderError(
            "Le resource_id est obligatoire pour rechercher les projets."
        )

    if not auth_header or not auth_header.strip():
        raise ProjectFinderError(
            "Le jeton d'authentification est obligatoire pour rechercher "
            "les projets."
        )

    raw_response = get_projects_fn(
        resource_id=resource_id.strip(),
        data_area_id=data_area_id,
        limit=limit,
        skip=skip,
        auth_header=auth_header,
    )

    payload = _parse_json_response(raw_response)

    if not payload.get("ok"):
        return ProjectLookupResult(
            hub_error=_extract_hub_error(payload),
        )

    raw_projects = _extract_project_items(payload.get("data"))

    normalized_projects: list[ProjectSummary] = []

    for raw_project in raw_projects:
        project = _normalize_project(raw_project)

        if project is not None:
            normalized_projects.append(project)

    normalized_projects = _deduplicate_projects(normalized_projects)

    normalized_projects.sort(
        key=lambda project: (
            project.name.casefold(),
            project.project_id.casefold(),
        )
    )

    return ProjectLookupResult(projects=normalized_projects)

def find_global_projects(
    *,
    auth_header: str,
    limit: int = 100,
    list_projects_fn: ListProjectsCallable = hub_list_projects,
) -> ProjectLookupResult:
    """
    Récupère et normalise la liste globale des projets Operate.

    Cette fonction est utilisée après l'échec de la recherche dans les
    projets associés à la ressource. Elle permet de déterminer si un projet
    existe globalement, mais n'est pas associé à l'utilisateur.

    La fonction ne réalise aucune recherche textuelle. Elle se limite à :

    1. appeler Integration Hub ;
    2. parser la réponse JSON ;
    3. détecter les erreurs fonctionnelles ;
    4. extraire les projets ;
    5. normaliser les projets ;
    6. supprimer les doublons ;
    7. retourner un ProjectLookupResult.

    Args:
        auth_header:
            En-tête d'authentification transmis à Integration Hub.

        limit:
            Nombre maximal de projets demandés.

        list_projects_fn:
            Fonction Hub utilisée pour récupérer les projets.
            Ce paramètre permet d'injecter une fausse fonction dans les tests.

    Returns:
        ProjectLookupResult:
            Résultat contenant les projets globaux normalisés ou une erreur Hub.

    Raises:
        ProjectFinderError:
            Lorsque la réponse Hub n'est pas un JSON valide ou ne peut pas
            être interprétée.
    """

    if not auth_header or not auth_header.strip():
        return ProjectLookupResult(
            projects=[],
            hub_error="L'en-tête d'authentification est manquant.",
        )

    if limit <= 0:
        return ProjectLookupResult(
            projects=[],
            hub_error="La limite de projets doit être supérieure à zéro.",
        )
    
    try:
        raw_response = list_projects_fn(
            limit=limit,
            auth_header=auth_header,
        )
    except Exception as exc:
        return ProjectLookupResult(
            projects=[],
            hub_error=(
                "Erreur lors de la récupération de la liste globale "
                f"des projets : {exc}"
            ),
        )

    payload = _parse_json_response(raw_response)

    if not payload.get("ok") :
        return ProjectLookupResult(
            projects=[],
            hub_error=_extract_hub_error(payload),
        )

    raw_projects = _extract_project_items(payload.get("data"))
    
    normalized_projects: list[ProjectSummary] = []

    for raw_project in raw_projects:
        project = _normalize_project(raw_project)

        if project is not None:
            normalized_projects.append(project)

    projects_by_id: dict[str, ProjectSummary] = {}

    for project in normalized_projects:
        normalized_id = project.project_id.strip().casefold()

        if not normalized_id:
            continue

        if normalized_id not in projects_by_id:
            projects_by_id[normalized_id] = project

    sorted_projects = sorted(
        projects_by_id.values(),
        key=lambda project: (
            project.name.casefold(),
            project.project_id.casefold(),
        ),
    )

    return ProjectLookupResult(
        projects=sorted_projects,
        hub_error=None,
    )

def _parse_json_response(raw_response: str) -> dict[str, Any]:
    """Convertit la réponse JSON Hub en dictionnaire."""

    try:
        payload = json.loads(raw_response)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ProjectFinderError(
            "La réponse des projets de la ressource n'est pas un JSON valide."
        ) from exc

    if not isinstance(payload, dict):
        raise ProjectFinderError(
            "La réponse des projets de la ressource doit être un objet JSON."
        )

    return payload


def _extract_hub_error(payload: dict[str, Any]) -> str:
    """Construit un message contrôlé depuis une réponse Hub en erreur."""

    error = payload.get("error")
    hint = payload.get("hint")

    if error and hint:
        return f"{error} — {hint}"

    return str(
        error
        or hint
        or "La recherche des projets de la ressource a échoué."
    )


def _extract_project_items(data: Any) -> list[dict[str, Any]]:
    """Extrait les projets depuis les structures Hub connues."""

    if data is None:
        return []

    if isinstance(data, list):
        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    if not isinstance(data, dict):
        return []

    candidate_keys = (
        "projects",
        "items",
        "results",
        "records",
        "data",
        "value",
    )

    for key in candidate_keys:
        candidate = data.get(key)

        if isinstance(candidate, list):
            return [
                item
                for item in candidate
                if isinstance(item, dict)
            ]

    if _looks_like_project(data):
        return [data]

    return []


def _normalize_project(
    raw_project: dict[str, Any],
) -> ProjectSummary | None:
    """Normalise un projet retourné par Integration Hub."""

    project_id = _first_non_empty(
        raw_project,
        (
            "projId",
            "projectId",
            "project_id",
            "id",
            "number",
        ),
    )

    name = _first_non_empty(
        raw_project,
        (
            "name",
            "projectName",
            "project_name",
            "description",
            "title",
        ),
    )

    if project_id is None or name is None:
        return None

    normalized_project_id = str(project_id).strip()
    normalized_name = str(name).strip()

    if not normalized_project_id or not normalized_name:
        return None

    description = _first_non_empty(
        raw_project,
        (
            "description",
            "projectDescription",
            "project_description",
        ),
    )

    status = _first_non_empty(
        raw_project,
        (
            "status",
            "projectStatus",
            "state",
        ),
    )

    return ProjectSummary(
        project_id=normalized_project_id,
        name=normalized_name,
        description=(
            str(description).strip()
            if description not in (None, "")
            else None
        ),
        status=(
            str(status).strip()
            if status not in (None, "")
            else None
        ),
        raw_data=raw_project,
    )


def _first_non_empty(
    data: dict[str, Any],
    keys: tuple[str, ...],
) -> Any:
    """Retourne la première valeur non vide trouvée."""

    for key in keys:
        value = data.get(key)

        if value not in (None, ""):
            return value

    return None


def _looks_like_project(data: dict[str, Any]) -> bool:
    """Indique si un objet unique ressemble à un projet."""

    identifier_keys = {
        "projId",
        "projectId",
        "project_id",
        "id",
    }

    return any(key in data for key in identifier_keys)


def _deduplicate_projects(
    projects: list[ProjectSummary],
) -> list[ProjectSummary]:
    """Supprime les doublons techniques selon l'identifiant projet."""

    unique_projects: dict[str, ProjectSummary] = {}

    for project in projects:
        key = project.project_id.casefold()

        if key not in unique_projects:
            unique_projects[key] = project

    return list(unique_projects.values())