"""
Module: backend.agent.scrubbing.observability
==============================================
Configuration centralisée de l'observabilité du FDT Agent.

Ce module configure:
  - Logfire locale (sans envoi cloud, console stdout)
  - Export OpenTelemetry vers Aspire Dashboard (http://localhost:18888)
  - Scrubbing des données sensibles (3 couches de défense)
  - Protection des arguments FastAPI
  - Instrumentation Pydantic AI (sans contenu)
  - Instrumentation FastAPI (avec masquage des questions)

Défense en profondeur (3 couches):
  1. Patterns sensibles (clés d'attributs OTel)
  2. Callback fdt_scrub_callback (allowlist safe paths)
  3. request_attributes_mapper (suppression des arguments)

Données masquées:
  - Questions utilisateur (fastapi.arguments.values)
  - Prompts système et complétions
  - Noms, prénoms, adresses
  - Salaires, coûts, rentabilité
  - Secrets techniques (clés, tokens)

Données conservées:
  - Métriques (durées, tokens, count)
  - Métadonnées techniques (model, service, version)
  - Erreurs et avertissements (sans contexte sensible)
"""

from __future__ import annotations

import os
import logging
from typing import Any

import logfire
from fastapi import FastAPI
from logfire import ConsoleOptions, ScrubbingOptions


# ── Configuration OpenTelemetry locale ─────────────────────────────
#   OTLP HTTP : http://localhost:4318/v1/traces
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "http://localhost:4318/v1/traces"
#   UI Web    : http://localhost:18888
os.environ["OTEL_EXPORTER_OTLP_PROTOCOL"] = "http/protobuf"


# ════════════════════════════════════════════════════════════════════
# PATTERNS SENSIBLES FDT
# ════════════════════════════════════════════════════════════════════
#
#   La défense en profondeur repose sur TROIS couches :
#     1. Ces patterns (clés d'attributs OTel sensibles)
#     2. Le callback fdt_scrub_callback (allowlists safe paths : nous permettent de ne pas cacher les variables qu'on veut)
#     3. request_attributes_mapper (suppression suppression des arguments de la fonction ask_route 
#        qui contient la question de l'utilisateur et il va le cacher)
#
# ════════════════════════════════════════════════════════════════════

FDT_SENSITIVE_PATTERNS = [

    # ── Payload utilisateur / contenu conversationnel ──────────────
    
    r"fastapi\.arguments\.values", # cache les arguments de la fonction ask_route 
    r"(?:^|[._-])question(?:$|[._-])", # cache la question de l'utilisateur
    r"(?:^|[._-])prompt(?:$|[._-])", # cache le prompt de l'utilisateur
    r"(?:^|[._-])completion(?:$|[._-])", # cache la completion de l'utilisateur
    r"(?:^|[._-])response(?:$|[._-])", # cache la réponse de l'agent

    # ── Données employés / ressources RH ──────────────────────────
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
    r"\bsalary\b",
    r"\bsalaire\b",
    r"\bpayroll\b",

    # ── Noms de personnes ──────────────────────────────────────────
    r"(?:^|[._-])name(?:$|[._-])",
    r"(?:^|[._-])firstname(?:$|[._-])",
    r"(?:^|[._-])lastname(?:$|[._-])",

    # ── Notes / texte libre potentiellement sensible ───────────────
    r"\bdescription\b",
    r"internalnote",
    r"externalnote",
    r"referencenumber",

    # ── Coûts / prix / rentabilité / budgets ──────────────────────
    r"\bcost\b",
    r"\bcout\b",
    r"\bcoût\b",
    r"saleprice",
    r"totalsaleprice",
    r"standardcost",
    r"totalstandardcost",
    r"realcost",
    r"totalrealcost",
    r"\bmargin\b",
    r"\bmarge\b",
    r"\bprofit\b",
    r"\brevenue\b",
    r"\bbudget\b",
    r"consumedbudget",       
    r"cunsumedbudget",       #
    r"contractualbudget",

    # ── Notes de frais / montants ──────────────────────────────────
    r"\bamount\b",
    r"\bmontant\b",
    r"expcardamount",
    r"totalamount",
    r"totaltaxeamount",
    r"subtotalamount",
    r"totalpaymentamount",
    r"tipsamount",
    r"paymentexchangerate",
    r"exchangeratecompany",

    # ── Secrets techniques / connexions ───────────────────────────
    r"connection_string",
    r"connectionstring",
    r"odbc",
    r"synapse_key",
    r"azure_openai",
    r"api_key",
    r"client_secret",
    r"tenant_id",
    r"(?:^|[._-])token(?:$|[._-])",  # Clé `token` isolée seulement
    r"\bsecret\b",

    # ── SQL statements  ────────────────────────────────
    r"(?:^|[._-])sql(?:$|[._-])",
    r"db\.statement",
    r"db\.query",
]


# ════════════════════════════════════════════════════════════════════
# ALLOWLISTS — NAMESPACES TECHNIQUES SÛRS
# ════════════════════════════════════════════════════════════════════

SAFE_TELEMETRY_PATH_PARTS = (
    # ── IA / LLM ─────────────────────────────────────────────────
    "gen_ai.", # Autorise tout sauf ce qui est bloqué par instrument_pydantic_ai (gen_ai.request.messages et gen_ai.response.text)

    # ── Logfire interne ────────────────────────────────────────────
    "logfire.", # Autorise tout sauf ce qui est bloqué par instrument_pydantic_ai (logfire.request.messages et logfire.response.text)

    # ── HTTP / réseau ──────────────────────────────────────────────
    "http.", # http.url / http.method / http.request.body / http.response.body
    "net.", # net.peer.* / net.type 

    # ── FastAPI : route et timing uniquement ───────────────────────
    "fastapi.route.", # fastapi.route.path → "/ask" (pas les params)
    "fastapi.endpoint_function.",     # fastapi.endpoint_function.name → nom de la fonction handler

    # ── Ressource OpenTelemetry standard ──────────────────────────
    "service.", 
    "deployment.",
    "telemetry.",
    "process.",

    # ── Erreurs OTel standard ─────────────────────────
    "error.type", # → "ValueError", "TimeoutError" etc. → utile debugging
    "exception.type", # → nom de l'exception classe

    # ── Base de données méta-only ─────────────────────
    "db.system", # → "mssql", "postgresql" → safe
    "db.name",   # → nom de la base (pas sensible, utile au routing)
    "db.operation", # → "SELECT", "INSERT" → safe
)


# ════════════════════════════════════════════════════════════════════
# ALLOWLIST — CLÉS EXACTES TOUJOURS CONSERVÉES
# ════════════════════════════════════════════════════════════════════
#
# Ces clés sont des attributs custom FDT ou des clés OTel exactes
# qui matchent des patterns sensibles mais dont la valeur est sûre
#
# ════════════════════════════════════════════════════════════════════

SAFE_TELEMETRY_EXACT_KEYS = {
    # ── Méta agent FDT ────────────────────────────────────────────
    "model_name",
    "agent_name",
    "table_name",

    # ── Coût opération ────────────────────────────────────────────
    # `operation.cost` matche le pattern `\bcost\b` → whitelisté explicitement.
    "operation.cost",
    "operation_cost",
    "row_count",

    # ── Question sanitization fields ──────────────────────────────
    # Ces champs contiennent des données déjà anonymisées par question_sanitizer.
    # La valeur loguée est le preview, jamais la question brute.
    "question_hash",
    "question_preview",
    "question_category",
    "question_pii_detected",

    # ── gen_ai usage ──────────────────────────────────
    "gen_ai.usage.prompt_tokens", #  →  nombre de tokens dans le prompt
    "gen_ai.usage.completion_tokens", #  →  nombre de tokens dans la réponse
    "gen_ai.usage.total_tokens", #  →  nombre total de tokens
    "gen_ai.usage.input_tokens", #  →  nombre de tokens d'entrée
    "gen_ai.usage.output_tokens", #  →  nombre de tokens de sortie
    "gen_ai.response.model", #  →  nom du modèle utilisé
    "gen_ai.request.model", #  →  nom du modèle utilisé ( pas sensible)

    # ── HTTP métriques ────────────────────────────────
    "http.response.status_code", # code de reponse http 
    "http.request.method", # methode http 
    "http.route", # route http 

    # ── OTel méta ────────────────────────────────────
    "span.kind", # type de span (requette http ou autre)  →  ex: server,client 
    "span.name", # nom de la requette http ou autre  → ex : "POST /ask"  ou  "GET /"
    "service.name", # nom du service (fdt-agent)
    "scrubbing_group", # groupe de scrubbing qui a matché (utile pour debug)
    "service.version", # version du service (fdt-agent v1.2.0)
    "deployment.environment.name",  # environnement de déploiement (local, staging, prod)
}

# transformer les cles et les namespaces en minuscules pour faciliter la comparaison
SAFE_TELEMETRY_EXACT_KEYS_LOWER = {
    key.lower() for key in SAFE_TELEMETRY_EXACT_KEYS
}

SAFE_TELEMETRY_PATH_PARTS_LOWER = tuple(
    part.lower() for part in SAFE_TELEMETRY_PATH_PARTS
)

# ════════════════════════════════════════════════════════════════════
# SCRUBBING CALLBACK
# ════════════════════════════════════════════════════════════════════

def fdt_scrub_callback(match: logfire.ScrubMatch) -> Any:
    """
    Masque les attributs OTel sensibles sauf ceux explicitement safe.
    """
    path_parts = [str(part) for part in (match.path or [])]
    path = ".".join(path_parts).lower()
    key = path_parts[-1].lower() if path_parts else ""

    # 1. Mots clés exacts non sensibles 
    if key in SAFE_TELEMETRY_EXACT_KEYS_LOWER:
        return match.value

    # 2. Chemins de namespaces sûrs 
    if path in SAFE_TELEMETRY_EXACT_KEYS_LOWER:
        return match.value

    if any(path.startswith(namespace) for namespace in SAFE_TELEMETRY_PATH_PARTS_LOWER):
        return match.value

    # Debbuggage de scrubbing (à utiliser dans la phase de dev)
    logging.getLogger("fdt.scrubbing").debug(
        "SCRUBBED | key=%s | path=%s | pattern=%s",
        key, path, match.pattern_match.group(0) if match.pattern_match else "?"
    )
    return None


# ════════════════════════════════════════════════════════════════════
# NETTOYAGE DES ERREURS DE VALIDATION FASTAPI
# ════════════════════════════════════════════════════════════════════

def _safe_validation_errors(errors: list[Any]) -> list[dict[str, Any]]:
    """
    Convertit les erreurs FastAPI/Pydantic en version non sensible.

    Conservé :
      - loc  → localisation du champ invalide (ex: ["body", "question"])
      - type → type d'erreur Pydantic (ex: "string_too_short")

    Supprimé :
      - input   → contient la valeur soumise par l'utilisateur
      - msg     → peut contenir des extraits de la valeur invalide
      - url     → lien vers doc Pydantic 
      - ctx     → contexte avec valeurs limites 
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


# ════════════════════════════════════════════════════════════════════
# PROTECTION DES ARGUMENTS FASTAPI
# ════════════════════════════════════════════════════════════════════

def request_attributes_mapper(
    request: Any,
    attributes: dict[str, Any],
) -> dict[str, Any]:
    """
    Supprime les arguments FastAPI sensibles des traces Logfire.

    Comportement :
      - Si pas d'erreurs : retourne {} (aucun attribut du request logué).
      - Si erreurs de validation : retourne uniquement les méta-erreurs safe.
    """
    errors = attributes.get("errors") or []

    if not errors:
        return {}

    return {
        "fastapi.validation_error.count": len(errors),
        "fastapi.validation_error.safe": _safe_validation_errors(errors),
    }


# ════════════════════════════════════════════════════════════════════
# CONFIGURATION LOGFIRE
# ════════════════════════════════════════════════════════════════════

def configure_observability() -> None:
    """
    Configure Logfire avec export OTel local uniquement.
    """
    logfire.configure(
        service_name="fdt-agent",
        service_version="1.2.0",
        environment="local",

        # Isolation cloud absolue.
        send_to_logfire=False,

        
        console=ConsoleOptions(
            # Affiche les traces des spans dans l'ordre chronologique inverse.
            span_style="show-parents",
            # Affiche les logs de manière concise.
            verbose=False,
            # Empêche l'affichage du lien vers le projet Logfire.
            show_project_link=False,
        ),

        # Scrubbing des données sensibles.
        scrubbing=ScrubbingOptions(
            extra_patterns=FDT_SENSITIVE_PATTERNS,
            callback=fdt_scrub_callback,
        ),
    )


# ════════════════════════════════════════════════════════════════════
# INSTRUMENTATION PYDANTIC AI
# ════════════════════════════════════════════════════════════════════

def instrument_pydantic_ai() -> None:
    """
  Cette fonction Active l'instrumentation Pydantic AI.
  Permet de ne pas logger les données sensibles des requêtes et des réponses.
    """
    logfire.instrument_pydantic_ai(
        include_content=False,
    )


# ════════════════════════════════════════════════════════════════════
# INSTRUMENTATION FASTAPI
# ════════════════════════════════════════════════════════════════════

def instrument_fastapi_app(app: FastAPI) -> None:
    """
    Cette fonction Active l'instrumentation FastAPI.
    Permet de logger les requêtes et les réponses HTTP.
    """
    logfire.instrument_fastapi(
        app,
        # Mapper les attributs des requêtes et des réponses.
        request_attributes_mapper=request_attributes_mapper,
        # Eviter le bruit dans les traces HTTP.
        excluded_urls=".*/health$,.*/metrics$",
    )

