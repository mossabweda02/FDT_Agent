
from backend.core.business.business_request import BusinessRequest


def test_business_request_defaults():
    req = BusinessRequest()

    assert req.action.intent == "UNKNOWN"
    assert req.action.scenario == "UNKNOWN_SCENARIO"
    assert req.timesheet.period_mode == "unknown"
    assert req.entries == []


def test_business_request_with_entry():
    req = BusinessRequest.model_validate(
        {
            "action": {
                "intent": "ADD_MULTIPLE_TIME_ENTRIES",
                "scenario": "REPEAT_ENTRY_OVER_DATE_RANGE",
            },
            "timesheet": {
                "number": "TS-0000319",
                "period_mode": "timesheet_number",
            },
            "entries": [
                {
                    "project": "PRJ-00042",
                    "task": "TSK-00062",
                    "hours": 5,
                    "repeat_type": "weekday_range",
                }
            ],
        }
    )

    assert req.action.intent == "ADD_MULTIPLE_TIME_ENTRIES"
    assert req.timesheet.number == "TS-0000319"
    assert req.entries[0].project == "PRJ-00042"
    assert req.entries[0].hours == 5
    assert req.entries[0].repeat_type == "weekday_range"