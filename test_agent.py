"""
test_agent.py
=============
Tests de l'agent Pydantic AI FDT Timesheet.
"""

import asyncio
import sys
import pandas as pd
from dotenv import load_dotenv

from database.connection import get_engine
from agent.pydantic_agent.agent import ask  # ← Pydantic AI

load_dotenv()

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"


# ══════════════════════════════════════════════════════════════════
# VÉRIFICATION SQL DIRECTE (inchangée)
# ══════════════════════════════════════════════════════════════════

def verify_sql(sql: str) -> str:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn)
        if df.empty:
            return f"{YELLOW}SQL direct → Aucun résultat{RESET}"
        META = {"_run_id", "_source_table", "_load_mode", "Deleted", "Deleted_At", "_ingested_at"}
        df = df[[c for c in df.columns if c not in META]]
        return f"{GREEN}SQL direct → {len(df)} ligne(s) :{RESET}\n{df.to_string(index=False)}"
    except Exception as e:
        return f"{RED}SQL direct → Erreur : {e}{RESET}"


# ══════════════════════════════════════════════════════════════════
# TEST CASES (inchangés)
# ══════════════════════════════════════════════════════════════════

TEST_CASES = [
    {
        "id": 1, "niveau": "FACILE",
        "question": "Quelles sont les vues disponibles dans la base ?",
        "sql_verification": "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_NAME",
        "attendu": "Liste de vues dont timesheet_header et timesheet_line",
    },
    {
        "id": 2, "niveau": "FACILE",
        "question": "Combien d'heures ont été enregistrées en janvier 2026 ?",
        "sql_verification": """
            SELECT SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
            WHERE MONTH(h.PERIODFROM) = 1 AND YEAR(h.PERIODFROM) = 2026
        """,
        "attendu": "Total heures janvier 2026",
    },
    {
        "id": 3, "niveau": "FACILE",
        "question": "Combien d'heures ont été enregistrées en décembre 2025 ?",
        "sql_verification": """
            SELECT SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
            WHERE MONTH(h.PERIODFROM) = 12 AND YEAR(h.PERIODFROM) = 2025
        """,
        "attendu": "Total heures décembre 2025",
    },
    {
        "id": 4, "niveau": "MOYEN",
        "question": "Quel est le total des heures par projet en janvier 2026 ?",
        "sql_verification": """
            SELECT p.PROJID, p.PROJNAME, SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
            JOIN prj_proj_table p ON p.PROJID = l.PROJID
            WHERE MONTH(h.PERIODFROM) = 1 AND YEAR(h.PERIODFROM) = 2026
            GROUP BY p.PROJID, p.PROJNAME ORDER BY TotalHeures DESC
        """,
        "attendu": "Projets + heures triés par total décroissant",
    },
    {
        "id": 5, "niveau": "MOYEN",
        "question": "Quels employés ont travaillé en janvier 2026 et combien d'heures ?",
        "sql_verification": """
            SELECT r.NAME AS Employe, SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
            JOIN ga_resource r    ON r.RECID = h.RESOURCE
            WHERE MONTH(h.PERIODFROM) = 1 AND YEAR(h.PERIODFROM) = 2026
            GROUP BY r.NAME ORDER BY TotalHeures DESC
        """,
        "attendu": "Employés + heures janvier 2026",
    },
    {
        "id": 6, "niveau": "MOYEN",
        "question": "What are the top 3 projects by hours worked in 2026?",
        "sql_verification": """
            SELECT TOP 3 p.PROJID, p.PROJNAME, SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
            JOIN prj_proj_table p ON p.PROJID = l.PROJID
            WHERE YEAR(h.PERIODFROM) = 2026
            GROUP BY p.PROJID, p.PROJNAME ORDER BY TotalHeures DESC
        """,
        "attendu": "Top 3 projets en anglais",
    },
    {
        "id": 7, "niveau": "AVANCÉ",
        "question": "Montre-moi les heures par employé et par projet en janvier 2026",
        "sql_verification": """
            SELECT r.NAME AS Employe, p.PROJNAME AS Projet, SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
            JOIN ga_resource r    ON r.RECID = h.RESOURCE
            JOIN prj_proj_table p ON p.PROJID = l.PROJID
            WHERE MONTH(h.PERIODFROM) = 1 AND YEAR(h.PERIODFROM) = 2026
            GROUP BY r.NAME, p.PROJNAME ORDER BY r.NAME, TotalHeures DESC
        """,
        "attendu": "Matrice employé × projet avec heures",
    },
    {
        "id": 8, "niveau": "AVANCÉ",
        "question": "Quelles tâches ont été effectuées sur le projet PRJ-00329 ?",
        "sql_verification": """
            SELECT t.ACTIVITYNUMBER, t.TASKNAME, l.CATEGORYID, SUM(l.QTY) AS TotalHeures
            FROM timesheet_line l
            JOIN ga_task t ON t.ACTIVITYNUMBER = l.ACTIVITYNUMBER
            WHERE l.PROJID = 'PRJ-00329'
            GROUP BY t.ACTIVITYNUMBER, t.TASKNAME, l.CATEGORYID
            ORDER BY TotalHeures DESC
        """,
        "attendu": "Tâches du projet PRJ-00329",
    },
    {
        "id": 9,  "niveau": "HORS CONTEXTE",
        "question": "Quel est le meilleur restaurant à Tunis ?",
        "sql_verification": None,
        "attendu": "Refus — hors contexte en français",
    },
    {
        "id": 10, "niveau": "HORS CONTEXTE",
        "question": "What is the weather in Montreal today?",
        "sql_verification": None,
        "attendu": "Refus — out of context in English",
    },
    {
        "id": 11, "niveau": "ANALYTIQUE",
        "question": "Quel projet a pris le plus de temps au total ?",
        "sql_verification": """
            SELECT TOP 1 p.PROJID, p.PROJNAME, SUM(l.QTY) AS TotalHeures
            FROM timesheet_line l
            JOIN prj_proj_table p ON p.PROJID = l.PROJID
            GROUP BY p.PROJID, p.PROJNAME ORDER BY TotalHeures DESC
        """,
        "attendu": "Projet avec le plus grand SUM(QTY)",
    },
    {
        "id": 12, "niveau": "ANALYTIQUE",
        "question": "Quels sont les projets les plus rentables ?",
        "sql_verification": """
            SELECT p.PROJID, p.PROJNAME,
                   SUM(l.TotalSalePrice)    AS ChiffreAffaires,
                   SUM(l.TotalStandardCost) AS CoutTotal,
                   SUM(l.TotalSalePrice) - SUM(l.TotalStandardCost) AS Marge
            FROM timesheet_line l
            JOIN prj_proj_table p ON p.PROJID = l.PROJID
            WHERE l.TotalSalePrice IS NOT NULL
            GROUP BY p.PROJID, p.PROJNAME ORDER BY Marge DESC
        """,
        "attendu": "Projets classés par marge décroissante",
    },
    {
        "id": 13, "niveau": "ANALYTIQUE",
        "question": "Quelle tâche prend le plus de temps et sur quel projet ?",
        "sql_verification": """
            SELECT TOP 1 t.ACTIVITYNUMBER, t.TASKNAME,
                   p.PROJID, p.PROJNAME, SUM(l.QTY) AS TotalHeures
            FROM timesheet_line l
            JOIN ga_task t        ON t.ACTIVITYNUMBER = l.ACTIVITYNUMBER
            JOIN prj_proj_table p ON p.PROJID = l.PROJID
            GROUP BY t.ACTIVITYNUMBER, t.TASKNAME, p.PROJID, p.PROJNAME
            ORDER BY TotalHeures DESC
        """,
        "attendu": "Tâche avec le plus d'heures + son projet",
    },
]


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

async def main():
    print(f"\n{'='*65}")
    print(f"  TESTS AGENT FDT — Pydantic AI")
    print(f"{'='*65}\n")

    filtre = sys.argv[1].upper() if len(sys.argv) > 1 else None
    tests  = [t for t in TEST_CASES if not filtre or t["niveau"] == filtre]

    scores = []

    for tc in tests:
        print(f"\n{'─'*65}")
        print(f"  TEST {tc['id']:02d} [{tc['niveau']}]")
        print(f"  Question : {tc['question']}")
        print(f"  Attendu  : {tc['attendu']}")
        print(f"{'─'*65}")

        # 1. Vérification SQL directe
        if tc["sql_verification"]:
            print(f"\n{YELLOW}── VÉRIFICATION SQL DIRECTE ──{RESET}")
            print(verify_sql(tc["sql_verification"]))

        # 2. Réponse agent Pydantic AI
        print(f"\n{BLUE}── RÉPONSE AGENT ──{RESET}")
        print("  Traitement en cours...")
        try:
            response = await ask(tc["question"])  # ← appel direct, plus de client Azure
            print(f"\n{response}")
        except Exception as e:
            response = f"[EXCEPTION] {e}"
            print(f"\n{RED}{response}{RESET}")

        # 3. Score manuel
        raw_score = input(
            f"\n{YELLOW}Score ? (1=Réussi / 0.5=Partiel / 0=Échec) : {RESET}"
        ).strip()

        try:
            score = float(raw_score) if raw_score else 0.0
        except ValueError:
            score = 0.0
        scores.append(score)
        print(f"{GREEN}→ Passage au test suivant...{RESET}")

    # Résumé final
    total   = sum(scores)
    max_pts = len(scores)
    pct     = (total / max_pts * 100) if max_pts else 0

    print(f"\n{'='*65}")
    print(f"  RÉSULTATS FINAUX")
    print(f"{'='*65}")
    for tc, s in zip(tests, scores):
        emoji = "✅" if s == 1 else ("⚠️ " if s == 0.5 else "❌")
        print(f"  {emoji} Test {tc['id']:02d} [{tc['niveau']:15s}] — {s}")
    print(f"{'─'*65}")
    print(f"  Score : {total}/{max_pts} = {pct:.0f}%")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    asyncio.run(main())