"""
tests/scrubbing/test_hr_fields.py
==================================
Catégorie : RH / Employés / Ressources
Couvre : employee_*, PERSONNELNUMBER, RESOURCEID, WORKER, salary, name fields

"""

import pytest
from conftest import should_be_scrubbed, should_be_visible


# ════════════════════════════════════════════════════════════════════
# MUST SCRUB — champs RH critiques
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,value", [
    # Clés directes
    ("employee_name",        "Mohamed Ben Ali"),
    ("employee_id",          "EMP-458921"),
    ("employee_code",        "EMP-999"),
    ("PERSONNELNUMBER",      "EMP-458921"),
    ("RESOURCEID",           "RES-2936"),
    ("WORKER",               "123456"),
    ("resource_name",        "Mohamed Ben Ali"),
    # Colonnes DB réelles (observability_tool_outputs_anonymized.json)
    ("WORKERRESPONSIBLE",    "ref-worker-1"),
    ("WORKERRESPONSIBLEFINANCIAL", "ref-worker-2"),
    ("WORKERRESPONSIBLESALES",     "ref-worker-3"),
    ("RESOURCECOMPANYID",    "COMP-01"),
    ("EXTERNALRESOURCERECID","12345"),
    ("FirstName",            "Mohamed"),
    ("NAME",                 "Mohamed Ben Ali"),
    ("Name",                 "Dupont"),
])
def test_hr_field_is_scrubbed(key, value):
    assert should_be_scrubbed(key, value), (
        f"FAUX NÉGATIF CRITIQUE : '{key}' devrait être scrubbed mais reste visible."
    )


# ════════════════════════════════════════════════════════════════════
# FAUX NÉGATIF CRITIQUE CONNU — salary
# Ce test doit ÉCHOUER tant que le patch n'est pas appliqué
# Désactivé avec xfail pour tracer le problème sans bloquer la CI
# ════════════════════════════════════════════════════════════════════

@pytest.mark.xfail(
    reason="salary non couvert par FDT_SENSITIVE_PATTERNS — patch requis",
    strict=True,
)
def test_salary_must_be_scrubbed():
    """salary est un faux négatif critique. Doit passer à XPASS après patch."""
    assert should_be_scrubbed("salary", 5000), (
        "CRITIQUE : 'salary' reste visible. Ajouter \\bsalary\\b aux patterns."
    )


@pytest.mark.xfail(reason="salaire non couvert — patch requis", strict=True)
def test_salaire_must_be_scrubbed():
    assert should_be_scrubbed("salaire", 4500)


@pytest.mark.xfail(reason="payroll non couvert — patch requis", strict=True)
def test_payroll_must_be_scrubbed():
    assert should_be_scrubbed("payroll", 12000)


# ════════════════════════════════════════════════════════════════════
# MUST REMAIN VISIBLE — champs RH sûrs
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,value", [
    ("row_count",         25),
    ("table_name",        "ga_resource"),
    ("agent_name",        "fdt-agent"),
    ("model_name",        "gpt-4.1-nano"),
    ("operation_cost",    0.002),
])
def test_hr_safe_fields_visible(key, value):
    assert should_be_visible(key, value), (
        f"SUR-SCRUBBING : '{key}' devrait rester visible mais est scrubbed."
    )
