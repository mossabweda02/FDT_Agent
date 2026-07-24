"""
Module: backend.business.intent_classifier
======================================
Classifie les messages utilisateur en intentions métier (création, ajout, modification, suppression, consultation, confirmation ou annulation) à partir de règles déterministes et de mots-clés.
Il constitue le premier niveau d'analyse du workflow métier en orientant chaque demande vers le scénario de traitement approprié.

"""
from __future__ import annotations

import re
import unicodedata

def classify_business_intent(message: str) -> str | None:
    text = _normalize_text(message)

    if text in {"oui", "ok", "confirmer", "confirme", "continue", "continuer", "vas-y"}:
        return "CONFIRM_ACTION"

    if text in {"non", "annuler", "stop", "abandonner"}:
        return "CANCEL_ACTION"

    # L'ajout doit être prioritaire sur la création. Ainsi, un nom de tâche
    # comme "Prepare building permit..." ne déclenche pas CREATE_TIMESHEET.
    add_words = {"ajoute", "ajouter", "saisis", "saisir", "mets", "mettre", "enregistre"}
    if _contains_word(text, add_words) or _looks_like_time_entry(text):
        return (
            "ADD_MULTIPLE_TIME_ENTRIES"
            if _looks_multiple_entries(text)
            else "ADD_TIME_ENTRY"
        )

    update_words = {"modifie", "modifier", "change", "corrige", "remplace"}
    if _contains_word(text, update_words):
        return "UPDATE_TIME_ENTRY"

    delete_words = {"supprime", "supprimer", "efface", "retire", "enleve"}
    if _contains_word(text, delete_words):
        return "DELETE_TIME_ENTRY"

    if _asks_for_hours_total(text):
        return "CONSULT_TIMESHEET"

    consult_words = {"affiche", "montre", "liste", "consulte", "voir", "detail"}
    timesheet_patterns = (
        r"\bfeuilles?\b",
        r"\btimesheets?\b",
        r"\bfdt\b",
    )    
    time_words = {"heure", "heures", "temps", "ligne", "entry"}

    has_timesheet_reference = any(
        re.search(pattern, text)
        for pattern in timesheet_patterns
    )
    if _contains_word(text, consult_words) and (has_timesheet_reference
        or _contains_word(text, time_words)
    ):
        return "CONSULT_TIMESHEET"

    create_patterns = (
        r"\bcre(?:e|er|ez|ons)\b",
        r"\bouvrir\b",
        r"\bnouvelle?\b",
        r"\bpreparer\b",
        r"\bprepare\b",
    )
    if (
        any(re.search(pattern, text) for pattern in create_patterns)
        and has_timesheet_reference
    ):
        return "CREATE_TIMESHEET"

    return None


def _normalize_text(message: str | None) -> str:
    text = (message or "").lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text)


def _contains_word(text: str, words: set[str]) -> bool:
    return any(
        re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", text)
        for word in words
    )


def _asks_for_hours_total(text: str) -> bool:
    patterns = (
        r"\btotal\s+(?:des?\s+)?heures?\b",
        r"\bcombien\s+d[' ]?heures?\b",
        r"\bcumul\s+(?:des?\s+)?heures?\b",
        r"\bsomme\s+(?:des?\s+)?heures?\b",
        r"\bnombre\s+d[' ]?heures?\b",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _looks_like_time_entry(text: str) -> bool:
    has_hours = bool(re.search(r"\b\d+(?:[.,]\d+)?\s*(?:h|heure|heures)\b", text))
    has_project_or_task = "prj-" in text or "tsk-" in text
    days = {
        "lundi", "mardi", "mercredi", "jeudi",
        "vendredi", "samedi", "dimanche",
        "aujourd'hui", "hier", "demain",
    }
    return has_hours and has_project_or_task and any(day in text for day in days)


def _looks_multiple_entries(text: str) -> bool:
    markers = (
        "du lundi au vendredi",
        "toute la semaine",
        "chaque jour",
        "tous les jours",
        "plusieurs projets",
        "plusieurs taches",
        "plusieurs tasks",
    )
    if any(marker in text for marker in markers):
        return True

    hour_values = re.findall(r"\b\d+(?:[.,]\d+)?\s*(?:h|heure|heures)\b", text)
    if len(hour_values) > 1:
        return True

    project_refs = re.findall(r"\bprj-[a-z0-9_-]+\b", text)
    task_refs = re.findall(r"\btsk-[a-z0-9_-]+\b", text)
    if len(set(project_refs)) > 1 or len(set(task_refs)) > 1:
        return True

    days = re.findall(
        r"\b(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b",
        text,
    )
    return len(set(days)) > 1