"""
tests/test_question_sanitizer_dynamic.py
========================================

Validation avancée et aléatoire du question_sanitizer FDT.

Principe :
- Génère une banque large de questions métier.
- Exécute 10 rounds de test.
- Chaque round sélectionne 20 questions aléatoires.
- Compare expected_preview vs actual_preview.
- Produit un score global de robustesse.

Usage :
    py -m tests.test_question_sanitizer_dynamic
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from agent.question_sanitizer import sanitize_question

# ────────────────────────────────────────────────────────────────────
# Couleurs console
# ────────────────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GRAY = "\033[90m"

ROUNDS = 10
QUESTIONS_PER_ROUND = 20
RANDOM_SEED = None  # mettre 42 pour rendre les tests reproductibles


@dataclass(frozen=True)
class TestCase:
    name: str
    question: str
    expected_preview: str
    expected_category: str | None = None
    expected_pii: bool | None = None


PERSONS = [
    "Mohamed Ben Ali",
    "Ahmed Salah",
    "Jean Dupont",
    "Sarah Martin",
    "Émilie Gagnon",
    "Anthony Collins",
    "Michael Brown",
    "John Doe",
]

PROJECTS = [
    "Alpha",
    "Atlas",
    "Fusion-2026",
    "PRJ-00329",
    "PRJ-00648",
    "PRJ-00987",
    "PRJ-12345",
]

CLIENTS = [
    "Airbus Defense",
    "Orange Business",
    "Total Energy",
    "Société Générale",
    "Renault Digital",
]

TASKS = [
    "Estimation",
    "Inspection & préparation du site",
    "Préparation du plancher",
    "Application apprêt",
]

CATEGORIES = [
    "Operateur",
    "Gestionnaire de projet",
    "Support",
    "Design",
    "Maladie",
]

ROLES = [
    "Software Engineer",
    "Project manager",
    "Product Owner",
    "Membre d'équipe",
]

LOCATIONS = [
    "Québec",
    "Centre Commercial Mapleview",
    "Centre Administratif Riverstone",
    "Bastien & Fils",
]

AMOUNTS = [
    "15000 EUR",
    "50 000 €",
    "1 250 000 EUR",
    "25 000 USD",
    "12 500 MAD",
]

EMAILS = [
    "mohamed.benali@company.com",
    "jean.dupont@company.com",
    "sarah.martin@company.com",
]

EMPLOYEE_IDS = [
    "EMP-458921",
    "RH-00987",
    "MAT-00329",
]

RESOURCE_IDS = [
    "RES-2936",
    "RES-3697",
    "RES-2958",
    "RES-3145",
]

TIMESHEETS = [
    "TS-0000021",
    "TS-0000036",
    "TS-0000259",
]


def color(text: str, color_code: str) -> str:
    return f"{color_code}{text}{RESET}"

def separator(char: str = "=", size: int = 100) -> str:
    return char * size


def build_question_bank() -> list[TestCase]:
    cases: list[TestCase] = []

    # ── Employés / RH ──────────────────────────────────────────────
    for person in PERSONS:
        cases.extend([
            TestCase(
                "employee_hours",
                f"Combien d’heures a travaillé {person} en janvier ?",
                "Combien d’heures a travaillé [PERSON] en janvier ?",
                "heures",
                True,
            ),
            TestCase(
                "employee_salary",
                f"Quel est le salaire de {person} ?",
                "Quel est le salaire de [PERSON] ?",
                None,
                True,
            ),
            TestCase(
                "employee_absence",
                f"Pourquoi {person} était absent la semaine dernière ?",
                "Pourquoi [PERSON] était absent la semaine dernière ?",
                None,
                True,
            ),
            TestCase(
                "employee_project_work",
                f"Est-ce que {person} a travaillé sur le projet Alpha en décembre 2025 ?",
                "Est-ce que [PERSON] a travaillé sur le projet [PROJECT] en décembre 2025 ?",
                "heures",
                True,
            ),
        ])

    # ── Projets ────────────────────────────────────────────────────
    for project in PROJECTS:
        cases.extend([
            TestCase(
                "project_cost",
                f"Quel est le coût total de {random.choice(AMOUNTS)} du projet {project} ?",
                "Quel est le coût total de [MONTANT] du projet [PROJECT] ?",
                "finance",
                True,
            ),
            TestCase(
                "project_tasks",
                f"Quelles tâches ont été réalisées sur le projet {project} ?",
                "Quelles tâches ont été réalisées sur le projet [PROJECT] ?",
                "tache",
                True,
            ),
            TestCase(
                "project_time",
                f"Quel est le total des heures sur le projet {project} ?",
                "Quel est le total des heures sur le projet [PROJECT] ?",
                "heures",
                True,
            ),
        ])

    # ── Clients ────────────────────────────────────────────────────
    for client in CLIENTS:
        cases.extend([
            TestCase(
                "client_consultants",
                f"Quels consultants travaillent chez le client {client} ?",
                "Quels consultants travaillent chez le client [CLIENT] ?",
                None,
                True,
            ),
            TestCase(
                "client_revenue",
                f"Montre les revenus générés pour le client {client}.",
                "Montre les revenus générés pour le client [CLIENT].",
                "finance",
                True,
            ),
            TestCase(
                "client_projects",
                f"Quels projets sont liés au client {client} ?",
                "Quels projets sont liés au client [CLIENT] ?",
                "projet",
                True,
            ),
        ])

    # ── Tâches ─────────────────────────────────────────────────────
    for task in TASKS:
        cases.extend([
            TestCase(
                "task_hours",
                f"Combien d’heures ont été saisies sur la tâche {task} ?",
                "Combien d’heures ont été saisies sur la tâche [TASK] ?",
                "heures",
                True,
            ),
            TestCase(
                "task_employee",
                f"Qui a travaillé sur la tâche {task} ?",
                "Qui a travaillé sur la tâche [TASK] ?",
                "tache",
                True,
            ),
        ])

    # ── Catégories ─────────────────────────────────────────────────
    for category in CATEGORIES:
        cases.append(
            TestCase(
                "category_hours",
                f"Combien d’heures ont été enregistrées dans la catégorie {category} ?",
                "Combien d’heures ont été enregistrées dans la catégorie [CATEGORY] ?",
                "heures",
                True,
            )
        )

    # ── Rôles ──────────────────────────────────────────────────────
    for role in ROLES:
        cases.append(
            TestCase(
                "role_hours",
                f"Quels {role} ont travaillé plus de 40 heures ?",
                "Quels [ROLE] ont travaillé plus de 40 heures ?",
                "heures",
                True,
            )
        )

    # ── Locations ──────────────────────────────────────────────────
    for location in LOCATIONS:
        cases.append(
            TestCase(
                "location_tasks",
                f"Quelles tâches ont été réalisées à {location} ?",
                "Quelles tâches ont été réalisées à [LOCATION] ?",
                "tache",
                True,
            )
        )

    # ── Emails ─────────────────────────────────────────────────────
    for email in EMAILS:
        cases.append(
            TestCase(
                "email_assignment",
                f"Quels projets sont assignés à {email} ?",
                "Quels projets sont assignés à [EMAIL] ?",
                "projet",
                True,
            )
        )

    # ── Matricules / ressources ────────────────────────────────────
    for employee_id in EMPLOYEE_IDS:
        cases.append(
            TestCase(
                "employee_id_hours",
                f"Combien d’heures a travaillé {employee_id} ?",
                "Combien d’heures a travaillé [MATRICULE] ?",
                "heures",
                True,
            )
        )

    for resource_id in RESOURCE_IDS:
        cases.append(
            TestCase(
                "resource_id_projects",
                f"Quels projets sont affectés à la ressource {resource_id} ?",
                "Quels projets sont affectés à la ressource [RESOURCE_ID] ?",
                "projet",
                True,
            )
        )

    # ── Timesheets ─────────────────────────────────────────────────
    for timesheet in TIMESHEETS:
        cases.extend([
            TestCase(
                "timesheet_detail",
                f"Montre-moi le détail de la feuille de temps {timesheet}.",
                "Montre-moi le détail de la feuille de temps [TIMESHEET].",
                "heures",
                True,
            ),
            TestCase(
                "timesheet_status",
                f"Quel est le statut de la timesheet {timesheet} ?",
                "Quel est le statut de la timesheet [TIMESHEET] ?",
                "validation",
                True,
            ),
        ])

    # ── Cas mixtes avancés ─────────────────────────────────────────
    for _ in range(20):
        person = random.choice(PERSONS)
        project = random.choice(PROJECTS)
        client = random.choice(CLIENTS)
        task = random.choice(TASKS)
        amount = random.choice(AMOUNTS)
        timesheet = random.choice(TIMESHEETS)

        cases.extend([
            TestCase(
                "mixed_person_project_client",
                (
                    f"Combien d’heures {person} a-t-il passé sur le projet {project} "
                    f"pour le client {client} ?"
                ),
                (
                    "Combien d’heures [PERSON] a-t-il passé sur le projet [PROJECT] "
                    "pour le client [CLIENT] ?"
                ),
                "heures",
                True,
            ),
            TestCase(
                "mixed_task_timesheet_project",
                (
                    f"Dans la feuille {timesheet}, quelles heures sont liées à la tâche "
                    f"{task} sur le projet {project} ?"
                ),
                (
                    "Dans la feuille [TIMESHEET], quelles heures sont liées à la tâche "
                    "[TASK] sur le projet [PROJECT] ?"
                ),
                "heures",
                True,
            ),
            TestCase(
                "mixed_finance_project_client",
                (
                    f"Quel est le coût total de {amount} du projet {project} "
                    f"pour le client {client} ?"
                ),
                (
                    "Quel est le coût total de [MONTANT] du projet [PROJECT] "
                    "pour le client [CLIENT] ?"
                ),
                "finance",
                True,
            ),
        ])

    # ── Cas non sensibles / faux positifs ──────────────────────────
    cases.extend([
        TestCase(
            "generic_best_project",
            "Quel est le meilleur projet en 2026 ?",
            "Quel est le meilleur projet en 2026 ?",
            "projet",
            False,
        ),
        TestCase(
            "generic_project_time",
            "Quels projets ont pris le plus de temps ?",
            "Quels projets ont pris le plus de temps ?",
            "projet",
            False,
        ),
        TestCase(
            "generic_average_cost",
            "Quel est le coût moyen par projet ?",
            "Quel est le coût moyen par projet ?",
            "finance",
            False,
        ),
        TestCase(
            "conversation_hello",
            "Bonjour, présentez vous.",
            "Bonjour, présentez vous.",
            "conversationnel",
            False,
        ),
        TestCase(
            "conversation_thanks",
            "Merci beaucoup pour votre aide.",
            "Merci beaucoup pour votre aide.",
            "conversationnel",
            False,
        ),
    ])

    return list({case.question: case for case in cases}.values())


def select_round_cases(bank: list[TestCase]) -> list[TestCase]:
    return random.sample(bank, min(QUESTIONS_PER_ROUND, len(bank)))


def evaluate_case(case: TestCase):
    result = sanitize_question(case.question, truncate=False)

    errors: list[str] = []

    if result.preview != case.expected_preview:
        errors.append("preview")

    if case.expected_category is not None and result.category != case.expected_category:
        errors.append("category")

    if case.expected_pii is not None and result.pii_detected != case.expected_pii:
        errors.append("pii_detected")

    return not errors, errors, result


def run_tests() -> None:
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    bank = build_question_bank()

    total_passed = 0
    total_failed = 0

    print("=" * 100)
    print("FDT QUESTION SANITIZER — ADVANCED RANDOM MULTI-ROUND VALIDATION")
    print("=" * 100)
    print(f"Question bank size : {len(bank)}")
    print(f"Rounds             : {ROUNDS}")
    print(f"Questions / round  : {QUESTIONS_PER_ROUND}")
    print("=" * 100)

    for round_idx in range(1, ROUNDS + 1):
        round_cases = select_round_cases(bank)
        round_passed = 0
        round_failed = 0

        print(f"\nROUND {round_idx}/{ROUNDS}")
        print("-" * 100)

        for idx, case in enumerate(round_cases, start=1):
            success, errors, result = evaluate_case(case)

            if success:
                round_passed += 1
                total_passed += 1
                continue

            round_failed += 1
            total_failed += 1

            print(color(f"\n[FAIL] {idx}. {case.name}", RED + BOLD))
            print(color(separator("-", 100), GRAY))

            print(color("QUESTION:", BLUE))
            print(case.question)

            print(color("\nEXPECTED:", GREEN))
            print(case.expected_preview)

            print(color("\nACTUAL:", RED))
            print(result.preview)

            print(color("\nMETADATA:", CYAN))
            print(f"expected_category : {case.expected_category}")
            print(f"actual_category   : {result.category}")
            print(f"expected_pii      : {case.expected_pii}")
            print(f"actual_pii        : {result.pii_detected}")

            print(color("\nERRORS:", YELLOW))
            print(", ".join(errors))

            print(color(separator("-", 100), GRAY))
        round_total = len(round_cases)
        round_accuracy = (round_passed / round_total) * 100 if round_total else 0

        print(
            f"\nRound result: {round_passed}/{round_total} "
            f"({round_accuracy:.2f}%)"
        )

    total = total_passed + total_failed
    global_accuracy = (total_passed / total) * 100 if total else 0

    print("\nFINAL RESULTS")
    print("=" * 100)
    print(f"Total tested : {total}")
    print(f"Passed       : {total_passed}")
    print(f"Failed       : {total_failed}")
    print(f"Accuracy     : {global_accuracy:.2f}%")
    print("=" * 100)


if __name__ == "__main__":
    run_tests()