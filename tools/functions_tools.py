"""
fdtAgent/tools/functions_tools.py
==================================
Les 5 function tools SQL avec logs et gestion d'erreurs améliorée.
"""

import pandas as pd
from database.connection import get_engine


def list_tables() -> str:
    """Liste toutes les vues de la Silver Layer."""
    try:
        df = pd.read_sql(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_NAME",
            get_engine()
        )
        if df.empty:
            return "Aucune vue trouvée."
        return "\n".join(df["TABLE_NAME"].tolist())
    except Exception as e:
        return f"Erreur list_tables : {e}"


def describe_table(table_name: str) -> str:
    """
    Retourne les colonnes EXACTES et types d'une vue.
    Toujours appeler avant execute_query.
    """
    try:
        df = pd.read_sql(
            "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME = %(t)s ORDER BY ORDINAL_POSITION",
            get_engine(), params={"t": table_name}
        )
        if df.empty:
            return f"Vue '{table_name}' introuvable. Vérifie le nom avec list_tables()."
        return "\n".join(
            f"{r.COLUMN_NAME} ({r.DATA_TYPE})" for _, r in df.iterrows()
        )
    except Exception as e:
        return f"Erreur describe_table : {e}"


def get_sample_data(table_name: str) -> str:
    """
    Retourne 5 vraies lignes d'une vue.
    Utiliser pour voir les vraies valeurs de APPROVALSTATUS,
    formats de date, codes projets, etc. avant de filtrer.
    """
    try:
        df = pd.read_sql(
            f"SELECT TOP 5 * FROM {table_name}",
            get_engine()
        )
        if df.empty:
            return f"Aucune donnée dans '{table_name}'."

        # Filtrer les colonnes metadata inutiles
        meta_cols = {"_run_id", "_source_table", "_load_mode",
                     "Deleted", "Deleted_At", "_ingested_at"}
        df = df[[c for c in df.columns if c not in meta_cols]]

        return df.to_string(index=False)
    except Exception as e:
        return f"Erreur get_sample_data : {e}"


def get_table_relationships() -> str:
    """Retourne les clés de jointure entre les vues principales."""
    return """
=== Relations entre les vues Silver Layer ===

1. timesheet_header ──< timesheet_line
   timesheet_header.TIMESHEETNBR = timesheet_line.TIMESHEETNBR

2. timesheet_header/line ──> ga_resource (employé)
   timesheet_header.RESOURCE = ga_resource.RECID
   timesheet_line.RESOURCE   = ga_resource.RECID
   → Utiliser ga_resource.NAME pour le nom de l'employé

3. timesheet_line ──> prj_proj_table (projet)
   timesheet_line.PROJID = prj_proj_table.PROJID
   → Utiliser prj_proj_table.PROJNAME pour le nom du projet

4. timesheet_line ──> ga_task (tâche)
   timesheet_line.ACTIVITYNUMBER = ga_task.ACTIVITYNUMBER
   → Utiliser ga_task.TASKNAME pour le nom de la tâche

=== Jointure complète recommandée ===
SELECT
    r.NAME          AS Employe,
    p.PROJNAME      AS Projet,
    t.TASKNAME      AS Tache,
    l.CATEGORYID    AS Categorie,
    SUM(l.QTY)      AS TotalHeures
FROM timesheet_header h
JOIN timesheet_line l    ON h.TIMESHEETNBR = l.TIMESHEETNBR
JOIN ga_resource r       ON r.RECID = h.RESOURCE
JOIN prj_proj_table p    ON p.PROJID = l.PROJID
JOIN ga_task t           ON t.ACTIVITYNUMBER = l.ACTIVITYNUMBER
WHERE MONTH(h.PERIODFROM) = 1 AND YEAR(h.PERIODFROM) = 2026
GROUP BY r.NAME, p.PROJNAME, t.TASKNAME, l.CATEGORYID
ORDER BY TotalHeures DESC
"""


def execute_query(query: str) -> str:
    """
    Exécute une requête SQL SELECT sur la Silver Layer.
    Lecture seule — INSERT/UPDATE/DELETE refusés.
    Log la requête pour debug.
    """
    # Sécurité : SELECT uniquement
    q = query.strip().upper()
    if not (q.startswith("SELECT") or q.startswith("WITH")):
        return "Seules les requêtes SELECT sont autorisées."

    # Log de la requête pour debug
    print(f"\n[SQL] {query}\n")

    try:
        df = pd.read_sql(query, get_engine())

        if df.empty:
            return (
                "Aucun résultat trouvé.\n"
                "Conseil : si tu as utilisé APPROVALSTATUS ou d'autres filtres, "
                "réessaie sans ces filtres pour voir s'il y a des données."
            )

        # Filtrer colonnes metadata
        meta_cols = {"_run_id", "_source_table", "_load_mode",
                     "Deleted", "Deleted_At", "_ingested_at"}
        df = df[[c for c in df.columns if c not in meta_cols]]

        return f"{len(df)} ligne(s) :\n{df.to_string(index=False)}"

    except Exception as e:
        return (
            f"Erreur SQL : {e}\n"
            f"Requête exécutée : {query}\n"
            "Vérifie les noms de colonnes avec describe_table()."
        )