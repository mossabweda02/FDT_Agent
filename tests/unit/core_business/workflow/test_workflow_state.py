import pytest
from backend.core.business.workflow_state import (
    WorkflowState, WorkflowStatus, InvalidTransitionError,
    save_workflow_state, get_workflow_state, clear_workflow_state,
)


class TestStorage:
    def test_save_and_get_by_conversation_id(self):
        state = WorkflowState(conversation_id="conv-1", status=WorkflowStatus.WAITING_CONFIRMATION)
        save_workflow_state(state)
        assert get_workflow_state("conv-1").status == WorkflowStatus.WAITING_CONFIRMATION
        clear_workflow_state("conv-1")

    def test_isolation_between_conversations(self):
        save_workflow_state(WorkflowState(conversation_id="conv-a", scenario="A"))
        save_workflow_state(WorkflowState(conversation_id="conv-b", scenario="B"))
        assert get_workflow_state("conv-a").scenario == "A"
        assert get_workflow_state("conv-b").scenario == "B"
        clear_workflow_state("conv-a")
        clear_workflow_state("conv-b")

    def test_clear_removes_state(self):
        save_workflow_state(WorkflowState(conversation_id="conv-c"))
        clear_workflow_state("conv-c")
        assert get_workflow_state("conv-c") is None

    def test_get_unknown_conversation_returns_none(self):
        assert get_workflow_state("does-not-exist") is None


class TestTransitions:
    def test_idle_to_waiting_confirmation_valid(self):
        state = WorkflowState(conversation_id="c", status=WorkflowStatus.IDLE)
        state.transition_to(WorkflowStatus.WAITING_CONFIRMATION)
        assert state.status == WorkflowStatus.WAITING_CONFIRMATION

    def test_full_success_chain(self):
        state = WorkflowState(conversation_id="c", status=WorkflowStatus.WAITING_CONFIRMATION)
        state.transition_to(WorkflowStatus.EXECUTING)
        state.transition_to(WorkflowStatus.COMPLETED)
        assert state.status == WorkflowStatus.COMPLETED

    def test_cancellation_from_waiting_confirmation(self):
        state = WorkflowState(conversation_id="c", status=WorkflowStatus.WAITING_CONFIRMATION)
        state.transition_to(WorkflowStatus.CANCELLED)
        assert state.status == WorkflowStatus.CANCELLED

    def test_retry_from_failed(self):
        state = WorkflowState(conversation_id="c", status=WorkflowStatus.FAILED)
        state.transition_to(WorkflowStatus.EXECUTING)
        assert state.status == WorkflowStatus.EXECUTING

    def test_double_execution_blocked(self):
        state = WorkflowState(conversation_id="c", status=WorkflowStatus.EXECUTING)
        with pytest.raises(InvalidTransitionError):
            state.transition_to(WorkflowStatus.EXECUTING)

    def test_completed_is_terminal(self):
        state = WorkflowState(conversation_id="c", status=WorkflowStatus.COMPLETED)
        with pytest.raises(InvalidTransitionError):
            state.transition_to(WorkflowStatus.EXECUTING)

    def test_invalid_jump_idle_to_executing(self):
        state = WorkflowState(conversation_id="c", status=WorkflowStatus.IDLE)
        with pytest.raises(InvalidTransitionError):
            state.transition_to(WorkflowStatus.EXECUTING)