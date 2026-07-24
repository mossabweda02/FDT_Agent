from types import SimpleNamespace
import pytest

from backend.core.business import workflow_manager
from backend.core.business.workflow_state import WorkflowState, WorkflowStatus


def make_state(**overrides):
    defaults = dict(
        conversation_id="conv-1",
        status=WorkflowStatus.WAITING_CONFIRMATION,
        scenario="SINGLE_TIME_ENTRY",
        business_request={
            "entries": [{"project": "PRJ-1", "task": "TSK-1", "category": "Dev", "date": "2026-07-13", "hours": 5}],
            "timesheet": {"number": "TS-0001"},
        },
    )
    defaults.update(overrides)
    return WorkflowState(**defaults)


USER_CTX = SimpleNamespace(resource_id="RES-1")


class TestNoActiveWorkflow:
    def test_confirmation_without_state_returns_canned_message(self):
        result = workflow_manager.handle_workflow_message("oui", None, "conv-x", USER_CTX, "Bearer x")
        assert result == {"answer": workflow_manager.NO_ACTION_PENDING_MESSAGE}

    def test_cancellation_without_state_returns_canned_message(self):
        result = workflow_manager.handle_workflow_message("non", None, "conv-x", USER_CTX, "Bearer x")
        assert result == {"answer": workflow_manager.NO_CANCELLATION_PENDING_MESSAGE}

    def test_normal_message_without_state_returns_none(self):
        result = workflow_manager.handle_workflow_message("combien d'heures ce mois ?", None, "conv-x", USER_CTX, "Bearer x")
        assert result is None


class TestConfirmationExecutesOnce:
    def test_valid_confirmation_calls_executor_once(self, monkeypatch):
        calls = []

        def fake_execute(**kwargs):
            calls.append(kwargs)
            return {"answer": "OK", "ok": True, "recoverable": False}

        monkeypatch.setattr(workflow_manager, "execute_confirmed_scenario", fake_execute)

        state = make_state()
        result = workflow_manager.handle_workflow_message("oui", state, "conv-1", USER_CTX, "Bearer x")

        assert result == {"answer": "OK"}
        assert len(calls) == 1
        assert state.status == WorkflowStatus.COMPLETED

    def test_second_confirmation_after_completion_is_a_noop(self, monkeypatch):
        """Une fois COMPLETED, une nouvelle 'confirme' ne doit RIEN redéclencher —
        elle est traitée comme 'aucune action en attente', pas comme une reprise."""
        calls = []

        def fake_execute(**kwargs):
            calls.append(kwargs)
            return {"answer": "OK", "ok": True, "recoverable": False}

        monkeypatch.setattr(workflow_manager, "execute_confirmed_scenario", fake_execute)

        state = make_state()
        workflow_manager.handle_workflow_message("oui", state, "conv-1", USER_CTX, "Bearer x")
        result2 = workflow_manager.handle_workflow_message("oui", state, "conv-1", USER_CTX, "Bearer x")

        assert len(calls) == 1
        assert result2 == {"answer": workflow_manager.NO_ACTION_PENDING_MESSAGE}

    def test_confirmation_blocked_while_executing(self):
        """Protection réelle contre la double confirmation concurrente :
        un message reçu PENDANT l'exécution (avant COMPLETED/FAILED) est refusé,
        pas réinterprété comme une nouvelle demande."""
        state = make_state()
        state.transition_to(WorkflowStatus.EXECUTING)

        result = workflow_manager.handle_workflow_message("oui", state, "conv-1", USER_CTX, "Bearer x")

        assert result == {"answer": workflow_manager.ALREADY_IN_PROGRESS_MESSAGE}

    def test_cancellation_does_not_call_executor(self, monkeypatch):
        calls = []
        monkeypatch.setattr(workflow_manager, "execute_confirmed_scenario", lambda **kw: calls.append(kw))

        state = make_state()
        result = workflow_manager.handle_workflow_message("non merci", state, "conv-1", USER_CTX, "Bearer x")

        assert calls == []
        assert result == {"answer": "D’accord, j’annule cette action."}


class TestRecoverableFailureAndRetry:
    def test_recoverable_failure_keeps_state_as_failed(self, monkeypatch):
        monkeypatch.setattr(
            workflow_manager, "execute_confirmed_scenario",
            lambda **kw: {"answer": "erreur temporaire", "ok": False, "recoverable": True},
        )
        state = make_state()
        workflow_manager.handle_workflow_message("oui", state, "conv-1", USER_CTX, "Bearer x")

        assert state.status == WorkflowStatus.FAILED
        assert state.error_recoverable is True

    def test_retry_calls_executor_again_and_increments_count(self, monkeypatch):
        calls = []

        def fake_execute(**kw):
            calls.append(kw)
            return {"answer": "toujours en échec", "ok": False, "recoverable": True}

        monkeypatch.setattr(workflow_manager, "execute_confirmed_scenario", fake_execute)

        state = make_state(status=WorkflowStatus.FAILED, error_recoverable=True, retry_count=0)
        workflow_manager.handle_workflow_message("réessayer", state, "conv-1", USER_CTX, "Bearer x")

        assert len(calls) == 1
        assert state.retry_count == 1

    def test_retry_exhausted_returns_message_and_clears(self, monkeypatch):
        monkeypatch.setattr(workflow_manager, "execute_confirmed_scenario", lambda **kw: {"answer": "x", "ok": False, "recoverable": True})
        state = make_state(status=WorkflowStatus.FAILED, error_recoverable=True, retry_count=2)

        result = workflow_manager.handle_workflow_message("réessayer", state, "conv-1", USER_CTX, "Bearer x")
        assert result == {"answer": workflow_manager.TOO_MANY_RETRIES_MESSAGE}

    def test_non_recoverable_failure_blocks_retry(self):
        state = make_state(status=WorkflowStatus.FAILED, error_recoverable=False)
        result = workflow_manager.handle_workflow_message("réessayer", state, "conv-1", USER_CTX, "Bearer x")
        assert result == {"answer": workflow_manager.NOT_RETRYABLE_MESSAGE}


class TestSuccessClearsState:
    def test_success_clears_state(self, monkeypatch):
        from backend.core.business import workflow_state as ws
        monkeypatch.setattr(workflow_manager, "execute_confirmed_scenario", lambda **kw: {"answer": "OK", "ok": True, "recoverable": False})

        state = make_state()
        ws.save_workflow_state(state)
        workflow_manager.handle_workflow_message("oui", state, "conv-1", USER_CTX, "Bearer x")

        assert ws.get_workflow_state("conv-1") is None


class TestIncompleteState:
    def test_missing_entries_blocks_execution(self, monkeypatch):
        calls = []
        monkeypatch.setattr(workflow_manager, "execute_confirmed_scenario", lambda **kw: calls.append(kw))

        state = make_state(business_request={"entries": [], "timesheet": {"number": "TS-0001"}})
        result = workflow_manager.handle_workflow_message("oui", state, "conv-1", USER_CTX, "Bearer x")

        assert calls == []
        assert result == {"answer": workflow_manager.STATE_INCOMPLETE_MESSAGE}
        assert state.status == WorkflowStatus.WAITING_CLARIFICATION

    def test_missing_scenario_detected(self):
        state = make_state(scenario=None)
        is_valid, missing = workflow_manager.validate_state_before_execution(state)
        assert is_valid is False
        assert "scenario" in missing

    def test_missing_business_request_detected(self):
        state = make_state(business_request=None)
        is_valid, missing = workflow_manager.validate_state_before_execution(state)
        assert is_valid is False
        assert "business_request" in missing

    def test_create_empty_timesheet_needs_nothing_extra(self):
        state = make_state(scenario="CREATE_EMPTY_TIMESHEET", business_request={})
        is_valid, missing = workflow_manager.validate_state_before_execution(state)
        assert is_valid is True
        assert missing == []