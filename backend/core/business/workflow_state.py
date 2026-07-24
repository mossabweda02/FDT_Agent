"""
Module: backend.core.business.workflow_state
======================================
Ce fichier contient la logique de gestion de l'état du workflow métier pour les interactions avec l'agent.
Il définit :
- WorkflowStatus : un enum représentant les différents états du workflow.
- WorkflowState : une classe représentant l'état complet d'une conversation, incluant le statut,les données métier, les questions en attente, et les informations d'erreur.
- ALLOWED_TRANSITIONS : un dictionnaire définissant les transitions autorisées entre les statuts.
- Fonctions utilitaires pour obtenir, sauvegarder et effacer l'état du workflow.

"""


from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class WorkflowStatus(StrEnum):
    IDLE = "IDLE"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    WAITING_CLARIFICATION = "WAITING_CLARIFICATION"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


MAX_RETRY_COUNT = 2

# Seule source de vérité du cycle de vie — toute transition hors de cette
# table est refusée. C'est ce qui empêche une double confirmation d'exécuter
# deux fois la même action.
ALLOWED_TRANSITIONS: dict[WorkflowStatus, set[WorkflowStatus]] = {
    WorkflowStatus.IDLE: {WorkflowStatus.WAITING_CONFIRMATION, WorkflowStatus.WAITING_CLARIFICATION},
    WorkflowStatus.WAITING_CLARIFICATION: {WorkflowStatus.WAITING_CONFIRMATION, WorkflowStatus.CANCELLED},
    WorkflowStatus.WAITING_CONFIRMATION: {
        WorkflowStatus.EXECUTING, WorkflowStatus.CANCELLED, WorkflowStatus.WAITING_CLARIFICATION,
    },
    WorkflowStatus.EXECUTING: {WorkflowStatus.COMPLETED, WorkflowStatus.FAILED},
    WorkflowStatus.FAILED: {WorkflowStatus.EXECUTING, WorkflowStatus.CANCELLED},
    WorkflowStatus.COMPLETED: set(),
    WorkflowStatus.CANCELLED: set(),
}


class InvalidTransitionError(Exception):
    """Levée quand une transition de statut viole ALLOWED_TRANSITIONS."""


@dataclass
class WorkflowState:
    conversation_id: str
    status: WorkflowStatus = WorkflowStatus.IDLE

    # Données métier — jamais perdues entre préparation et confirmation.
    intent: str | None = None
    scenario: str | None = None
    business_request: dict[str, Any] | None = None
    execution_plan: dict[str, Any] | None = None
    missing_fields: list[str] = field(default_factory=list)

    # Préparation de la Clarification Active (pas de questionnaire actif encore).
    pending_questions: list[dict[str, Any]] = field(default_factory=list)
    collected_answers: dict[str, Any] = field(default_factory=dict)

    # Gestion des erreurs / retry.
    error: str | None = None
    error_recoverable: bool = False
    retry_count: int = 0

    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def transition_to(self, new_status: WorkflowStatus) -> None:
        """Applique une transition si elle est autorisée, sinon lève InvalidTransitionError.
        C'est le point unique de protection contre les doubles exécutions."""
        allowed = ALLOWED_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"Transition invalide: {self.status} -> {new_status} "
                f"(conversation_id={self.conversation_id})"
            )
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc).isoformat()


_WORKFLOW_STORE: dict[str, WorkflowState] = {}


def get_workflow_state(conversation_id: str | None) -> WorkflowState | None:
    if not conversation_id:
        return None
    return _WORKFLOW_STORE.get(conversation_id)


def save_workflow_state(state: WorkflowState) -> None:
    _WORKFLOW_STORE[state.conversation_id] = state


def clear_workflow_state(conversation_id: str | None) -> None:
    if conversation_id:
        _WORKFLOW_STORE.pop(conversation_id, None)


def has_pending_confirmation(conversation_id: str | None) -> bool:
    state = get_workflow_state(conversation_id)
    return bool(state and state.status == WorkflowStatus.WAITING_CONFIRMATION)