"""
agent/question_sanitizer.py
============================
Sanitization des questions utilisateur pour l'observabilité.
La question originale est préservée pour l'agent — seul le log est anonymisé.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

# ────────────────────────────────────────────────────────────────────
# Stopwords métier (évite faux positifs)
# ────────────────────────────────────────────────────────────────────

GENERIC_BUSINESS_WORDS = {
    "consultant",
    "consultants",
    "employee",
    "employé",
    "employés",
    "projet",
    "project",
    "projets",
    "client",
    "clients",
    "heures",
    "heure",
    "travaille",
    "travaillent",
    "budget",
    "temps",
    "coût",
    "cout",
    "finance",
    "revenu",
    "revenus",
    "rentable",
    "rentables",
    "top",
    "meilleur",
    "meilleurs",
    "en",
    "janvier",
    "février",
    "fevrier",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "aout",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
    "decembre",
}


# ────────────────────────────────────────────────────────────────────
# Modèle résultat sanitization
# ────────────────────────────────────────────────────────────────────
# classe de retour de sanitize_question, avec hash, preview anonymisée, catégorie métier, et indicateur de PII détecté.

@dataclass
class SanitizedQuestion:
    hash: str             # sha256[:12] — identifiant unique stable
    preview: str          # question avec PII (Personally Identifiable Information) remplacés par placeholders
    category: str         # catégorie métier détectée
    pii_detected: bool    # True si au moins un pattern PII a matché

# ────────────────────────────────────────────────────────────────────
# Regex de base
# ────────────────────────────────────────────────────────────────────

# Pattern regex pour détecter les emails
EMAIL_RE = re.compile(
    r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b",
    re.IGNORECASE,
)

# Pattern regex pour détecter les montants
AMOUNT_RE = re.compile(
    r"""
    (?:
        \b\d{1,3}(?:[\s.,']\d{3})*(?:[.,]\d+)?\s*
        (?:€|eur|dh|mad|\$|usd)
    )
    |
    (?:
        (?:€|eur|dh|mad|\$|usd)\s*
        \d{1,3}(?:[\s.,']\d{3})*(?:[.,]\d+)?
    )
    |
    (?:
        \b\d+(?:[.,]\d+)?\s*
        (?:€|eur|dh|mad|\$|usd)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Pattern regex pour détecter les numéros de téléphone
PHONE_RE = re.compile(
    r"""
    (?:
        \+\d{1,3}[\s.-]*
    )?
    (?:
        \d[\s.-]*
    ){8,12}
    """,
    re.VERBOSE,
)

# Pattern regex pour détecter les identifiants employés 
EMPLOYEE_ID_RE = re.compile(
    r"\b(?:EMP|RH|MAT|RES)-?\d{3,}\b",
    re.IGNORECASE,
)

# Pattern regex pour détecter les codes projets
PROJECT_CODE_RE = re.compile(
    r"\bPRJ-?\d{3,}\b",
    re.IGNORECASE,
)

# ────────────────────────────────────────────────────────────────────
# Regex contextuelles
# ────────────────────────────────────────────────────────────────────
# Pattern regex pour détecter les noms de projets mentionnés explicitement ("projet X", "project Y")
PROJECT_NAMED_RE = re.compile(
    r"""
    \b
    (projet|project)
    \s+
    ([A-Z][A-Za-z0-9_-]+(?:\s+[A-Z][A-Za-z0-9_-]+)?)
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Pattern regex pour détecter les noms de clients mentionnés explicitement ("client X", "client chez Y", "client du projet Z")
CLIENT_NAMED_RE = re.compile(
    r"""
    \b
    (?P<prefix>
        sur\s+le\s+|
        chez\s+le\s+|
        du\s+|
        pour\s+le\s+|
        informations\s+
    )?
    (?P<keyword>client)
    \s+
    (?P<client>
        [A-Z][A-Za-z0-9_-]+
        (?:\s+[A-Z][A-Za-z0-9_-]+)?
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Pattern regex pour détecter les noms de personnes mentionnés après un contexte métier ("salaire de X", "a travaillé avec Y")
PERSON_AFTER_CONTEXT_RE = re.compile(
    r"""
    \b(?P<context>
        salaire\s+de|
        heures\s+de|
        a\s+travaillé|
        a\s+travaille|
        travaillées\s+par|
        travaillees\s+par|
        travaillé\s+par|
        travaille\s+par|
        employé|
        employee|
        collaborateur|
        consultant|
        ressource|
        worker
    )
    \s+
    (?P<person>
        [A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ][a-zàâéèêëîïôùûüç]+
        (?:\s+
        [A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ][a-zàâéèêëîïôùûüç]+)+
    )
    (?=
        \s+(?:en|sur|chez|du|de|pour|avec|entre|à|au|aux)\b
        |[?.!,]
        |$
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Pattern regex pour détecter les noms de personnes mentionnés avant un contexte métier ("X a travaillé sur Y", "Y travaille chez Z avec X")
PERSON_BEFORE_CONTEXT_RE = re.compile(
    r"""
    (?P<prefix>\b(?:pourquoi|est-ce\s+que|pourquoi\s+est-ce\s+que)?\s*)
    (?P<person>
        [A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ][a-zàâéèêëîïôùûüç]+
        (?:\s+
        [A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ][a-zàâéèêëîïôùûüç]+)+
    )
    \s+
    (?P<context>
        était\s+absent|
        etait\s+absent|
        a-t-il\s+travaillé|
        a-t-il\s+travaille|
        travaille\s+sur|
        travaille\s+chez
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# ────────────────────────────────────────────────────────────────────
# Catégories métier FDT
# ────────────────────────────────────────────────────────────────────

_CATEGORY_PATTERNS: list[tuple[str, str]] = [
    (r"heure|timesheet|saisie|enregistr|travaill", "heures"),
    (r"rentabl|marge|profit|coût|cout|cost|budget|revenu|frais|montant", "finance"),
    (r"tâche|task|activit", "tache"),
    (r"employ|ressource|worker|collabor|consultant|équipe|team", "employe"),
    (r"heure|timesheet|saisie|enregistr", "heures"),
    (r"projet|project|prj", "projet"),
    (r"approuv|valid|statut|status", "validation"),
    (r"top|meilleur|plus|premier|classement|ranking", "analytique"),
    (r"bonjour|merci|présente|aide|help|qu.est.ce", "conversationnel"),
]

# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

# fonction de hashage de question (identifier les questions similaires sans stocker le texte brut)
def _hash_question(question: str) -> str:
    return hashlib.sha256(
        question.encode("utf-8")
    ).hexdigest()[:12]

# fonction de détection de catégorie
def _detect_category(question: str) -> str:
    q_lower = question.lower()

    for pattern, category in _CATEGORY_PATTERNS:
        if re.search(pattern, q_lower):
            return category

    return "autre"

# fonction de troncature pour les questions très longues (garde les premiers 160 caractères, ajoute "..." si tronqué) 
# questions trop longues = peuvent contenir des données sensibles
def _truncate(text: str, max_length: int = 160) -> str:
    if len(text) <= max_length:
        return text

    return text[: max_length - 3].rstrip() + "..."


# ────────────────────────────────────────────────────────────────────
# Remplacements contextuels
# ────────────────────────────────────────────────────────────────────

def _replace_project_name(match: re.Match) -> str:
    keyword = match.group(1)
    project_name = match.group(2).strip()
    project_lower = project_name.lower()

    generic_words = GENERIC_BUSINESS_WORDS | {
        "en",
        "du",
        "de",
        "des",
        "par",
        "pour",
        "avec",
    }

    first_word = project_lower.split()[0]

    if first_word in generic_words:
        return match.group(0)

    if re.fullmatch(r"\d{4}", project_name):
        return match.group(0)

    return f"{keyword} [PROJECT]"


def _replace_client_name(match: re.Match) -> str:
    prefix = match.group("prefix") or ""
    keyword = match.group("keyword")
    return f"{prefix}{keyword} [CLIENT]"


def _replace_person_after_context(match: re.Match) -> str:
    person = match.group("person")

    if person.lower() in GENERIC_BUSINESS_WORDS:
        return match.group(0)

    return f"{match.group('context')} [PERSON]"


def _replace_person_before_context(match: re.Match) -> str:
    person = match.group("person")

    if person.lower() in GENERIC_BUSINESS_WORDS:
        return match.group(0)

    return f"{match.group('prefix')}[PERSON] {match.group('context')}"


# ────────────────────────────────────────────────────────────────────
# Fonction principale
# ────────────────────────────────────────────────────────────────────

def sanitize_question(
    question: str,
    truncate: bool = True,
) -> SanitizedQuestion:
    """
    Sanitization observabilité.

    Important :
    - la question originale reste inchangée
    - seule la version loggée est anonymisée
    """

    preview = question.strip()
    pii_found = False

    replacements: list[tuple[re.Pattern, str | callable]] = [
        (EMAIL_RE, "[EMAIL]"),
        (AMOUNT_RE, "[MONTANT]"),
        (PHONE_RE, "[TEL]"),
        (EMPLOYEE_ID_RE, "[MATRICULE]"),
        (PROJECT_CODE_RE, "[PROJECT]"),
        (CLIENT_NAMED_RE, _replace_client_name),
        (PROJECT_NAMED_RE, _replace_project_name),
        (PERSON_AFTER_CONTEXT_RE, _replace_person_after_context),
        (PERSON_BEFORE_CONTEXT_RE, _replace_person_before_context),
    ]

    for pattern, replacement in replacements:
        old_preview = preview
        preview = pattern.sub(replacement, preview)

        if old_preview != preview:
            pii_found = True

    # Nettoyage espaces
    preview = re.sub(r"\s{2,}", " ", preview).strip()

    # Tronquer uniquement hors tests
    if truncate:
        preview = _truncate(preview)

    return SanitizedQuestion(
        hash=_hash_question(question),
        preview=preview,
        category=_detect_category(question),
        pii_detected=pii_found,
    )