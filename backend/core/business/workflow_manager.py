"""
Module: backend.core.business.workflow_manager
======================================
Point d'entrée unique pour tout ce qui doit être décidé côté backend AVANT
de laisser un message partir vers le LLM : confirmation, annulation, retry,
validation du state, protection contre la double confirmation, politique de
nettoyage. `api_server.py` ne fait que déléguer ici.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.core.business.business_types import BusinessScenario
from backend.core.business.confirmation import is_cancellation, is_confirmation, is_retry
from backend.core.business.executors import execute_confirmed_scenario
from backend.core.business.workflow_state import (
    MAX_RETRY_COUNT,
    WorkflowState,
    WorkflowStatus,
    clear_workflow_state,
    get_workflow_state,
    save_workflow_state,
)

logger = logging.getLogger(__name__)

NO_ACTION_PENDING_MESSAGE = "Je n’ai aucune action en attente de confirmation."
NO_CANCELLATION_PENDING_MESSAGE = "Je n’ai aucune action en attente à annuler."
TOO_MANY_RETRIES_MESSAGE = "Trop de tentatives infructueuses. Merci de reformuler votre demande."
STATE_INCOMPLETE_MESSAGE = "Il me manque des informations pour exécuter cette action en toute sécurité. Merci de reformuler votre demande."
NOT_RETRYABLE_MESSAGE = "Cette action ne peut pas être relancée automatiquement. Merci de reformuler votre demande."
ALREADY_IN_PROGRESS_MESSAGE = "Cette action est déjà en cours de traitement."

_REQUIRED_FIELDS_BY_SCENARIO: dict[str, list[str]] = {
    str(BusinessScenario.CREATE_EMPTY_TIMESHEET): [],
    str(BusinessScenario.SINGLE_TIME_ENTRY): ["entries", "timesheet.number"],
    str(BusinessScenario.REPEAT_ENTRY_OVER_DATE_RANGE): ["entries", "timesheet.number"],
    str(BusinessScenario.MULTI_PROJECT_SAME_DAY): ["entries", "timesheet.number"],
    str(BusinessScenario.MULTI_TASK_SAME_PROJECT): ["entries", "timesheet.number"],
}


def _get_nested(data: dict, dotted_path: str) -> Any:
    node: Any = data
    for part in dotted_path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def validate_state_before_execution(state: WorkflowState) -> tuple[bool, list[str]]:
    """Vérifie que le state contient tout le nécessaire avant d'appeler le Hub."""
    missing: list[str] = []

    if not state.scenario:
        missing.append("scenario")
    if state.business_request is None:
        missing.append("business_request")

    required = _REQUIRED_FIELDS_BY_SCENARIO.get(state.scenario or "", [])
    business_request = state.business_request or {}

    for field_path in required:
        if not _get_nested(business_request, field_path):
            missing.append(field_path)

    return (len(missing) == 0, missing)


def handle_workflow_message(
    question: str,
    state: WorkflowState | None,
    conversation_id: str | None,
    user_context: Any,
    auth_header: str,
) -> dict | None:
    """Retourne un dict `{"answer": ...}` si le message a été traité ici
    (confirmation, annulation, retry, ou état incomplet), ou None si le
    message doit être transmis à `pydantic_agent.ask()`."""

    if state and state.status == WorkflowStatus.EXECUTING:
        return {"answer": ALREADY_IN_PROGRESS_MESSAGE}

    active_statuses = {
        WorkflowStatus.WAITING_CONFIRMATION,
        WorkflowStatus.WAITING_CLARIFICATION,
        WorkflowStatus.FAILED,
    }

    if not state or state.status not in active_statuses:
        if is_confirmation(question):
            return {"answer": NO_ACTION_PENDING_MESSAGE}
        if is_cancellation(question):
            return {"answer": NO_CANCELLATION_PENDING_MESSAGE}
        return None

    if is_cancellation(question):
        clear_workflow_state(conversation_id)
        return {"answer": "D’accord, j’annule cette action."}

    if state.status == WorkflowStatus.FAILED:
        if not is_retry(question):
            if not state.error_recoverable:
                clear_workflow_state(conversation_id)
            return None

        if not state.error_recoverable:
            clear_workflow_state(conversation_id)
            return {"answer": NOT_RETRYABLE_MESSAGE}

        if state.retry_count >= MAX_RETRY_COUNT:
            clear_workflow_state(conversation_id)
            return {"answer": TOO_MANY_RETRIES_MESSAGE}

        state.retry_count += 1
        return _execute(state, conversation_id, user_context, auth_header)

    if state.status == WorkflowStatus.WAITING_CONFIRMATION:
        if not is_confirmation(question):
            return None

        is_valid, missing = validate_state_before_execution(state)
        if not is_valid:
            state.missing_fields = missing
            state.transition_to(WorkflowStatus.WAITING_CLARIFICATION)
            save_workflow_state(state)
            logger.warning("État incomplet avant exécution (conversation_id=%s): %s", conversation_id, missing)
            return {"answer": STATE_INCOMPLETE_MESSAGE}

        return _execute(state, conversation_id, user_context, auth_header)

    # WAITING_CLARIFICATION redevient un no-op en attendant la reprise
    # de la Clarification Active (fichiers dédiés commentés côté user).
    if state.status == WorkflowStatus.WAITING_CLARIFICATION:
        return None

    return None


def _execute(
    state: WorkflowState,
    conversation_id: str | None,
    user_context: Any,
    auth_header: str,
) -> dict:
    """Exécute un scénario confirmé. La transition vers EXECUTING avant l'appel
    Hub est la protection contre la double confirmation."""

    try:
        state.transition_to(WorkflowStatus.EXECUTING)
    except Exception:
        logger.warning(
            "Exécution refusée, transition invalide depuis %s (conversation_id=%s)",
            state.status, conversation_id,
        )
        return {"answer": ALREADY_IN_PROGRESS_MESSAGE}

    save_workflow_state(state)

    result = execute_confirmed_scenario(
        scenario=state.scenario,
        business_request=state.business_request or {},
        user_context=user_context,
        auth_header=auth_header,
    )

    ok = result.get("ok", True)
    recoverable = result.get("recoverable", False)

    if ok:
        state.transition_to(WorkflowStatus.COMPLETED)
        clear_workflow_state(conversation_id)
        return {"answer": result["answer"]}

    state.error = result["answer"]
    state.error_recoverable = recoverable
    state.transition_to(WorkflowStatus.FAILED)

    if recoverable:
        save_workflow_state(state)
    else:
        clear_workflow_state(conversation_id)

    return {"answer": result["answer"]}