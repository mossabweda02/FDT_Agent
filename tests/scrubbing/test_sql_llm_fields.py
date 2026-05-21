"""
tests/scrubbing/test_sql_llm_fields.py
=======================================
Catégorie :SQL statements / LLM content (prompt, completion, response)
Couvre : db.statement, db.query, prompt, completion, response, fastapi.arguments.values

"""

import pytest
from conftest import should_be_scrubbed, should_be_visible


@pytest.mark.parametrize("key,value", [
    # SQL
    ("db.statement",  "SELECT * FROM timesheet_line WHERE employee_name = 'X'"),
    ("db_statement",  "SELECT salary FROM ga_resource WHERE PERSONNELNUMBER = 'Y'"),
    ("db.query",      "SELECT TotalSalePrice FROM timesheet_line"),
    ("sql",           "SELECT * FROM ga_resource"),
    # LLM content
    ("prompt",        "Quel est le salaire de Mohamed Ben Ali ?"),
    ("completion",    "Le salaire de Mohamed Ben Ali est 5000 EUR"),
    ("response",      "Sensitive model response content"),
    # FastAPI args
    ("fastapi.arguments.values", '{"question": "Combien de jours ?"}'),
    ("question",      "Combien d'heures a travaillé l'employé 458921 ?"),
])
def test_sql_llm_content_is_scrubbed(key, value):
    assert should_be_scrubbed(key, value), (
        f"FUITE LLM/SQL : '{key}' devrait être scrubbed."
    )


# ════════════════════════════════════════════════════════════════════
# MUST REMAIN VISIBLE — méta SQL safe
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,value", [
    ("db.system",    "mssql"),
    ("db.name",      "fdt_db"),
    ("db.operation", "SELECT"),
    ("table_name",   "timesheet_line"),
    ("row_count",    25),
])
def test_sql_meta_fields_visible(key, value):
    assert should_be_visible(key, value), (
        f"SUR-SCRUBBING : '{key}' méta SQL devrait rester visible."
    )


# ════════════════════════════════════════════════════════════════════
# Question sanitizer fields — MUST remain visible (déjà anonymisés)
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,value", [
    ("question_preview",      "Combien d'heures a travaillé [PERSON] en janvier ?"),
    ("question_hash",         "abc123def456"),
    ("question_category",     "heures"),
    ("question_pii_detected", True),
])
def test_question_sanitizer_fields_visible(key, value):
    """
    Ces champs sont déjà anonymisés par question_sanitizer.
    Le scrubbing NE DOIT PAS les cacher.
    """
    assert should_be_visible(key, value), (
        f"SUR-SCRUBBING : '{key}' est un champ déjà anonymisé — ne doit pas être scrubbed."
    )
