"""
Module: backend.business.handlers.repeat_entry_handler
======================================
Ce module fournit un gestionnaire pour le scénario de création d'entrée de temps répétée.
"""

from typing import Any

from backend.core.business.business_types import ExecutionPlan, PlanStep
from backend.core.business.handlers.base import ScenarioHandler


class RepeatEntryHandler(ScenarioHandler):
    def build(self, message: str, intent: str | None, scenario: str) -> ExecutionPlan:
        text = (message or "").lower()

        return ExecutionPlan(
            intent=intent,
            scenario=scenario,
            requires_confirmation=True,
            steps=[
                PlanStep(
                    action="resolve_timesheet_period",
                    tool="hub_get_timesheet",
                    params=_extract_timesheet_params(text),
                ),
                PlanStep(
                    action="create_multiple_timesheet_lines",
                    tool="hub_create_timesheet_line",
                    params={
                        "repeat": "weekday_range",
                    },
                ),
            ],
        )


def _extract_timesheet_params(text: str) -> dict[str, Any]:
    for token in text.replace(",", " ").split():
        if token.upper().startswith("TS-"):
            return {"timesheet_nbr": token.upper()}
    return {}