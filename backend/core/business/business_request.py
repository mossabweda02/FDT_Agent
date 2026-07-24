"""
Module: backend.business.business_request
======================================
Contrat métier structuré pour FDT Agent.

Ce fichier définit les objets Pydantic utilisés pour représenter
une demande utilisateur sous forme exploitable par le backend.

Le LLM interprète le langage naturel.
Le backend contrôle, valide, planifie et exécute.
"""


from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


BusinessIntent = Literal[
    "CREATE_TIMESHEET",
    "ADD_TIME_ENTRY",
    "ADD_MULTIPLE_TIME_ENTRIES",
    "UPDATE_TIME_ENTRY",
    "DELETE_TIME_ENTRY",
    "CONSULT_TIMESHEET",
    "CONFIRM_ACTION",
    "CANCEL_ACTION",
    "UNKNOWN",
]

BusinessScenarioName = Literal[
    "CREATE_EMPTY_TIMESHEET",
    "SINGLE_TIME_ENTRY",
    "REPEAT_ENTRY_OVER_DATE_RANGE",
    "MULTI_PROJECT_SAME_DAY",
    "MULTI_TASK_SAME_PROJECT",
    "UNKNOWN_SCENARIO",
]

TimesheetPeriodMode = Literal[
    "today",
    "yesterday",
    "tomorrow",
    "current_week",
    "last_week",
    "next_week",
    "current_month",
    "last_month",
    "next_month",
    "explicit_date",
    "explicit_range",
    "timesheet_number",
    "unknown",
]

RepeatType = Literal[   
    "none",
    "weekday_range",
    "daily_range",
    "same_entry_multiple_days",
    "unknown",
]


class TimesheetReference(BaseModel):
    """Référence temporelle ou directe à une feuille de temps."""

    number: str | None = Field(
        default=None,
        description="Numéro de feuille de temps si fourni, ex: TS-0000319.",
    )
    period_mode: TimesheetPeriodMode = Field(
        default="unknown",
        description="Type de période demandée par l'utilisateur.",
    )
    explicit_date: str | None = Field(
        default=None,
        description="Date explicite ISO yyyy-mm-dd si fournie ou interprétable.",
    )
    explicit_start_date: str | None = Field(
        default=None,
        description="Début explicite de période ISO yyyy-mm-dd si fourni.",
    )
    explicit_end_date: str | None = Field(
        default=None,
        description="Fin explicite de période ISO yyyy-mm-dd si fourni.",
    )


class TimeEntryRequest(BaseModel):
    """Une ligne ou saisie de temps demandée par l'utilisateur."""

    project: str | None = Field(
        default=None,
        description="Projet fourni par l'utilisateur : ID ou nom.",
    )
    task: str | None = Field(
        default=None,
        description="Tâche fournie par l'utilisateur : ID ou nom.",
    )
    category: str | None = Field(
        default=None,
        description="Catégorie timesheet si fournie.",
    )
    deliverable: str | None = Field(
        default=None,
        description="Livrable si fourni.",
    )
    hours: float | None = Field(
        default=None,
        description="Nombre d'heures demandé.",
    )
    date: str | None = Field(
        default=None,
        description="Date cible ISO yyyy-mm-dd si une journée spécifique est demandée.",
    )
    repeat_type: RepeatType = Field(
        default="none",
        description="Type de répétition demandé.",
    )
    dates_must_be_resolved_from_timesheet: bool = Field(
    default=False,
    description=(
        "True si les dates exactes ne doivent pas être déduites du contexte courant "
        "mais calculées après récupération de la période réelle de la feuille TS."
        ),
    )

class ActionContext(BaseModel):
    """Contexte de l'action métier demandée."""

    intent: BusinessIntent = Field(
        default="UNKNOWN",
        description="Intention métier principale.",
    )
    scenario: BusinessScenarioName = Field(
        default="UNKNOWN_SCENARIO",
        description="Scénario métier principal.",
    )
    requires_confirmation: bool = Field(
        default=True,
        description="True pour toute action d'écriture.",
    )
    user_confirmation_detected: bool = Field(
        default=False,
        description="True si le message utilisateur est une confirmation.",
    )


class BusinessRequest(BaseModel):
    """Demande métier structurée extraite du langage naturel."""

    action: ActionContext = Field(default_factory=ActionContext)
    timesheet: TimesheetReference = Field(default_factory=TimesheetReference)
    entries: list[TimeEntryRequest] = Field(default_factory=list)
    missing_information: list[str] = Field(
        default_factory=list,
        description="Informations nécessaires mais absentes.",
    )
    ambiguity_notes: list[str] = Field(
        default_factory=list,
        description="Ambiguïtés détectées à clarifier.",
    )