"""
test_data.py
Exploration de la base de données FDT
"""

import pandas as pd
from database.connection import get_engine


# ─────────────────────────────────────────
# Connexion à la base de données
# ─────────────────────────────────────────

engine = get_engine()


# ─────────────────────────────────────────
# 1. Liste des vues disponibles
# ─────────────────────────────────────────

QUERY_VIEWS = """
SELECT DISTINCT TABLE_NAME
FROM INFORMATION_SCHEMA.VIEWS
ORDER BY TABLE_NAME
"""

views_df = pd.read_sql(QUERY_VIEWS, engine)

print("\n==============================")
print("VUES DISPONIBLES")
print("==============================")
print(views_df.to_string(index=False))


# ─────────────────────────────────────────
# 2. Exemple de données (timesheet_header)
# ─────────────────────────────────────────

QUERY_SAMPLE_TIMESHEET = """
SELECT TOP 10 *
FROM timesheet_header
"""

sample_df = pd.read_sql(QUERY_SAMPLE_TIMESHEET, engine)

print("\n==============================")
print("EXEMPLE DE DONNÉES : TIMESHEET_HEADER")
print("==============================")
print(sample_df.to_string(index=False))


# ─────────────────────────────────────────
# 3. Tables à explorer pour l'agent FDT
# ─────────────────────────────────────────

TABLES_TO_EXPLORE = [
    "acp_expense_card",
    "ga_enum_table",
    "ga_enum_value_table",
    "ga_location",
    "ga_resource",
    "ga_resource_booking",
    "ga_task",
    "ga_task_line",
    "ga_task_source",
    "ga_task_source_assignment",
    "ga_unit_of_measure",
    "hrm_working_calendar",
    "hrm_working_day",
    "hrm_working_hours",
    "prc_vendor_order_header",
    "prc_vendor_order_line",
    "prj_delivery",
    "prj_delivery_task",
    "prj_equipment_operator",
    "prj_proj_table",
    "prj_project_assigned_resources",
    "timesheet_header",
    "timesheet_line",
]


# ─────────────────────────────────────────
# 4. Exploration des tables
# ─────────────────────────────────────────

print("\n==============================")
print("EXPLORATION DES TABLES")
print("==============================")

for table in TABLES_TO_EXPLORE:

    try:
        df = pd.read_sql(f"SELECT TOP 3 * FROM {table}", engine)

        print(f"\n--- {table.upper()} ---")
        print(f"Nombre de colonnes : {len(df.columns)}")
        print("Colonnes :", list(df.columns))
        print("\nExemple de données :")
        print(df.to_string(index=False))

    except Exception as e:
        print(f"\n[{table}] → Introuvable ou erreur : {e}")

# ─────────────────────────────────────────
# 1. Partie de test des reponses de l'agent FDT par rapport à la base de données
# ─────────────────────────────────────────

QUERY = """
SELECT COUNT(*) AS total_timesheets
FROM timesheet_header;

"""

df = pd.read_sql(QUERY, engine)

print("\n==============================")
print("Reponse attendue")
print("==============================")
print(df.to_string(index=False))