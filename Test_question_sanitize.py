"""
Tests/test_question_sanitizer_dynamique.py
==========================================

Tests robustes du sanitizer FDT.

Objectifs :
- couvrir les cas RH, finance, projet, client, email, matricule
- éviter la répétition excessive des mêmes questions
- comparer ACTUAL vs EXPECTED
- produire un score de validation crédible

Usage :
    py -m Tests.test_question_sanitizer_dynamique
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from agent.question_sanitizer import sanitize_question


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
]

PROJECTS = [
    "Alpha",
    "Fusion-2026",
    "PRJ-00329",
    "PRJ-00987",
]

CLIENTS = [
    "Airbus Defense",
    "Orange Business",
    "Total Energy",
]

AMOUNTS = [
    "15000 EUR",
    "50 000 €",
    "1 250 000 EUR",
]

EMAILS = [
    "mohamed.benali@company.com",
    "jean.dupont@company.com",
]

EMPLOYEE_IDS = [
    "EMP-458921",
    "RH-00987",
]


# ── Cas déterministes importants ───────────────────────────────────

FIXED_CASES = [
    TestCase(
        name="employee_hours_named_person",
        question="Combien d’heures a travaillé Mohamed Ben Ali en janvier ?",
        expected_preview="Combien d’heures a travaillé [PERSON] en janvier ?",
        expected_category="heures",
        expected_pii=True,
    ),
    TestCase(
        name="salary_named_person",
        question="Quel est le salaire de Jean Dupont ?",
        expected_preview="Quel est le salaire de [PERSON] ?",
        expected_pii=True,
    ),
    TestCase(
        name="absence_named_person",
        question="Pourquoi Ahmed Salah était absent la semaine dernière ?",
        expected_preview="Pourquoi [PERSON] était absent la semaine dernière ?",
        expected_pii=True,
    ),
    TestCase(
        name="project_amount_named_project",
        question="Quel est le coût total de 15000 EUR du projet Alpha ?",
        expected_preview="Quel est le coût total de [MONTANT] du projet [PROJECT] ?",
        expected_category="finance",
        expected_pii=True,
    ),
    TestCase(
        name="project_code_tasks",
        question="Quelles tâches ont été réalisées sur le projet PRJ-00329 ?",
        expected_preview="Quelles tâches ont été réalisées sur le projet [PROJECT] ?",
        expected_category="tache",
        expected_pii=True,
    ),
    TestCase(
        name="consultants_client",
        question="Quels consultants travaillent chez le client Airbus Defense ?",
        expected_preview="Quels consultants travaillent chez le client [CLIENT] ?",
        expected_pii=True,
    ),
    TestCase(
        name="client_revenue",
        question="Montre les revenus générés pour le client Orange Business.",
        expected_preview="Montre les revenus générés pour le client [CLIENT].",
        expected_category="finance",
        expected_pii=True,
    ),
    TestCase(
        name="email_assignment",
        question="Quels projets sont assignés à mohamed.benali@company.com ?",
        expected_preview="Quels projets sont assignés à [EMAIL] ?",
        expected_pii=True,
    ),
    TestCase(
        name="employee_id_hours",
        question="Combien d’heures a travaillé EMP-458921 ?",
        expected_preview="Combien d’heures a travaillé [MATRICULE] ?",
        expected_category="heures",
        expected_pii=True,
    ),
    TestCase(
        name="large_amount_budget",
        question="Quels projets dépassent 1 250 000 € de budget ?",
        expected_preview="Quels projets dépassent [MONTANT] de budget ?",
        expected_category="finance",
        expected_pii=True,
    ),
    TestCase(
        name="no_pii_generic_project",
        question="Quel est le meilleur projet en 2026 ?",
        expected_preview="Quel est le meilleur projet en 2026 ?",
        expected_category="projet",
        expected_pii=False,
    ),
    TestCase(
        name="no_pii_conversation",
        question="Bonjour, présentez vous.",
        expected_preview="Bonjour, présentez vous.",
        expected_category="conversationnel",
        expected_pii=False,
    ),
    TestCase(
        name="long_mixed_sensitive_question",
        question=(
            "Pouvez-vous me montrer le détail complet des heures travaillées par "
            "Mohamed Ben Ali sur le projet PRJ-00329 entre janvier 2025 et mars 2026 "
            "avec les coûts supérieurs à 15 000 EUR et les informations client "
            "Airbus Defense afin d’analyser la rentabilité globale ?"
        ),
        expected_preview=(
            "Pouvez-vous me montrer le détail complet des heures travaillées par "
            "[PERSON] sur le projet [PROJECT] entre janvier 2025 et mars 2026 "
            "avec les coûts supérieurs à [MONTANT] et les informations client "
            "[CLIENT] afin d’analyser la rentabilité globale ?"
        ),
        expected_category="heures",
        expected_pii=True,
    ),
]


# ── Templates dynamiques, max 2 variations chacun ──────────────────

DYNAMIC_TEMPLATES = [
    {
        "name": "dynamic_employee_hours",
        "max_variations": 2,
        "builder": lambda: TestCase(
            name="dynamic_employee_hours",
            question=f"Combien d’heures a travaillé {random.choice(PERSONS)} en janvier ?",
            expected_preview="Combien d’heures a travaillé [PERSON] en janvier ?",
            expected_category="heures",
            expected_pii=True,
        ),
    },
    {
        "name": "dynamic_salary",
        "max_variations": 2,
        "builder": lambda: TestCase(
            name="dynamic_salary",
            question=f"Quel est le salaire de {random.choice(PERSONS)} ?",
            expected_preview="Quel est le salaire de [PERSON] ?",
            expected_pii=True,
        ),
    },
    {
        "name": "dynamic_project_cost",
        "max_variations": 2,
        "builder": lambda: TestCase(
            name="dynamic_project_cost",
            question=f"Quel est le coût total de {random.choice(AMOUNTS)} du projet {random.choice(PROJECTS)} ?",
            expected_preview="Quel est le coût total de [MONTANT] du projet [PROJECT] ?",
            expected_category="finance",
            expected_pii=True,
        ),
    },
    {
        "name": "dynamic_client_consultants",
        "max_variations": 2,
        "builder": lambda: TestCase(
            name="dynamic_client_consultants",
            question=f"Quels consultants travaillent chez le client {random.choice(CLIENTS)} ?",
            expected_preview="Quels consultants travaillent chez le client [CLIENT] ?",
            expected_pii=True,
        ),
    },
    {
        "name": "dynamic_email",
        "max_variations": 2,
        "builder": lambda: TestCase(
            name="dynamic_email",
            question=f"Quels projets sont assignés à {random.choice(EMAILS)} ?",
            expected_preview="Quels projets sont assignés à [EMAIL] ?",
            expected_pii=True,
        ),
    },
    {
        "name": "dynamic_employee_id",
        "max_variations": 2,
        "builder": lambda: TestCase(
            name="dynamic_employee_id",
            question=f"Combien d’heures a travaillé {random.choice(EMPLOYEE_IDS)} ?",
            expected_preview="Combien d’heures a travaillé [MATRICULE] ?",
            expected_category="heures",
            expected_pii=True,
        ),
    },
]


def build_dynamic_cases() -> list[TestCase]:
    cases: list[TestCase] = []
    seen_questions: set[str] = set()

    for template in DYNAMIC_TEMPLATES:
        attempts = 0
        added = 0

        while added < template["max_variations"] and attempts < 20:
            attempts += 1
            case = template["builder"]()

            if case.question in seen_questions:
                continue

            seen_questions.add(case.question)
            cases.append(case)
            added += 1

    return cases


def run_tests() -> None:
    cases = FIXED_CASES + build_dynamic_cases()

    passed = 0
    failed = 0

    print("=" * 100)
    print("FDT QUESTION SANITIZER — STRONG VALIDATION SUITE")
    print("=" * 100)

    for idx, case in enumerate(cases, start=1):
        result = sanitize_question(case.question, truncate=False)

        errors: list[str] = []

        if result.preview != case.expected_preview:
            errors.append("preview")

        if case.expected_category is not None and result.category != case.expected_category:
            errors.append("category")

        if case.expected_pii is not None and result.pii_detected != case.expected_pii:
            errors.append("pii_detected")

        success = not errors

        if success:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        print(f"\n[{status}] {idx}. {case.name}")
        print("-" * 100)
        print("QUESTION:")
        print(case.question)

        print("\nEXPECTED:")
        print(case.expected_preview)

        print("\nACTUAL:")
        print(result.preview)

        print("\nMETADATA:")
        print(f"expected_category : {case.expected_category}")
        print(f"actual_category   : {result.category}")
        print(f"expected_pii      : {case.expected_pii}")
        print(f"actual_pii        : {result.pii_detected}")

        if errors:
            print("\nERRORS:")
            print(", ".join(errors))

        print("=" * 100)

    total = len(cases)
    accuracy = (passed / total) * 100 if total else 0

    print("\nFINAL RESULTS")
    print("=" * 100)
    print(f"Total    : {total}")
    print(f"Passed   : {passed}")
    print(f"Failed   : {failed}")
    print(f"Accuracy : {accuracy:.2f}%")
    print("=" * 100)


if __name__ == "__main__":
    run_tests()