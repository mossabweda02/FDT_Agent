"""
Module: backend.core.business.handlers.multi_project_same_day_handler
======================================
Gestionnaire pour plusieurs projets saisis le même jour.
"""

from backend.core.business.business_types import ExecutionPlan, PlanStep
from backend.core.business.handlers.base import ScenarioHandler


class MultiProjectSameDayHandler(ScenarioHandler):
    def build(self, message: str, intent: str | None, scenario: str) -> ExecutionPlan:
        return ExecutionPlan(
            intent=intent,
            scenario=scenario,
            requires_confirmation=True,
            steps=[
                PlanStep(
                    action="create_timesheet_line_per_project",
                    tool="hub_create_timesheet_line",
                    params={"repeat": "same_day_multi_project"},
                )
            ],
        )