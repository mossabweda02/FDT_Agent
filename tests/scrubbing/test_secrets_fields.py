"""
tests/scrubbing/test_secrets_fields.py
=======================================
Catégorie : Secrets techniques / Connexions / Tokens 
Couvre : connection_string, api_key, client_secret, token, synapse_key, tenant_id,
         et les patterns génériques \bsecret\b

"""

import pytest
from conftest import should_be_scrubbed, should_be_visible


@pytest.mark.parametrize("key,value", [
    ("connection_string", "Driver={ODBC};Server=synapse;Pwd=secret"),
    ("connectionstring",  "DSN=FDT;UID=user;PWD=password"),
    ("odbc",              "DSN=FDT;UID=user;PWD=password"),
    ("api_key",           "sk-secret-test"),
    ("client_secret",     "client-secret-value"),
    ("token",             "secret-token-value"),
    ("synapse_key",       "synapse-secret-key"),
    ("azure_openai",      "https://xxx.openai.azure.com"),
    ("tenant_id",         "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"),
    # Patterns \bsecret\b
    ("my_secret",         "hunter2"),
    ("secret_key",        "abc123"),
])
def test_secrets_are_scrubbed(key, value):
    assert should_be_scrubbed(key, value), (
        f"FUITE CRITIQUE : '{key}' devrait être scrubbed."
    )


# ════════════════════════════════════════════════════════════════════
# FAUX POSITIF CONNU — scrubbing_group
# Scrubbed quand sa valeur contient "secret" ou "sql_"
# Le faux positif vient de la valeur, pas de la clé
# Test documentaire : la clé elle-même ne devrait pas être scrubbed
# ════════════════════════════════════════════════════════════════════

@pytest.mark.xfail(
    reason="scrubbing_group scrubbed car valeur='secrets' matche \\bsecret\\b — "
           "ajouter scrubbing_group aux SAFE_TELEMETRY_EXACT_KEYS",
    strict=True,
)
def test_scrubbing_group_not_scrubbed_when_value_contains_secret():
    """
    La clé 'scrubbing_group' avec valeur 'secrets' est scrubbed par erreur.
    Après patch (ajout dans SAFE_EXACT_KEYS), ce test doit passer à XPASS.
    """
    assert should_be_visible("scrubbing_group", "secrets"), (
        "FAUX POSITIF : scrubbing_group='secrets' est scrubbed — clé de monitoring."
    )


@pytest.mark.xfail(
    reason="scrubbing_group scrubbed car valeur='sql_llm' matche pattern sql",
    strict=True,
)
def test_scrubbing_group_not_scrubbed_when_value_is_sql_llm():
    assert should_be_visible("scrubbing_group", "sql_llm")
