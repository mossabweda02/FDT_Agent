"""
Module: backend.core.business.timesheet_resolution
==================================================

Résolution et recherche métier des feuilles de temps.

Ce package transforme une référence temporelle en période calendaire,
puis recherche les feuilles de l'utilisateur qui correspondent à cette
période sans effectuer d'action d'écriture.
"""

from backend.core.business.timesheet_resolution.models import (
    ResolvedTimesheetPeriod,
    TimesheetLookupResult,
    TimesheetPeriodGranularity,
    TimesheetSummary,
)
from backend.core.business.timesheet_resolution.period_resolver import (
    TimesheetPeriodResolutionError,
    resolve_timesheet_period,
)
from backend.core.business.timesheet_resolution.timesheet_finder import (
    TimesheetFinderError,
    find_timesheets_for_period,
    periods_overlap,
)

__all__ = [
    "ResolvedTimesheetPeriod",
    "TimesheetFinderError",
    "TimesheetLookupResult",
    "TimesheetPeriodGranularity",
    "TimesheetPeriodResolutionError",
    "TimesheetSummary",
    "find_timesheets_for_period",
    "periods_overlap",
    "resolve_timesheet_period",
]