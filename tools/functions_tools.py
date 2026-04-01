import pandas as pd
from database.connection import get_engine


def list_tables() -> str:
    """Liste toutes les vues de la Silver Layer."""
    df = pd.read_sql(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_NAME",
        get_engine()
    )
    if df.empty:
        return "Aucune vue trouvée."
    return "\n".join(df["TABLE_NAME"].tolist())


def describe_table(table_name: str) -> str:
    """Retourne les colonnes et types d'une vue."""
    df = pd.read_sql(
        "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME = %(t)s ORDER BY ORDINAL_POSITION",
        get_engine(), params={"t": table_name}
    )
    if df.empty:
        return f"Vue '{table_name}' introuvable."
    return "\n".join(
        f"{r.COLUMN_NAME} ({r.DATA_TYPE})" for _, r in df.iterrows()
    )


def get_sample_data(table_name: str) -> str:
    """Retourne 5 lignes d'exemple pour comprendre les vraies valeurs."""
    try:
        df = pd.read_sql(f"SELECT TOP 5 * FROM {table_name}", get_engine())
        if df.empty:
            return f"Aucune donnée dans '{table_name}'."
        return df.to_string(index=False)
    except Exception as e:
        return f"Erreur : {e}"


def get_table_relationships() -> str:
    """Retourne les relations entre les vues principales."""
    return """
Relations entre les vues principales :

timesheet_header ──< timesheet_line
  Clé : timesheet_header.TIMESHEETNBR = timesheet_line.TIMESHEETNBR

Exemple de jointure :
  SELECT h.RESOURCE, h.PERIODFROM, SUM(l.QTY) AS TotalHeures
  FROM timesheet_header h
  JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
  GROUP BY h.RESOURCE, h.PERIODFROM
"""


def execute_query(query: str) -> str:
    """Exécute une requête SQL SELECT. Lecture seule."""
    if not query.strip().upper().startswith(("SELECT", "WITH")):
        return "Seules les requêtes SELECT sont autorisées."
    try:
        df = pd.read_sql(query, get_engine())
        if df.empty:
            return "Aucun résultat trouvé."
        return df.to_string(index=False)
    except Exception as e:
        return f"Erreur SQL : {e}"