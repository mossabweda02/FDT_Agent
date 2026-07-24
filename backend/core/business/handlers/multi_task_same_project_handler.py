"""
Module: backend.core.business.handlers.multi_task_same_project_handler
======================================
Gestionnaire pour plusieurs tâches saisies le même jour sur un même projet.
"""

from backend.core.business.business_types import ExecutionPlan, PlanStep
from backend.core.business.handlers.base import ScenarioHandler


class MultiTaskSameProjectHandler(ScenarioHandler):
    def build(self, message: str, intent: str | None, scenario: str) -> ExecutionPlan:
        return ExecutionPlan(
            intent=intent,
            scenario=scenario,
            requires_confirmation=True,
            steps=[
                PlanStep(
                    action="create_timesheet_line_per_task",
                    tool="hub_create_timesheet_line",
                    params={"repeat": "same_day_multi_task"},
                )
            ],
        )