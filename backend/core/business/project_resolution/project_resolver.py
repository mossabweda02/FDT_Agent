"""
Module: backend.core.business.project_resolution.project_resolver
=================================================================

Résolution déterministe d'une référence projet exprimée par l'utilisateur.

Ce composant :

1. récupère les projets associés à la ressource ;
2. normalise la référence utilisateur ;
3. recherche une correspondance exacte sur l'identifiant ;
4. recherche une correspondance exacte sur le nom ;
5. applique une correspondance textuelle prudente ;
6. retourne une décision métier exploitable par le workflow.

Aucun LLM n'est utilisé.

Le résolveur ne crée, ne modifie et ne supprime aucun projet.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from backend.core.business.project_resolution.models import (
    ProjectResolutionDecision,
    ProjectResolutionStatus,
    ProjectSummary,
)
from backend.core.business.project_resolution.project_finder import (
    GetResourceProjectsCallable,
    ListProjectsCallable,
    ProjectFinderError,
    find_global_projects,
    find_resource_projects,
)
from backend.tools.hub_functions import (
    hub_get_ressource_project,
    hub_list_projects,
)

_GENERIC_PROJECT_PREFIXES = (
    "projet",
    "project",
    "le projet",
    "la projet",
    "du projet",
    "de projet",
    "sur le projet",
    "pour le projet",
)

_GENERIC_REFERENCE_WORDS = {
    "projet",
    "project",
    "le",
    "la",
    "les",
    "du",
    "de",
    "des",
    "sur",
    "pour",
    "dans",
    "au",
    "aux",
}
    
def resolve_project_reference(
    *,
    requested_reference: str | None,
    resource_id: str,
    auth_header: str,
    data_area_id: str | None = None,
    limit: int = 50,
    skip: int = 0,
    global_limit: int = 100,
    get_projects_fn: GetResourceProjectsCallable = (
        hub_get_ressource_project
    ),
    list_projects_fn: ListProjectsCallable = hub_list_projects,
) -> ProjectResolutionDecision:
    """
    Résout une référence projet en utilisant les projets de la ressource.

    Ordre de résolution :

    1. validation de la référence utilisateur ;
    2. récupération des projets de la ressource ;
    3. correspondance exacte sur l'identifiant ;
    4. correspondance exacte sur le nom ;
    5. correspondance exacte après suppression du préfixe "projet" ;
    6. correspondance par tokens significatifs ;
    7. correspondance partielle prudente.

    Une sélection automatique n'est effectuée que lorsqu'une seule
    correspondance suffisamment fiable existe.
    """

    normalized_reference = _normalize_reference(requested_reference)

    try:
        lookup_result = find_resource_projects(
            resource_id=resource_id,
            auth_header=auth_header,
            data_area_id=data_area_id,
            limit=limit,
            skip=skip,
            get_projects_fn=get_projects_fn,
        )
    except ProjectFinderError as exc:
        return ProjectResolutionDecision(
            status=ProjectResolutionStatus.INVALID_RESPONSE,
            requested_reference=requested_reference,
            requires_user_input=False,
            can_continue=False,
            message=(
                "La liste des projets n'a pas pu être interprétée."
            ),
            hub_error=str(exc),
        )
    except Exception as exc:
        return ProjectResolutionDecision(
            status=ProjectResolutionStatus.HUB_ERROR,
            requested_reference=requested_reference,
            requires_user_input=False,
            can_continue=False,
            message=(
                "Le service des projets est temporairement indisponible."
            ),
            hub_error=str(exc),
        )

    if lookup_result.hub_error:
        return ProjectResolutionDecision(
            status=ProjectResolutionStatus.HUB_ERROR,
            requested_reference=requested_reference,
            requires_user_input=False,
            can_continue=False,
            message=(
                "Integration Hub n'a pas pu récupérer les projets "
                "de la ressource."
            ),
            hub_error=lookup_result.hub_error,
        )

    projects = lookup_result.projects
    available_projects = list(projects)

    if not normalized_reference:
        return ProjectResolutionDecision(
            status=ProjectResolutionStatus.MISSING_REFERENCE,
            requested_reference=requested_reference,
            candidate_projects=available_projects,
            available_projects=available_projects,
            requires_user_input=True,
            can_continue=False,
            message=(
                "Je n'ai pas pu identifier le projet à utiliser. "
                "Veuillez choisir un projet parmi ceux qui vous sont associés."
            ),
        )

    if not projects:
        return ProjectResolutionDecision(
            status=ProjectResolutionStatus.NOT_FOUND,
            requested_reference=requested_reference,
            requires_user_input=True,
            can_continue=False,
            message=(
                "Aucun projet n'est associé à cette ressource."
            ),
        )

    exact_id_matches = _find_exact_identifier_matches(
        normalized_reference,
        projects,
    )

    if exact_id_matches:
        return _build_match_decision(
            requested_reference=requested_reference,
            matches=exact_id_matches,
            exact_match=True,
        )

    exact_name_matches = _find_exact_name_matches(
        normalized_reference,
        projects,
    )

    if exact_name_matches:
        return _build_match_decision(
            requested_reference=requested_reference,
            matches=exact_name_matches,
            exact_match=True,
        )

    simplified_reference = _remove_generic_project_prefix(
        normalized_reference
    )

    if simplified_reference != normalized_reference:
        simplified_name_matches = _find_exact_name_matches(
            simplified_reference,
            projects,
        )

        if simplified_name_matches:
            return _build_match_decision(
                requested_reference=requested_reference,
                matches=simplified_name_matches,
                exact_match=True,
            )

    token_matches = _find_token_matches(
        simplified_reference,
        projects,
    )

    if token_matches:
        return _build_match_decision(
            requested_reference=requested_reference,
            matches=token_matches,
            exact_match=False,
        )

    partial_matches = _find_partial_matches(
    simplified_reference,
        projects,
    )

    if partial_matches:
        return _build_match_decision(
            requested_reference=requested_reference,
            matches=partial_matches,
            exact_match=False,
        )

    # ============================================================
    # RECHERCHE GLOBALE
    # Aucun projet associé n'a été trouvé.
    # On cherche maintenant dans tous les projets Operate.
    # ============================================================

    try:
        global_lookup_result = find_global_projects(
            auth_header=auth_header,
            limit=global_limit,
            list_projects_fn=list_projects_fn,
        )
    except ProjectFinderError:
        global_lookup_result = None
    except Exception:
        global_lookup_result = None

    if (
        global_lookup_result is not None
        and not global_lookup_result.hub_error
    ):
        global_projects = global_lookup_result.projects

        global_exact_id_matches = _find_exact_identifier_matches(
            normalized_reference,
            global_projects,
        )

        if global_exact_id_matches:
            return _build_not_associated_decision(
                requested_reference=requested_reference,
                matches=global_exact_id_matches,
                available_projects=available_projects,
            )

        global_exact_name_matches = _find_exact_name_matches(
            normalized_reference,
            global_projects,
        )

        if global_exact_name_matches:
            return _build_not_associated_decision(
                requested_reference=requested_reference,
                matches=global_exact_name_matches,
                available_projects=available_projects,
            )

        if simplified_reference != normalized_reference:
            global_simplified_name_matches = _find_exact_name_matches(
                simplified_reference,
                global_projects,
            )

            if global_simplified_name_matches:
                return _build_not_associated_decision(
                    requested_reference=requested_reference,
                    matches=global_simplified_name_matches,
                    available_projects=available_projects,
                )

        global_token_matches = _find_token_matches(
            simplified_reference,
            global_projects,
        )

        if global_token_matches:
            return _build_not_associated_decision(
                requested_reference=requested_reference,
                matches=global_token_matches,
                available_projects=available_projects,
            )

        global_partial_matches = _find_partial_matches(
            simplified_reference,
            global_projects,
        )

        if global_partial_matches:
            return _build_not_associated_decision(
                requested_reference=requested_reference,
                matches=global_partial_matches,
                available_projects=available_projects,
            )

    # ============================================================
    # NOT_FOUND FINAL
    # Le projet n'est ni associé, ni trouvé dans les projets globaux.
    # ============================================================

    return ProjectResolutionDecision(
        status=ProjectResolutionStatus.NOT_FOUND,
        requested_reference=requested_reference,
        candidate_projects=available_projects,
        available_projects=available_projects,
        requires_user_input=True,
        can_continue=False,
        message=(
            f"Je n'ai pas trouvé le projet "
            f"« {requested_reference.strip()} ». "
            "Veuillez choisir un projet parmi ceux qui vous sont associés."
        ),
    )


def _build_match_decision(
    *,
    requested_reference: str | None,
    matches: list[ProjectSummary],
    exact_match: bool,
) -> ProjectResolutionDecision:
    """Construit une décision à partir des projets correspondants."""

    if len(matches) == 1:
        selected_project = matches[0]

        return ProjectResolutionDecision(
            status=ProjectResolutionStatus.MATCHED,
            requested_reference=requested_reference,
            selected_project=selected_project,
            candidate_projects=[selected_project],
            requires_user_input=False,
            can_continue=True,
            message=(
                f"Le projet {selected_project.name} "
                f"({selected_project.project_id}) a été sélectionné."
            ),
        )

    match_type = (
        "exactement"
        if exact_match
        else "partiellement"
    )

    return ProjectResolutionDecision(
        status=ProjectResolutionStatus.MULTIPLE_MATCHES,
        requested_reference=requested_reference,
        candidate_projects=matches,
        requires_user_input=True,
        can_continue=False,
        message=(
            f"{len(matches)} projets correspondent {match_type} "
            "à la référence fournie. "
            "Veuillez préciser le projet à utiliser."
        ),
    )

def _build_not_associated_decision(
    *,
    requested_reference: str | None,
    matches: list[ProjectSummary],
    available_projects: list[ProjectSummary],
) -> ProjectResolutionDecision:
    """
    Construit une décision indiquant que le projet existe globalement,
    mais n'est pas associé à la ressource actuelle.
    """

    if len(matches) == 1:
        matched_project = matches[0]

        return ProjectResolutionDecision(
            status=ProjectResolutionStatus.NOT_ASSOCIATED,
            requested_reference=requested_reference,
            candidate_projects=[matched_project],
            available_projects=available_projects,
            requires_user_input=True,
            can_continue=False,
            message=(
                f"Le projet « {matched_project.name} » "
                f"({matched_project.project_id}) existe, "
                "mais il n'est pas associé à votre ressource. "
                "Veuillez choisir un projet parmi ceux qui vous sont "
                "accessibles."
            ),
        )

    return ProjectResolutionDecision(
        status=ProjectResolutionStatus.NOT_ASSOCIATED,
        requested_reference=requested_reference,
        candidate_projects=matches,
        available_projects=available_projects,
        requires_user_input=True,
        can_continue=False,
        message=(
            f"Plusieurs projets correspondant à "
            f"« {requested_reference.strip() if requested_reference else ''} » "
            "existent, mais aucun n'est associé à votre ressource. "
            "Veuillez choisir un projet parmi ceux qui vous sont accessibles."
        ),
    )

def _find_exact_identifier_matches(
    normalized_reference: str,
    projects: Iterable[ProjectSummary],
) -> list[ProjectSummary]:
    """Recherche une correspondance exacte sur l'identifiant projet."""

    return [
        project
        for project in projects
        if _normalize_reference(project.project_id)
        == normalized_reference
    ]


def _find_exact_name_matches(
    normalized_reference: str,
    projects: Iterable[ProjectSummary],
) -> list[ProjectSummary]:
    """Recherche une correspondance exacte sur le nom projet."""

    matches: list[ProjectSummary] = []

    for project in projects:
        normalized_name = _normalize_reference(project.name)

        if normalized_name == normalized_reference:
            matches.append(project)
            continue

        simplified_name = _remove_generic_project_prefix(
            normalized_name
        )

        if simplified_name == normalized_reference:
            matches.append(project)

    return _deduplicate_projects(matches)


def _find_token_matches(
    normalized_reference: str,
    projects: Iterable[ProjectSummary],
) -> list[ProjectSummary]:
    """
    Recherche les projets contenant tous les tokens significatifs.

    Exemple :

        "migration atlas"

    peut correspondre à :

        "Projet de migration Atlas"

    La correspondance n'est retenue que si tous les mots significatifs
    de la référence sont présents dans le nom ou la description.
    """

    reference_tokens = _significant_tokens(normalized_reference)

    if not reference_tokens:
        return []

    matches: list[ProjectSummary] = []

    for project in projects:
        searchable_text = " ".join(
            value
            for value in (
                project.name,
                project.description,
                project.project_id,
            )
            if value
        )

        project_tokens = _significant_tokens(
            _normalize_reference(searchable_text)
        )

        if reference_tokens.issubset(project_tokens):
            matches.append(project)

    return _deduplicate_projects(matches)


def _find_partial_matches(
    normalized_reference: str,
    projects: Iterable[ProjectSummary],
) -> list[ProjectSummary]:
    """
    Recherche une correspondance partielle prudente.

    La référence doit contenir au moins trois caractères significatifs.
    La correspondance est faite sur le nom simplifié ou l'identifiant.

    Cette stratégie est exécutée en dernier pour éviter les sélections
    trop permissives.
    """

    compact_reference = normalized_reference.strip()

    if len(compact_reference) < 3:
        return []

    matches: list[ProjectSummary] = []

    for project in projects:
        normalized_id = _normalize_reference(project.project_id)
        normalized_name = _normalize_reference(project.name)
        simplified_name = _remove_generic_project_prefix(
            normalized_name
        )

        if compact_reference in normalized_id:
            matches.append(project)
            continue

        if compact_reference in normalized_name:
            matches.append(project)
            continue

        if compact_reference in simplified_name:
            matches.append(project)
            continue

        if normalized_name in compact_reference:
            matches.append(project)
            continue

        if (
            simplified_name
            and simplified_name in compact_reference
        ):
            matches.append(project)

    return _deduplicate_projects(matches)


def _normalize_reference(value: str | None) -> str:
    """
    Normalise une référence pour permettre une comparaison déterministe.

    Transformations :

    - suppression des accents ;
    - conversion en minuscules ;
    - remplacement de la ponctuation par des espaces ;
    - réduction des espaces multiples.
    """

    if value is None:
        return ""

    stripped_value = value.strip()

    if not stripped_value:
        return ""

    decomposed = unicodedata.normalize(
        "NFKD",
        stripped_value,
    )

    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )

    lowercase_value = without_accents.casefold()

    without_punctuation = re.sub(
        r"[^a-z0-9]+",
        " ",
        lowercase_value,
    )

    return " ".join(without_punctuation.split())


def _remove_generic_project_prefix(value: str) -> str:
    """
    Supprime les expressions génériques placées avant un nom de projet.

    Exemple :

        "le projet atlas" devient "atlas".
    """

    normalized_value = value.strip()

    for prefix in sorted(
        _GENERIC_PROJECT_PREFIXES,
        key=len,
        reverse=True,
    ):
        normalized_prefix = _normalize_reference(prefix)

        if normalized_value == normalized_prefix:
            return ""

        prefix_with_space = f"{normalized_prefix} "

        if normalized_value.startswith(prefix_with_space):
            return normalized_value[
                len(prefix_with_space):
            ].strip()

    return normalized_value


def _significant_tokens(value: str) -> set[str]:
    """Retourne les mots significatifs d'une référence normalisée."""

    return {
        token
        for token in value.split()
        if token not in _GENERIC_REFERENCE_WORDS
        and len(token) >= 2
    }


def _deduplicate_projects(
    projects: Iterable[ProjectSummary],
) -> list[ProjectSummary]:
    """Supprime les doublons selon l'identifiant du projet."""

    unique_projects: dict[str, ProjectSummary] = {}

    for project in projects:
        key = project.project_id.casefold()

        if key not in unique_projects:
            unique_projects[key] = project

    return sorted(
        unique_projects.values(),
        key=lambda project: (
            project.name.casefold(),
            project.project_id.casefold(),
        ),
    )