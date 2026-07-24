"""
Module: backend.business.handlers.create_timesheet_handler
======================================
Ce module fournit un gestionnaire pour le scénario de création de feuille de temps.
"""

from backend.core.business.business_types import ExecutionPlan, PlanStep
from backend.core.business.handlers.base import ScenarioHandler


class CreateTimesheetHandler(ScenarioHandler):
    def build(self, message: str, intent: str | None, scenario: str) -> ExecutionPlan:
        return ExecutionPlan(
            intent=intent,
            scenario=scenario,
            requires_confirmation=True,
            steps=[
                PlanStep(
                    action="create_timesheet",
                    tool="hub_create_timesheet",
                )
            ],
        )