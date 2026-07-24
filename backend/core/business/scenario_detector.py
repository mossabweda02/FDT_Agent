"""
Module: backend.business.scenario_detector
======================================
Détecteur de scénarios métier.

Ce module fournit des fonctions pour détecter le scénario métier à partir du message utilisateur et de l'intention métier.
Les scénarios métier sont définis dans le module backend.business.business_types.
"""

from __future__ import annotations

import re
import unicodedata

from backend.core.business.business_types import (
    BusinessScenario,
    ScenarioDetectionResult,
)


def detect_business_scenario(message: str, intent: str | None) -> ScenarioDetectionResult:
    text = _normalize_text(message)

    if intent == "CREATE_TIMESHEET":
        return ScenarioDetectionResult(
            scenario=BusinessScenario.CREATE_EMPTY_TIMESHEET,
            reason="Demande de création de feuille de temps.",
        )

    if intent in {"ADD_TIME_ENTRY", "ADD_MULTIPLE_TIME_ENTRIES"}:
        if _is_repeat_over_date_range(text):
            return ScenarioDetectionResult(
                scenario=BusinessScenario.REPEAT_ENTRY_OVER_DATE_RANGE,
                reason="Même saisie à répéter sur plusieurs jours.",
            )

        if _is_multi_task_same_project(text):
            return ScenarioDetectionResult(
                scenario=BusinessScenario.MULTI_TASK_SAME_PROJECT,
                reason="Plusieurs tâches détectées pour un même projet.",
            )

        if _is_multi_project_same_day(text):
            return ScenarioDetectionResult(
                scenario=BusinessScenario.MULTI_PROJECT_SAME_DAY,
                reason="Plusieurs projets distincts détectés sur une même journée.",
            )

        return ScenarioDetectionResult(
            scenario=BusinessScenario.SINGLE_TIME_ENTRY,
            reason="Une seule ligne de temps détectée.",
        )

    return ScenarioDetectionResult(
        scenario=BusinessScenario.UNKNOWN_SCENARIO,
        reason="Aucun scénario métier reconnu.",
    )


def _normalize_text(message: str | None) -> str:
    text = (message or "").lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text)


def _is_repeat_over_date_range(text: str) -> bool:
    markers = (
        "du lundi au vendredi",
        "toute la semaine",
        "tous les jours",
        "chaque jour",
        "lundi a vendredi",
        "lundi jusqu",
    )
    return any(marker in text for marker in markers)


def _extract_unique_refs(text: str, prefix: str) -> set[str]:
    return set(re.findall(rf"\b{re.escape(prefix)}-[a-z0-9_-]+\b", text))


def _extract_named_projects_after_sur(text: str) -> list[str]:
    matches = re.findall(
        r"\b\d+(?:[.,]\d+)?\s*(?:h|heure|heures)\s+sur\s+"
        r"(.+?)(?=,\s*(?:la\s+)?tache\b)",
        text,
    )
    return [re.sub(r"\s+", " ", value).strip(" ,.") for value in matches]


def _is_multi_project_same_day(text: str) -> bool:
    project_refs = _extract_unique_refs(text, "prj")
    if len(project_refs) > 1:
        return True

    named_projects = _extract_named_projects_after_sur(text)
    return len(set(named_projects)) > 1


def _is_multi_task_same_project(text: str) -> bool:
    task_refs = _extract_unique_refs(text, "tsk")
    project_refs = _extract_unique_refs(text, "prj")

    # Deux tâches distinctes sur un seul projet unique.
    if len(task_refs) > 1 and len(project_refs) <= 1:
        return True

    # Forme naturelle :
    # "Ajoute sur Nova Construction 2h pour tâche A et 2h pour tâche B".
    hour_values = re.findall(r"\b\d+(?:[.,]\d+)?\s*(?:h|heure|heures)\b", text)
    if len(hour_values) > 1 and text.count(" pour ") >= 2:
        named_projects = _extract_named_projects_after_sur(text)
        return len(set(named_projects)) <= 1

    return False