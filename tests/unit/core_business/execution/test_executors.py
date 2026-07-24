from types import SimpleNamespace
from backend.core.business import executors

USER_CTX = SimpleNamespace(resource_id="RES-1")


def _entry(**overrides):
    base = {"project": "PRJ-1", "task": "TSK-1", "category": "Dev", "hours": 5, "date": None, "repeat_type": "none"}
    base.update(overrides)
    return base


class TestResolveEntryDates:
    def test_none_repeat_with_date_returns_single_date(self):
        dates, error = executors._resolve_entry_dates(
            _entry(date="2026-07-13", repeat_type="none"), "TS-1", "RES-1", "Bearer x",
        )
        assert dates == ["2026-07-13"]
        assert error is None

    def test_none_repeat_without_date_fails(self):
        dates, error = executors._resolve_entry_dates(
            _entry(date=None, repeat_type="none"), "TS-1", "RES-1", "Bearer x",
        )
        assert dates == []
        assert error == "missing_date"

    def test_weekday_range_expands_using_resolved_period(self, monkeypatch):
        monkeypatch.setattr(
            executors, "resolve_timesheet_period",
            lambda **kw: ("2026-07-13", "2026-07-19", {}),
        )
        dates, error = executors._resolve_entry_dates(
            _entry(repeat_type="weekday_range"), "TS-1", "RES-1", "Bearer x",
        )
        assert dates == ["2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17"]
        assert error is None

    def test_daily_range_includes_weekend(self, monkeypatch):
        monkeypatch.setattr(
            executors, "resolve_timesheet_period",
            lambda **kw: ("2026-07-18", "2026-07-19", {}),
        )
        dates, error = executors._resolve_entry_dates(
            _entry(repeat_type="daily_range"), "TS-1", "RES-1", "Bearer x",
        )
        assert dates == ["2026-07-18", "2026-07-19"]

    def test_range_fails_when_period_unresolved(self, monkeypatch):
        monkeypatch.setattr(executors, "resolve_timesheet_period", lambda **kw: (None, None, {}))
        dates, error = executors._resolve_entry_dates(
            _entry(repeat_type="weekday_range"), "TS-1", "RES-1", "Bearer x",
        )
        assert dates == []
        assert error == "period_unresolved"


class TestExecuteMultiEntries:
    def _business_request(self, entries):
        return {"entries": entries, "timesheet": {"number": "TS-0001"}}

    def test_single_project_single_day(self, monkeypatch):
        monkeypatch.setattr(executors, "_create_line", lambda entry, ts, uc, ah: {"ok": True})

        result = executors.execute_multi_entries(
            self._business_request([_entry(date="2026-07-13")]), USER_CTX, "Bearer x",
        )
        assert result["ok"] is True
        assert "1 lignes" in result["answer"]

    def test_multi_project_multi_day(self, monkeypatch):
        """Le vrai cas visé par le point 2 : deux entrées, chacune avec son
        propre repeat_type, projets différents."""
        monkeypatch.setattr(executors, "_create_line", lambda entry, ts, uc, ah: {"ok": True})
        monkeypatch.setattr(
            executors, "resolve_timesheet_period",
            lambda **kw: ("2026-07-13", "2026-07-15", {}),
        )

        entries = [
            _entry(project="PRJ-1", repeat_type="weekday_range"),  # -> 3 jours (13,14,15 = lun-mer)
            _entry(project="PRJ-2", date="2026-07-20", repeat_type="none"),  # -> 1 jour
        ]
        result = executors.execute_multi_entries(self._business_request(entries), USER_CTX, "Bearer x")

        assert result["ok"] is True
        assert "4 lignes" in result["answer"]

    def test_period_unresolved_and_nothing_written_is_recoverable(self, monkeypatch):
        monkeypatch.setattr(executors, "resolve_timesheet_period", lambda **kw: (None, None, {}))

        entries = [_entry(repeat_type="weekday_range")]
        result = executors.execute_multi_entries(self._business_request(entries), USER_CTX, "Bearer x")

        assert result["ok"] is False
        assert result["recoverable"] is True

    def test_partial_write_is_not_recoverable(self, monkeypatch):
        call_count = {"n": 0}

        def fake_create_line(entry, ts, uc, ah):
            call_count["n"] += 1
            return {"ok": call_count["n"] == 1}  # 1re réussit, 2e échoue

        monkeypatch.setattr(executors, "_create_line", fake_create_line)

        entries = [_entry(date="2026-07-13"), _entry(project="PRJ-2", date="2026-07-14")]
        result = executors.execute_multi_entries(self._business_request(entries), USER_CTX, "Bearer x")

        assert result["ok"] is False
        assert result["recoverable"] is False
        assert "1 lignes ajoutées" in result["answer"]
        assert "1 échecs" in result["answer"]

    def test_missing_entries_or_timesheet(self):
        result = executors.execute_multi_entries({"entries": [], "timesheet": {}}, USER_CTX, "Bearer x")
        assert result["ok"] is False
        assert result["recoverable"] is False