"""
Module: tools.functions_tool
=====================================
Implémentation des 6 outils SQL exposés à l'agent.

Ce module contient la logique réelle de chacun des 6 outils SQL:
  1. list_tables()              - Liste toutes les vues Synapse
  2. get_database_schema()      - Schéma simplifié des tables principales
  3. get_table_relationships()  - Clés de jointure et requête canonique
  4. describe_table(table_name) - Colonnes exactes, types, nullabilité
  5. get_sample_data(table_name)- 5 lignes d'exemple pour inférer format
  6. execute_query(query)       - Exécution SELECT avec validation

Les outils retournent du JSON string (pas de dict) car le LLM Azure n'interprète
que les strings JSON, pas les types Python.

Filtrage des colonnes:
  - META_COLS: Colonnes pipeline (metadata) filtrées de tous les résultats
"""

import json
import logging
import os

import pandas as pd

from backend.database.connection import get_engine
from backend.tools.sql_validator import validate_sql_query, sanitize_query_for_logging

logger = logging.getLogger(__name__)

META_COLS = {
    "_run_id", "_source_table", "_load_mode",
    "Deleted", "Deleted_At", "_ingested_at"
}
def _ok(data: dict) -> str:
    """Sérialise une réponse de succès au format JSON (plus lisible pour le LLM)."""
    return json.dumps(data, ensure_ascii=False, default=str)


def _err(msg: str, hint: str = "") -> str:
    """ Sérialise une réponse d'erreur en JSON string """
    return json.dumps({"error": msg, "hint": hint,
                       "rows": [], "row_count": 0}, ensure_ascii=False)

def _read(sql: str) -> pd.DataFrame:
    """Exécute un SELECT via connexion explicite et retourne un DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Retire les colonnes metadata pipeline."""
    return df[[c for c in df.columns if c not in META_COLS]]


# ── Outil 1 ───────────────────────────────────────────────────────
def list_tables() -> str:
    try:
        df = _read("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                   "ORDER BY TABLE_NAME")
        tables = df["TABLE_NAME"].tolist()
        return _ok({"tables": tables, "count": len(tables)})
    except Exception as e:
        return _err(str(e), "Vérifier la connexion à la base.")


# ── Outil 2 ───────────────────────────────────────────────────────
def describe_table(table_name: str) -> str:
    try:
        df = _read(
            f"SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE "
            f"FROM INFORMATION_SCHEMA.COLUMNS "
            f"WHERE TABLE_NAME = '{table_name}' "
            f"ORDER BY ORDINAL_POSITION"
        )
        if df.empty:
            return _err(f"Vue '{table_name}' introuvable.",
                        "Appeler list_tables() pour voir les vues disponibles.")
        cols = [{"name": r.COLUMN_NAME, "type": r.DATA_TYPE,
                 "nullable": r.IS_NULLABLE}
                for _, r in df.iterrows()]
        return _ok({"table": table_name, "columns": cols,
                    "column_count": len(cols)})
    except Exception as e:
        return _err(str(e))


# ── Outil 3 ───────────────────────────────────────────────────────
def get_sample_data(table_name: str) -> str:
    try:
        df = _clean(_read(f"SELECT TOP 5 * FROM {table_name}"))
        if df.empty:
            return _ok({"table": table_name, "rows": [], "row_count": 0})
        rows = json.loads(df.to_json(orient="records",
                                     date_format="iso", default_handler=str))
        return _ok({"table": table_name, "rows": rows, "row_count": len(rows)})
    except Exception as e:
        return _err(str(e),
                    f"Vérifier que '{table_name}' existe avec list_tables().")

# ── Outil 4 ───────────────────────────────────────────────────────
def get_table_relationships() -> str:
    data = {
        "joins": [
            {"from": "timesheet_header.TIMESHEETNBR",
             "to":   "timesheet_line.TIMESHEETNBR",
             "example": "JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR"},
            {"from": "timesheet_header.RESOURCE",
             "to":   "ga_resource.RECID",
             "example": "JOIN ga_resource r ON r.RECID = h.RESOURCE"},
            {"from": "timesheet_line.RESOURCE",
             "to":   "ga_resource.RECID",
             "example": "JOIN ga_resource r ON r.RECID = l.RESOURCE"},
            {"from": "timesheet_line.PROJID",
             "to":   "prj_proj_table.PROJID",
             "example": "JOIN prj_proj_table p ON p.PROJID = l.PROJID"},
            {"from": "timesheet_line.ACTIVITYNUMBER",
             "to":   "ga_task.ACTIVITYNUMBER",
             "example": "JOIN ga_task t ON t.ACTIVITYNUMBER = l.ACTIVITYNUMBER"},
            {"from": "acp_expense_card.ResourceRecId",
             "to":   "ga_resource.RECID",
             "example": "JOIN ga_resource r ON r.RECID = e.ResourceRecId"},
        ],
        "warning": (
            "Si timesheet_header n'est PAS dans le FROM, "
            "ne pas utiliser l'alias h — erreur 'could not be bound'."
        ),
        "canonical_query": (
            "SELECT r.NAME AS Employe, p.PROJNAME AS Projet, "
            "t.TASKNAME AS Tache, l.CATEGORYID, SUM(l.QTY) AS TotalHeures\n"
            "FROM timesheet_header h\n"
            "JOIN timesheet_line l  ON h.TIMESHEETNBR = l.TIMESHEETNBR\n"
            "JOIN ga_resource r     ON r.RECID = h.RESOURCE\n"
            "JOIN prj_proj_table p  ON p.PROJID = l.PROJID\n"
            "JOIN ga_task t         ON t.ACTIVITYNUMBER = l.ACTIVITYNUMBER\n"
            "WHERE MONTH(h.PERIODFROM) = {N} AND YEAR(h.PERIODFROM) = {YYYY}\n"
            "GROUP BY r.NAME, p.PROJNAME, t.TASKNAME, l.CATEGORYID\n"
            "ORDER BY TotalHeures DESC"
        ),
    }
    return _ok(data)


# ── Outil 5 ───────────────────────────────────────────────────────
def get_database_schema() -> str:
    schema = {
        "description": "Schéma simplifié — tables principales FDT",
        "tables": {
            "timesheet_header": {
                "role": "En-têtes feuilles de temps",
                "key_columns": ["TIMESHEETNBR", "RESOURCE", "PERIODFROM",
                                 "PERIODTO", "APPROVALSTATUS"],
                "join_to": ["timesheet_line via TIMESHEETNBR",
                            "ga_resource via RESOURCE=RECID"],
            },
            "timesheet_line": {
                "role": "Lignes détail — heures saisies",
                "key_columns": ["TIMESHEETNBR", "PROJID", "ACTIVITYNUMBER",
                                 "QTY", "CATEGORYID", "Date",
                                 "TotalSalePrice", "TotalStandardCost"],
                "join_to": ["timesheet_header via TIMESHEETNBR",
                            "prj_proj_table via PROJID",
                            "ga_task via ACTIVITYNUMBER",
                            "ga_resource via RESOURCE=RECID"],
            },
            "ga_resource": {
                "role": "Référentiel employés",
                "key_columns": ["RECID", "NAME", "ACTIVE"],
                "join_to": ["timesheet_header via RECID=RESOURCE",
                            "timesheet_line via RECID=RESOURCE"],
            },
            "prj_proj_table": {
                "role": "Référentiel projets",
                "key_columns": ["PROJID", "PROJNAME", "STATUS", "PROGRESSION"],
                "join_to": ["timesheet_line via PROJID"],
            },
            "ga_task": {
                "role": "Référentiel tâches",
                "key_columns": ["ACTIVITYNUMBER", "TASKNAME", "TASKCATEGORY",
                                 "WORKEDHOURES"],
                "join_to": ["timesheet_line via ACTIVITYNUMBER"],
            },
            "acp_expense_card": {
                "role": "Notes de frais",
                "key_columns": ["ResourceRecId", "ProjectRecID", "Date",
                                 "TotalAmountCompanyCur", "Billable"],
                "join_to": ["ga_resource via ResourceRecId=RECID"],
            },
        },
        "approvalstatus_warning": (
            "Ne JAMAIS filtrer par APPROVALSTATUS par défaut. "
            "Valeurs: 1=Draft 2=Submitted 3=Approved 4=Returned 9=Pending"
        ),
        "meta_cols_to_exclude": list(META_COLS),
    }
    return _ok(schema)


# ── Outil 6 ───────────────────────────────────────────────────────
def execute_query(query: str) -> str:
    """
    Retourne TOUJOURS un JSON string (jamais un dict).
    Le LLM ne peut pas lire un dict Python — il a besoin d'une string JSON.
    """
    if not query or not query.strip():
        return _err("Requête vide.", "Fournir une requête SQL SELECT complète.")

    is_valid, error = validate_sql_query(query)
    if not is_valid:
        logger.error(f"SQL blocked: {sanitize_query_for_logging(query)}")
        return _err(error, "Corriger la requête et réessayer.")

    try:
        logger.info(f"SQL: {sanitize_query_for_logging(query, 300)}")
        df = _clean(_read(query))

        if df.empty:
            return _ok({
                "rows": [], "row_count": 0,
                "hint": (
                    "0 résultats. Si APPROVALSTATUS est dans le WHERE, "
                    "réessayer SANS ce filtre."
                ),
            })

        rows = json.loads(
            df.to_json(orient="records", date_format="iso", default_handler=str)
        )
        logger.info(f"OK: {len(rows)} rows")
        return _ok({"rows": rows, "row_count": len(rows),
                    "columns": list(df.columns)})

    except Exception as e:
        msg = str(e)
        logger.error(f"SQL error: {msg}")

        if "Invalid column name" in msg:
            hint = "Vérifier colonnes avec describe_table()."
        elif "Invalid object name" in msg:
            hint = "Vérifier table avec list_tables()."
        elif "LIMIT" in query.upper() and "syntax" in msg.lower():
            hint = "Remplacer LIMIT N par TOP N (T-SQL)."
        elif "could not be bound" in msg:
            hint = ("Alias invalide — vérifier que toutes les tables du FROM "
                    "correspondent aux alias utilisés dans le WHERE.")
        elif "Conversion failed" in msg:
            hint = "Type incorrect. Utiliser get_sample_data() pour voir les vraies valeurs."
        else:
            hint = "Vérifier la requête et réessayer."

        return _err(msg, hint)

# ── Outil 7 : Diagnostic sécurisé authentification Hub ────────────────────────────────

def get_auth_runtime_status() -> str:
    """
    Retourne un diagnostic sécurisé du mode d'authentification Hub.

    Ne retourne jamais :
      - token
      - client secret
      - tenant complet sensible
      - valeur brute des variables d'environnement
    """
    has_static_token = bool(os.environ.get("HUB_BEARER_TOKEN"))
    has_hub_scope = bool(os.environ.get("HUB_SCOPE"))
    has_user_auth = False  # Sera activé plus tard avec Entra ID frontend.

    if has_static_token:
        auth_mode = "test_bearer_token"
        message = (
            "Le backend utilise actuellement un token Bearer temporaire pour les tests "
            "Integration Hub. L'authentification utilisateur Entra ID n'est pas encore activée."
        )
    else:
        auth_mode = "default_azure_credential"
        message = (
            "Le backend tente d'obtenir un token via DefaultAzureCredential. "
            "En local, cela nécessite généralement une session Azure CLI valide."
        )

    return json.dumps(
        {
            "ok": True,
            "auth_mode": auth_mode,
            "user_auth_enabled": has_user_auth,
            "hub_scope_configured": has_hub_scope,
            "hub_user_filtering_expected": True,
            "safe_message": message,
            "security_note": (
                "Les tokens, secrets et valeurs sensibles ne sont jamais exposés. "
                "Après l'authentification Entra ID, le token utilisateur devra être propagé "
                "vers Integration Hub pour appliquer le filtrage par utilisateur connecté."
            ),
        },
        ensure_ascii=False,
        default=str,
    )

# ── Mapping ───────────────────────────────────────────────────────
TOOL_FUNCTIONS = {
    "list_tables":             list_tables,
    "describe_table":          describe_table,
    "get_sample_data":         get_sample_data,
    "get_table_relationships": get_table_relationships,
    "get_database_schema":     get_database_schema,
    "execute_query":           execute_query,
    "get_auth_runtime_status": get_auth_runtime_status,
}