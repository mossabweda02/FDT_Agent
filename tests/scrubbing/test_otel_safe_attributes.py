"""
tests/scrubbing/test_otel_safe_attributes.py
=============================================

Catégorie : Attributs OTel techniques — doivent rester visibles pour le monitoring et le debugging
Couvre : gen_ai.*, http.*, db.meta, service.*, deployment.*

"""

import pytest
from conftest import should_be_visible, should_be_scrubbed


# ════════════════════════════════════════════════════════════════════
# MUST REMAIN VISIBLE — attributs OTel standard
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,value", [
    # gen_ai
    ("gen_ai.request.model",        "gpt-4.1-nano"),
    ("gen_ai.usage.input_tokens",   120),
    ("gen_ai.usage.output_tokens",  80),
    ("gen_ai.usage.total_tokens",   200),
    ("gen_ai.response.model",       "gpt-4.1-nano"),
    # HTTP
    ("http.request.method",         "GET"),
    ("http.response.status_code",   200),
    ("http.route",                  "/ask"),
    # DB méta
    ("db.system",    "mssql"),
    ("db.operation", "SELECT"),
    # Errors
    ("error.type",     "TimeoutError"),
    ("exception.type", "ValueError"),
    # Agent FDT
    ("model_name",     "gpt-4.1-nano"),
    ("agent_name",     "fdt-agent"),
    ("operation_cost", 0.002),
    ("row_count",      25),
])
def test_otel_attributes_visible(key, value):
    assert should_be_visible(key, value), (
        f"SUR-SCRUBBING OTEL : '{key}' doit rester visible pour le monitoring."
    )


# ════════════════════════════════════════════════════════════════════
# FAUX POSITIF CONNU — service.name
# ════════════════════════════════════════════════════════════════════

@pytest.mark.xfail(
    reason="service.name scrubbed car 'name' matche le pattern (?:^|[._-])name(?:$|[._-]) "
           "— ajouter 'service.name' dans SAFE_TELEMETRY_EXACT_KEYS ou vérifier "
           "que le namespace 'service.' est bien prioritaire dans le callback",
    strict=True,
)
def test_service_name_not_scrubbed():
    """
    service.name est scrubbed par erreur (pattern `name`).
    SAFE_TELEMETRY_PATH_PARTS contient 'service.' mais le callback
    doit vérifier le path complet, pas seulement la dernière clé.
    Doit passer à XPASS après correction du callback ou ajout dans SAFE_EXACT_KEYS.
    """
    assert should_be_visible("service.name", "fdt-agent"), (
        "FAUX POSITIF : service.name scrubbed — perte de métadonnée OTel critique."
    )


@pytest.mark.parametrize("key,value", [
    ("service.version",     "1.2.0"),
    ("deployment.environment.name", "local"),
    ("telemetry.sdk.name",  "opentelemetry"),
    ("process.runtime.name", "cpython"),
])
def test_service_namespace_attributes_visible(key, value):
    """
    Ces clés appartiennent aux namespaces sûrs (service., deployment., telemetry., process.)
    Le callback doit les laisser passer via SAFE_TELEMETRY_PATH_PARTS.
    """
    assert should_be_visible(key, value), (
        f"SUR-SCRUBBING : '{key}' appartient à un namespace safe."
    )
