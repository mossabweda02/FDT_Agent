"""
agent/observability.py
======================
Configuration centralisée de l'observabilité du FDT Agent.

Contient :
  - Configuration Logfire locale
  - Export OpenTelemetry vers Aspire Dashboard
  - Scrubbing des données sensibles
  - Protection des arguments FastAPI
  - Instrumentation Pydantic AI
  - Instrumentation FastAPI
"""

from __future__ import annotations

import os
from typing import Any

import logfire
from fastapi import FastAPI
from logfire import ConsoleOptions, ScrubbingOptions


# ── Configuration OpenTelemetry locale ─────────────────────────────
#   OTLP HTTP : http://localhost:4318/v1/traces
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "http://localhost:4318/v1/traces"
#   UI Web    : http://localhost:18888
os.environ["OTEL_EXPORTER_OTLP_PROTOCOL"] = "http/protobuf"

# ── Patterns sensibles FDT ─────────────────────────────────────────
FDT_SENSITIVE_PATTERNS = [
    # Payload utilisateur / contenu conversationnel
    r"fastapi\.arguments\.values",
    r"(^|[._-])question($|[._-])",
    r"(^|[._-])prompt($|[._-])",
    r"(^|[._-])completion($|[._-])",
    r"(^|[._-])response($|[._-])",

    # Données employés / ressources RH
    r"employee",
    r"employe",
    r"employé",
    r"worker",
    r"personnelnumber",
    r"resourceid",
    r"resourcecompanyid",
    r"resourcerecid",
    r"resourcerolerecid",
    r"workerresponsible",
    r"workerresponsiblefinancial",
    r"workerresponsiblesales",

    # Noms de personnes
    # Matche NAME comme clé isolée, sans masquer PROJNAME ou TASKNAME.
    r"(^|[._-])name($|[._-])",
    r"(^|[._-])firstname($|[._-])",

    # Notes / texte libre potentiellement sensible
    r"internalnote",
    r"externalnote",
    r"description",
    r"referencenumber",

    # Coûts / prix / rentabilité / budgets
    r"cost",
    r"cout",
    r"coût",
    r"saleprice",
    r"totalsaleprice",
    r"standardcost",
    r"totalstandardcost",
    r"realcost",
    r"totalrealcost",
    r"margin",
    r"marge",
    r"profit",
    r"revenue",
    r"budget",
    r"cunsumedbudget",
    r"contractualbudget",

    # Notes de frais / montants
    r"amount",
    r"montant",
    r"expcardamount",
    r"totalamount",
    r"totaltaxeamount",
    r"subtotalamount",
    r"totalpaymentamount",
    r"tipsamount",
    r"paymentexchangerate",
    r"exchangeratecompany",

    # Secrets techniques / connexions
    r"connection_string",
    r"connectionstring",
    r"odbc",
    r"synapse_key",
    r"azure_openai",
    r"api_key",
    r"client_secret",
    r"tenant_id",
    r"token",
    r"secret",
]

# ── Namespaces techniques sûrs ─────────────────────────────────────
SAFE_TELEMETRY_PATH_PARTS = (
     # IA / LLM
    "gen_ai.",

    # Logfire interne
    "logfire.",

    # HTTP / réseau
    "http.",
    "net.",

    # FastAPI : route et timing endpoint uniquement, pas les arguments
    "fastapi.route.",
    "fastapi.endpoint_function.",

    # Ressource OpenTelemetry
    "service.",
    "deployment.",
    "telemetry.",
    "process.",
)

SAFE_TELEMETRY_EXACT_KEYS = {
    "model_name",
    "agent_name",
    "operation.cost",
    "table_name"
}

# ── Scrubbing callback  : intercepter les données sensibles avant de les envoyer à Logfire ────
def fdt_scrub_callback(match: logfire.ScrubMatch):
    """
    Décide quoi faire lorsqu'un attribut matche un pattern sensible.

    return None
        → Logfire masque la valeur.

    return match.value
        → Logfire garde la valeur.
    """
    path_parts = [str(part) for part in (match.path or [])]
    path = ".".join(path_parts).lower()
    key = path_parts[-1].lower() if path_parts else ""

    # 1. Garder les clés techniques exactes observées.
    if key in SAFE_TELEMETRY_EXACT_KEYS:
        return match.value

    # 2. Garder les namespaces techniques sûrs.
    if any(namespace in path for namespace in SAFE_TELEMETRY_PATH_PARTS):
        return match.value

    # 3. Tout le reste qui matche un pattern sensible est masqué.
    return None

# ── Nettoyage des erreurs de validation FastAPI ────────────────────
def _safe_validation_errors(errors: list[Any]) -> list[dict[str, Any]]:
    """
    Convertit les erreurs FastAPI/Pydantic en version non sensible.

    On garde :
      - loc
      - type

    On ne garde pas :
      - input
      - message complet avec contenu utilisateur
      - payload brut
    """
    safe_errors: list[dict[str, Any]] = []

    for error in errors[:10]:
        if not isinstance(error, dict):
            continue

        safe_errors.append(
            {
                "loc": error.get("loc", []),
                "type": error.get("type", "unknown"),
            }
        )

    return safe_errors


# ── Protection des arguments FastAPI ───────────────────────────────
def request_attributes_mapper(
    request: Any,
    attributes: dict[str, Any],
) -> dict[str, Any]:
    """
    Empêche Logfire de stocker fastapi.arguments.values.

    Sans cette fonction, le span /ask peut contenir : fastapi.arguments.values = {"q": {"question": "..."}}

    Or la question utilisateur peut contenir (nom d'employé, projet, période...)
    """
    errors = attributes.get("errors") or []

    if not errors:
        return {}

    return {
        "fastapi.validation_error.count": len(errors),
        "fastapi.validation_error.safe": _safe_validation_errors(errors),
    }


# ── Configuration Logfire ──────────────────────────────────────────
def configure_observability() -> None:
    """
    Configure Logfire et l'export OpenTelemetry local.
    
    Important :
      send_to_logfire=False empêche tout envoi vers Logfire Cloud.
    """
    logfire.configure(
        service_name="fdt-agent",
        service_version="1.1.0",
        environment="local",

        # Empeche l'envoie des données vers Logfire Cloud.
        send_to_logfire=False,

        # Affichage local dans le terminal backend.
        console=ConsoleOptions(
            span_style="show-parents",
            verbose=False,
            show_project_link=False,
        ),

        # Scrubbing des données sensibles.
        scrubbing=ScrubbingOptions(
            extra_patterns=FDT_SENSITIVE_PATTERNS,
            callback=fdt_scrub_callback,
        ),
    )


# ── Instrumentation Pydantic AI ────────────────────────────────────
def instrument_pydantic_ai() -> None:
    """
    Active l'instrumentation Pydantic AI. 
    On garde les spans, durées, tokens, modèle et erreurs.
    """
    logfire.instrument_pydantic_ai(
        include_content=False,
    )


# ── Instrumentation FastAPI ────────────────────────────────────────
def instrument_fastapi_app(app: FastAPI) -> None:
    """
    Active l'instrumentation FastAPI.

    request_attributes_mapper :
      supprime fastapi.arguments.values pour éviter de logger
      la question utilisateur brute.

    excluded_urls :
      évite de polluer les traces avec /health ou /metrics.
    """
    logfire.instrument_fastapi(
        app,
        request_attributes_mapper=request_attributes_mapper,
        excluded_urls=".*/health$,.*/metrics$",
    )