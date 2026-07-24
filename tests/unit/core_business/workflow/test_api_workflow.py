from types import SimpleNamespace
from fastapi.testclient import TestClient

from backend.server import api_server
from backend.core.business.workflow_state import WorkflowState, WorkflowStatus, save_workflow_state, clear_workflow_state

client = TestClient(api_server.app)

HEADERS = {"Authorization": "Bearer test-token"}


def _fake_user_context(auth_header):
    return SimpleNamespace(resource_id="RES-1", email="x@y.com", fullname="X Y", resource_resolution_status="resolved")


def test_confirmation_valid_calls_executor_once(monkeypatch):
    monkeypatch.setattr(api_server, "resolve_user_context", _fake_user_context)

    calls = []
    def fake_handle(**kwargs):
        calls.append(kwargs)
        return {"answer": "fait"}
    monkeypatch.setattr(api_server, "handle_workflow_message", fake_handle)

    resp = client.post("/ask", json={"question": "oui", "conversation_id": "conv-api-1"}, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json() == {"answer": "fait"}
    assert len(calls) == 1


def test_normal_message_calls_agent(monkeypatch):
    monkeypatch.setattr(api_server, "resolve_user_context", _fake_user_context)
    monkeypatch.setattr(api_server, "handle_workflow_message", lambda **kw: None)

    called = {}
    async def fake_ask(*args, **kwargs):
        called["invoked"] = True
        return "réponse LLM"
    monkeypatch.setattr(api_server.pydantic_agent, "ask", fake_ask)

    resp = client.post("/ask", json={"question": "combien d'heures ?", "conversation_id": "conv-api-2"}, headers=HEADERS)
    assert resp.status_code == 200
    assert called.get("invoked") is True


def test_confirmation_with_workflow_never_calls_agent(monkeypatch):
    monkeypatch.setattr(api_server, "resolve_user_context", _fake_user_context)
    monkeypatch.setattr(api_server, "handle_workflow_message", lambda **kw: {"answer": "traité par workflow"})

    async def fake_ask(*args, **kwargs):
        raise AssertionError("pydantic_agent.ask ne doit jamais être appelé ici")
    monkeypatch.setattr(api_server.pydantic_agent, "ask", fake_ask)

    resp = client.post("/ask", json={"question": "oui", "conversation_id": "conv-api-3"}, headers=HEADERS)
    assert resp.json() == {"answer": "traité par workflow"}