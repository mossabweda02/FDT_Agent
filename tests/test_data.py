"""
tests/test_data.py
===========================
Ce script de test :
- se connecte à la base de données Azure Synapse utilisée par l'agent FDT,
- récupère la liste des vues disponibles 
- affiche les métadonnées et un échantillon de donnéespour chaque vue. 
C'est un test de validation pour s'assurer que les données attendues sont bien présentes et accessibles.
"""

import pandas as pd
from backend.database.connection import get_engine


# ─────────────────────────────────────────
# Connexion à la base de données
# ─────────────────────────────────────────

engine = get_engine()

# ─────────────────────────────────────────
# 1. Récupération dynamique des vues
# ─────────────────────────────────────────
QUERY_VIEWS = """
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.VIEWS
ORDER BY TABLE_NAME
"""

views_df = pd.read_sql(QUERY_VIEWS, engine)

print("\n" + "=" * 80)
print("LISTE DES VUES DISPONIBLES")
print("=" * 80)
print(views_df.to_string(index=False))

# Liste dynamique des vues
all_views = views_df["TABLE_NAME"].tolist()

# ─────────────────────────────────────────
# 2. Exploration dynamique des vues
# ─────────────────────────────────────────
print("\n" + "=" * 80)
print("EXPLORATION DÉTAILLÉE DES VUES")
print("=" * 80)

for view_name in all_views:
    try:
        print(f"\n{'=' * 80}")
        print(f"VUE : {view_name}")
        print(f"{'=' * 80}")

        # ─────────────────────────────────────────
        # 2.1 Récupération métadonnées colonnes
        # ─────────────────────────────────────────
        columns_query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{view_name}'
        ORDER BY ORDINAL_POSITION
        """

        columns_df = pd.read_sql(columns_query, engine)

        print("\nCOLONNES ET TYPES :")
        print("-" * 40)
        print(columns_df.to_string(index=False))

        # ─────────────────────────────────────────
        # 2.2 Récupération 10 premières lignes
        # ─────────────────────────────────────────
        sample_query = f"SELECT TOP 10 * FROM [{view_name}]"
        sample_df = pd.read_sql(sample_query, engine)

        print("\nAPERÇU DES 10 PREMIÈRES LIGNES :")
        print("-" * 40)

        if sample_df.empty:
            print("Aucune donnée disponible.")
        else:
            print(sample_df.to_string(index=False))

    except Exception as e:
        print(f"\n❌ Erreur lors de l'exploration de {view_name}")
        print(f"Détail : {str(e)}")

# ─────────────────────────────────────────
# 3. Partie de test des reponses de l'agent FDT par rapport à la base de données
# ─────────────────────────────────────────

QUERY = """
SELECT COUNT(*) AS total_timesheets
FROM timesheet_header;
"""

print("\n==============================")
print("Reponse attendue")
print("==============================")

try:
    df = pd.read_sql(QUERY, engine)
    print(df.to_string(index=False))
except Exception as e:
    print(f"Erreur lors du COUNT sur timesheet_header : {e}")
