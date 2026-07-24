"""
Module: backend.business.handlers.single_time_entry_handler
======================================
Ce module fournit un gestionnaire pour le scénario de création d'entrée de temps unique.
"""

from backend.core.business.business_types import ExecutionPlan, PlanStep
from backend.core.business.handlers.base import ScenarioHandler


class SingleTimeEntryHandler(ScenarioHandler):
    def build(self, message: str, intent: str | None, scenario: str) -> ExecutionPlan:
        return ExecutionPlan(
            intent=intent,
            scenario=scenario,
            requires_confirmation=True,
            steps=[
                PlanStep(
                    action="create_timesheet_line",
                    tool="hub_create_timesheet_line",
                )
            ],
        )