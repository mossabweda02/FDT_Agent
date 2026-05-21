"""
tests/scrubbing/test_false_positives.py
========================================
ce script contient des tests pour vérifier que :
- les champs de monitoring
- les champs OTel gen_ai 
- les champs OTel HTTP 
- les colonnes DB safe 
ne sont pas scrubbed par le système de scrubbing car ils sont essentiels pour le monitoring.

"""

import pytest
from conftest import should_be_visible 


# ════════════════════════════════════════════════════════════════════
# Champs de monitoring FDT — whitelistés explicitement
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,value", [
    ("model_name",            "gpt-4.1-nano"),
    ("agent_name",            "fdt-agent"),
    ("table_name",            "timesheet_line"),
    ("operation_cost",        0.002),
    ("operation.cost",        0.0015),
    ("row_count",             25),
    ("question_hash",         "abc123def456"),
    ("question_preview",      "Combien d'heures a travaillé [PERSON] ?"),
    ("question_category",     "heures"),
    ("question_pii_detected", True),
    ("span.kind",             "server"),
    ("span.name",             "POST /ask"),
])
def test_fdt_monitoring_fields_not_scrubbed(key, value):
    assert should_be_visible(key, value), (
        f"FAUX POSITIF MONITORING : '{key}' ne devrait pas être scrubbed."
    )


# ════════════════════════════════════════════════════════════════════
# Champs OTel gen_ai — couverts par namespace gen_ai.
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,value", [
    ("gen_ai.usage.prompt_tokens",      150),
    ("gen_ai.usage.completion_tokens",  90),
    ("gen_ai.usage.total_tokens",       240),
    ("gen_ai.usage.input_tokens",       150),
    ("gen_ai.usage.output_tokens",      90),
    ("gen_ai.request.model",            "gpt-4.1-nano"),
    ("gen_ai.response.model",           "gpt-4.1-nano"),
])
def test_gen_ai_usage_not_scrubbed(key, value):
    assert should_be_visible(key, value), (
        f"FAUX POSITIF gen_ai : '{key}' doit rester visible."
    )


# ════════════════════════════════════════════════════════════════════
# Champs OTel HTTP
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,value", [
    ("http.request.method",      "POST"),
    ("http.response.status_code", 200),
    ("http.route",               "/ask"),
])
def test_http_otel_not_scrubbed(key, value):
    assert should_be_visible(key, value), (
        f"FAUX POSITIF HTTP : '{key}' doit rester visible."
    )


# ════════════════════════════════════════════════════════════════════
# Colonnes DB safe (agrégées, pas de PII)
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,value", [
    # Ces colonnes viennent de all_safe_or_unknown_column_candidates
    ("APPROVALSTATUS",  1),
    ("LINENUM",         3),
    ("QTY",             8.0),
    ("row_count",       42),
    ("db.system",       "mssql"),
    ("db.operation",    "SELECT"),
])
def test_db_safe_columns_not_scrubbed(key, value):
    assert should_be_visible(key, value), (
        f"FAUX POSITIF DB : '{key}' doit rester visible (agrégat ou méta)."
    )
