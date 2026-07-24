"""
Module: backend.core.business.timesheet_resolution.models
=========================================================

Contrats de résolution des périodes de feuilles de temps.

Ce fichier définit les objets Pydantic utilisés pour représenter
une période calendaire résolue, ses jours ouvrables et les éventuelles
clarifications nécessaires avant la recherche d'une feuille de temps.

Le résolveur calcule les dates.
Le workflow décide ensuite de rechercher, clarifier ou créer.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class TimesheetPeriodGranularity(StrEnum):
    """Niveau de précision de la période demandée."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    CUSTOM = "custom"


class ResolvedTimesheetPeriod(BaseModel):
    """Période de feuille de temps résolue par le backend."""

    period_mode: str = Field(
        description="Mode temporel provenant du BusinessRequest.",
    )
    start_date: date = Field(
        description="Premier jour de la période recherchée.",
    )
    end_date: date = Field(
        description="Dernier jour de la période recherchée.",
    )
    working_dates: list[date] = Field(
        default_factory=list,
        description="Jours ouvrables compris dans la période, du lundi au vendredi.",
    )
    granularity: TimesheetPeriodGranularity = Field(
        description="Précision de la période résolue.",
    )
    explicit_date: date | None = Field(
        default=None,
        description="Date précise mentionnée par l'utilisateur.",
    )
    expects_multiple: bool = Field(
        default=False,
        description="Indique si plusieurs feuilles peuvent être attendues.",
    )
    requires_clarification: bool = Field(
        default=False,
        description="Indique qu'une confirmation de l'interprétation est nécessaire.",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Question courte à poser à l'utilisateur.",
    )
    source_expression: str | None = Field(
        default=None,
        description="Expression temporelle d'origine, si disponible.",
    )

class TimesheetSummary(BaseModel):
    """Référence normalisée vers une feuille de temps trouvée dans le Hub."""

    number: str = Field(
        description="Numéro technique de la feuille de temps.",
    )
    start_date: date = Field(
        description="Premier jour couvert par la feuille.",
    )
    end_date: date = Field(
        description="Dernier jour couvert par la feuille.",
    )
    status: str | None = Field(
        default=None,
        description="Statut métier de la feuille si fourni par le Hub.",
    )
    raw_data: dict[str, Any] = Field(
        default_factory=dict,
        exclude=True,
        description="Réponse Hub d'origine conservée pour diagnostic interne.",
    )


class TimesheetLookupResult(BaseModel):
    """Résultat d'une recherche de feuilles sur une période."""

    requested_start_date: date
    requested_end_date: date
    matched_timesheets: list[TimesheetSummary] = Field(default_factory=list)
    hub_error: str | None = None

    @property
    def count(self) -> int:
        """Retourne le nombre de feuilles trouvées."""

        return len(self.matched_timesheets)

    @property
    def found(self) -> bool:
        """Indique si au moins une feuille correspond à la période."""

        return bool(self.matched_timesheets)

    @property
    def selected_timesheet(self) -> TimesheetSummary | None:
        """Retourne automatiquement la feuille si une seule correspondance existe."""

        if len(self.matched_timesheets) == 1:
            return self.matched_timesheets[0]
        return None