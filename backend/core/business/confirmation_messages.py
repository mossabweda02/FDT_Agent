"""
Module: backend.core.business.confirmation_messages
======================================
Construit le message de confirmation en fonction du scénario réellement
détecté — jamais improvisé, jamais générique par défaut si évitable.
"""

from __future__ import annotations

from backend.core.business.business_types import BusinessScenario


def build_confirmation_message(scenario: str, business_request) -> str:
    entries = business_request.entries
    timesheet_nbr = business_request.timesheet.number

    if scenario == str(BusinessScenario.CREATE_EMPTY_TIMESHEET):
        return "Je vais créer une nouvelle feuille de temps vide. Confirmer ?"

    if not entries:
        return "Je vais exécuter cette action. Confirmer ?"

    if scenario == str(BusinessScenario.SINGLE_TIME_ENTRY):
        e = entries[0]
        return (
            f"Je vais ajouter **{e.hours:g}h** le **{e.date or '?'}** "
            f"sur le projet **{e.project}**, tâche **{e.task}**, "
            f"catégorie **{e.category}**, pour la feuille **{timesheet_nbr}**. Confirmer ?"
        )

    if scenario == str(BusinessScenario.REPEAT_ENTRY_OVER_DATE_RANGE):
        e = entries[0]
        return (
            f"Je vais ajouter **{e.hours:g}h** du lundi au vendredi "
            f"sur le projet **{e.project}**, tâche **{e.task}**, "
            f"catégorie **{e.category}**, pour la feuille **{timesheet_nbr}**. Confirmer ?"
        )

    if scenario in {str(BusinessScenario.MULTI_PROJECT_SAME_DAY), str(BusinessScenario.MULTI_TASK_SAME_PROJECT)}:
        detail = ", ".join(f"{e.hours:g}h sur {e.project}/{e.task}" for e in entries if e.hours)
        return f"Je vais ajouter **{len(entries)} lignes** ({detail}) pour la feuille **{timesheet_nbr}**. Confirmer ?"

    return "Je vais exécuter cette action. Confirmer ?"