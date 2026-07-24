import json
import httpx
import pytest

from backend.tools import hub_functions
from backend.tools.hub_functions import _get, hub_list_timesheets, hub_get_timesheet


class _FakeResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.text = text or json.dumps(self._json_data)

    @property
    def is_success(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._json_data


class TestGetTimeoutParam:
    def test_get_uses_default_timeout_when_not_specified(self, monkeypatch):
        captured = {}

        def fake_httpx_get(url, params=None, headers=None, timeout=None):
            captured["timeout"] = timeout
            return _FakeResponse(200, {"ok": True})

        monkeypatch.setattr(httpx, "get", fake_httpx_get)
        monkeypatch.setattr(hub_functions, "_headers", lambda auth_header=None: {})

        _get("/api/whatever", {}, auth_header="Bearer x")

        assert captured["timeout"] == 30.0

    def test_get_accepts_explicit_timeout(self, monkeypatch):
        captured = {}

        def fake_httpx_get(url, params=None, headers=None, timeout=None):
            captured["timeout"] = timeout
            return _FakeResponse(200, {"ok": True})

        monkeypatch.setattr(httpx, "get", fake_httpx_get)
        monkeypatch.setattr(hub_functions, "_headers", lambda auth_header=None: {})

        _get("/api/whatever", {}, auth_header="Bearer x", timeout=60)

        assert captured["timeout"] == 60

    def test_get_no_longer_raises_typeerror_with_timeout_kwarg(self, monkeypatch):
        def fake_httpx_get(url, params=None, headers=None, timeout=None):
            return _FakeResponse(200, {"ok": True})

        monkeypatch.setattr(httpx, "get", fake_httpx_get)
        monkeypatch.setattr(hub_functions, "_headers", lambda auth_header=None: {})

        # Ne doit pas lever TypeError
        result = _get("/api/whatever", {}, auth_header="Bearer x", timeout=60)
        assert json.loads(result)["ok"] is True


class TestHubListTimesheetsNoTypeError:
    def test_hub_list_timesheets_does_not_raise(self, monkeypatch):
        def fake_httpx_get(url, params=None, headers=None, timeout=None):
            assert timeout == 60
            return _FakeResponse(200, {"items": []})

        monkeypatch.setattr(httpx, "get", fake_httpx_get)
        monkeypatch.setattr(hub_functions, "_headers", lambda auth_header=None: {})

        result = hub_list_timesheets(resource_id="RES-3988", auth_header="Bearer x")
        payload = json.loads(result)
        assert payload["ok"] is True

    def test_hub_get_timesheet_does_not_raise(self, monkeypatch):
        def fake_httpx_get(url, params=None, headers=None, timeout=None):
            assert timeout == 60
            return _FakeResponse(200, {"timesheetNbr": "TS-0000318"})

        monkeypatch.setattr(httpx, "get", fake_httpx_get)
        monkeypatch.setattr(hub_functions, "_headers", lambda auth_header=None: {})

        result = hub_get_timesheet(timesheet_nbr="TS-0000318", resource_id="RES-3988", auth_header="Bearer x")
        payload = json.loads(result)
        assert payload["ok"] is True


class TestTimeoutBecomesStandardizedError:
    def test_httpx_timeout_returns_ok_false_status_zero(self, monkeypatch):
        def fake_httpx_get(url, params=None, headers=None, timeout=None):
            raise httpx.TimeoutException("Request timed out")

        monkeypatch.setattr(httpx, "get", fake_httpx_get)
        monkeypatch.setattr(hub_functions, "_headers", lambda auth_header=None: {})

        result = hub_list_timesheets(resource_id="RES-3988", auth_header="Bearer x", limit=50, skip=0)
        payload = json.loads(result)

        assert payload["ok"] is False
        assert payload["status"] == 0
        # aucune exception ne doit remonter — result est bien une string JSON exploitable
        assert isinstance(result, str)

    def test_no_exception_propagates_to_caller(self, monkeypatch):
        def fake_httpx_get(url, params=None, headers=None, timeout=None):
            raise httpx.ConnectTimeout("boom")

        monkeypatch.setattr(httpx, "get", fake_httpx_get)
        monkeypatch.setattr(hub_functions, "_headers", lambda auth_header=None: {})

        try:
            result = hub_get_timesheet(timesheet_nbr="TS-0000318", resource_id="RES-3988", auth_header="Bearer x")
        except Exception:
            pytest.fail("hub_get_timesheet ne doit jamais laisser remonter une exception")

        payload = json.loads(result)
        assert payload["ok"] is False