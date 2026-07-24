"""
Module: backend.core.business.project_resolution.models
========================================================

Contrats déterministes utilisés pour rechercher et résoudre un projet.

Ces modèles représentent :

- un projet normalisé provenant d'Integration Hub ;
- le résultat brut d'une recherche ;
- la décision finale de résolution.

Aucun appel réseau ni raisonnement LLM n'est effectué ici.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ProjectResolutionStatus(StrEnum):
    """Résultats possibles de la résolution d'un projet."""

    MATCHED = "MATCHED"
    NOT_ASSOCIATED = "NOT_ASSOCIATED"
    NOT_FOUND = "NOT_FOUND"
    MULTIPLE_MATCHES = "MULTIPLE_MATCHES"
    MISSING_REFERENCE = "MISSING_REFERENCE"
    HUB_ERROR = "HUB_ERROR"
    INVALID_RESPONSE = "INVALID_RESPONSE"


class ProjectSummary(BaseModel):
    """Représentation normalisée d'un projet."""

    project_id: str
    name: str
    description: str | None = None
    status: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)


class ProjectLookupResult(BaseModel):
    projects: list[ProjectSummary] = Field(default_factory=list)
    hub_error: str | None = None

    @property
    def count(self) -> int:
        return len(self.projects)


class ProjectResolutionDecision(BaseModel):
    """Décision produite après la résolution d'une référence projet."""

    status: ProjectResolutionStatus

    requested_reference: str | None = None

    selected_project: ProjectSummary | None = None

    candidate_projects: list[ProjectSummary] = Field(
        default_factory=list,
    )

    available_projects: list[ProjectSummary] = Field(
        default_factory=list,
    )

    requires_user_input: bool = False

    can_continue: bool = False

    message: str = ""

    hub_error: str | None = None