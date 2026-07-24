"""
Module: backend.business.execution_plan
======================================
Ce module fournit des fonctions pour construire un plan d'exécution métier à partir de l'intention 
et du scénario détectés dans la question utilisateur.
"""

from backend.core.business.business_types import BusinessScenario, ExecutionPlan
from backend.core.business.handlers.create_timesheet_handler import CreateTimesheetHandler
from backend.core.business.handlers.repeat_entry_handler import RepeatEntryHandler
from backend.core.business.handlers.single_time_entry_handler import SingleTimeEntryHandler
from backend.core.business.handlers.multi_project_same_day_handler import MultiProjectSameDayHandler
from backend.core.business.handlers.multi_task_same_project_handler import MultiTaskSameProjectHandler

SCENARIO_HANDLERS = {
    BusinessScenario.CREATE_EMPTY_TIMESHEET: CreateTimesheetHandler(),
    BusinessScenario.SINGLE_TIME_ENTRY: SingleTimeEntryHandler(),
    BusinessScenario.REPEAT_ENTRY_OVER_DATE_RANGE: RepeatEntryHandler(),
    BusinessScenario.MULTI_PROJECT_SAME_DAY: MultiProjectSameDayHandler(),
    BusinessScenario.MULTI_TASK_SAME_PROJECT: MultiTaskSameProjectHandler(),
}

def build_execution_plan(
    message: str,
    intent: str | None,
    scenario: str,
) -> ExecutionPlan:
    scenario_key = _normalize_scenario(scenario)
    handler = SCENARIO_HANDLERS.get(scenario_key)

    if not handler:
        return ExecutionPlan(
            intent=intent,
            scenario=scenario,
            requires_confirmation=False,
            steps=[],
            notes=["Aucun handler disponible pour ce scénario."],
        )

    return handler.build(message=message, intent=intent, scenario=str(scenario_key))


def _normalize_scenario(scenario: str) -> BusinessScenario | None:
    try:
        return BusinessScenario(str(scenario))
    except ValueError:
        return None