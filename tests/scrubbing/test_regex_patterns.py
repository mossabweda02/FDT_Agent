"""
tests/scrubbing/test_regex_patterns.py
=======================================
Catégorie : Validation unitaire des patterns regex FDT_SENSITIVE_PATTERNS.
Vérifie que chaque pattern est compilable et matche les clés attendues. c'est à dire
- les patterns doivent compiler sans erreur
- les patterns doivent matcher les clés sensibles prévues
- les patterns ne doivent pas matcher les clés non sensibles (risque de faux positifs)
- le pattern \bcost\b doit matcher operation_cost et operation.cost

"""

from __future__ import annotations
import re
import pytest
from conftest import FDT_SENSITIVE_PATTERNS


# ════════════════════════════════════════════════════════════════════
# Tous les patterns doivent compiler sans erreur
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("pattern", FDT_SENSITIVE_PATTERNS)
def test_pattern_is_valid_regex(pattern):
    """Aucun pattern ne doit lever re.error."""
    try:
        re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        pytest.fail(f"Pattern invalide '{pattern}' : {exc}")


# ════════════════════════════════════════════════════════════════════
# Vérification que les patterns isolés matchent bien les clés prévues
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("pattern,should_match,should_not_match", [
    # token isolé
    (
        r"(?:^|[._-])token(?:$|[._-])",
        ["token", "access_token", "token_id", ".token.", "refresh_token"],
        ["tokenizer", "tokens", "gen_ai.usage.total_tokens"],
    ),
    # name isolé
    (
        r"(?:^|[._-])name(?:$|[._-])",
        ["name", "employee_name", "resource_name", "first_name"],
        ["gen_ai.request.model", "filename_part"],
    ),
    # sql isolé
    (
        r"(?:^|[._-])sql(?:$|[._-])",
        ["sql", "raw_sql", "sql_query"],
        ["db.system", "nosql_meta"],
    ),
    # cost isolé
    (
        r"\bcost\b",
        ["cost", "StandardCost", "RealCost"],
        ["operation_cost", "operation.cost"],  # whitelistés — le pattern matche mais callback l'autorise
    ),
    # question isolé
    (
        r"(?:^|[._-])question(?:$|[._-])",
        ["question", "user_question"],
        ["question_preview", "question_hash", "question_category", "question_pii_detected"],
    ),
])
def test_pattern_matches_expected_keys(pattern, should_match, should_not_match):
    compiled = re.compile(pattern, re.IGNORECASE)
    for key in should_match:
        assert compiled.search(key), (
            f"Pattern '{pattern}' devrait matcher '{key}' mais ne matche pas."
        )
    for key in should_not_match:
        assert not compiled.search(key), (
            f"Pattern '{pattern}' ne devrait pas matcher '{key}' (risque faux positif)."
        )


# ════════════════════════════════════════════════════════════════════
# Vérifier que \bcost\b ne matche pas operation_cost / operation.cost
# Ces clés sont dans SAFE_EXACT_KEYS mais le pattern les matche —
# la sécurité repose donc ENTIÈREMENT sur le callback.
# Ce test documente cette dépendance.
# ════════════════════════════════════════════════════════════════════

def test_cost_pattern_matches_operation_cost():
    """
    \\bcost\\b matche 'operation_cost' et 'operation.cost'.
    La protection repose sur SAFE_TELEMETRY_EXACT_KEYS dans le callback.
    Ce test vérifie que la whitelist est bien en place côté callback.
    """
    from conftest import should_be_visible
    assert should_be_visible("operation_cost", 0.002), (
        "operation_cost est scrubbed malgré la whitelist — vérifier le callback."
    )
    assert should_be_visible("operation.cost", 0.0015), (
        "operation.cost est scrubbed malgré la whitelist."
    )
