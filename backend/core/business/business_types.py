"""
Module: backend.business.business_types
======================================
Ce module fournit des types et classes pour représenter les différents scénarios métier et intentions dans le système.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class BusinessScenario(StrEnum):
    CREATE_EMPTY_TIMESHEET = "CREATE_EMPTY_TIMESHEET"
    SINGLE_TIME_ENTRY = "SINGLE_TIME_ENTRY"
    REPEAT_ENTRY_OVER_DATE_RANGE = "REPEAT_ENTRY_OVER_DATE_RANGE"
    MULTI_PROJECT_SAME_DAY = "MULTI_PROJECT_SAME_DAY"
    MULTI_TASK_SAME_PROJECT = "MULTI_TASK_SAME_PROJECT"
    UNKNOWN_SCENARIO = "UNKNOWN_SCENARIO"


@dataclass
class ScenarioDetectionResult:
    scenario: BusinessScenario
    reason: str


@dataclass
class PlanStep:
    action: str
    tool: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    intent: str | None
    scenario: str
    requires_confirmation: bool
    steps: list[PlanStep]
    missing_fields: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

@dataclass
class BusinessEntities:
    timesheet_nbr: str | None = None
    project_id: str | None = None
    task_id: str | None = None
    category_id: str | None = None
    deliverable_id: str | None = None
    hours: float | None = None
    date: str | None = None
    repeat_type: str | None = None