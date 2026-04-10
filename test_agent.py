"""
test_agent.py
=============
Tests de l'agent avec vérification SQL directe.
"""

import asyncio
import json
import os
import re
import sys

import pandas as pd
from dotenv import load_dotenv
from azure.ai.agents.aio import AgentsClient
from azure.ai.agents.models import MessageRole, RunStatus
from azure.identity.aio import DefaultAzureCredential

from database.connection import get_engine
from tools.tools_runner import run_tool

load_dotenv()

AGENT_ID = os.environ["AGENT_ID"]
ENDPOINT = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"

# ══════════════════════════════════════════════════════════════════
# FIX 1 — verify_sql : connexion explicite via pyodbc
# ══════════════════════════════════════════════════════════════════

def verify_sql(sql: str) -> str:
    """
    Exécute la requête SQL de vérification directement.
    Utilise une connexion explicite pour éviter l'erreur
    'This result object does not return rows'.
    """
    try:
        # ✅ Connexion explicite — évite le bug SQLAlchemy + pd.read_sql
        engine = get_engine()
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn)

        if df.empty:
            return f"{YELLOW}SQL direct → Aucun résultat{RESET}"

        # Exclure colonnes metadata pipeline
        META = {"_run_id", "_source_table", "_load_mode",
                "Deleted", "Deleted_At", "_ingested_at"}
        df = df[[c for c in df.columns if c not in META]]

        return (
            f"{GREEN}SQL direct → {len(df)} ligne(s) :{RESET}\n"
            f"{df.to_string(index=False)}"
        )
    except Exception as e:
        return f"{RED}SQL direct → Erreur : {e}{RESET}"


# ══════════════════════════════════════════════════════════════════
# FIX 2 — parse_tool_args : JSON robuste
# ══════════════════════════════════════════════════════════════════

def parse_tool_args(raw: str) -> dict:
    """
    Parse les arguments d'un tool call de manière robuste.

    Cas gérés :
    - None ou vide         → {}
    - JSON valide          → dict normal
    - JSON tronqué         → tente une réparation
    - Double JSON collé    → prend le premier objet valide
    - Texte non-JSON       → {}
    """
    # Cas 1 : vide ou None
    if not raw or not raw.strip():
        return {}

    raw = raw.strip()

    # Cas 2 : JSON valide directement
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Cas 3 : extraire le premier objet JSON valide avec une regex
    # Gère les cas "{ ... }{ ... }" ou "{ ... } texte parasite"
    match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Cas 4 : trouver l'objet JSON le plus long possible
    # en cherchant depuis le premier '{' jusqu'au dernier '}'
    start = raw.find('{')
    end   = raw.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Cas 5 : abandon — retourner dict vide
    print(f"  {RED}[WARN] Impossible de parser les args : {raw[:100]}{RESET}")
    return {}


# ══════════════════════════════════════════════════════════════════
# TEST CASES
# ══════════════════════════════════════════════════════════════════

TEST_CASES = [
    {
        "id": 1,
        "niveau": "FACILE",
        "question": "Quelles sont les vues disponibles dans la base ?",
        "sql_verification": """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            ORDER BY TABLE_NAME
        """,
        "attendu": "Liste de vues dont timesheet_header et timesheet_line",
    },
    {
        "id": 2,
        "niveau": "FACILE",
        "question": "Combien d'heures ont été enregistrées en janvier 2026 ?",
        "sql_verification": """
            SELECT SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
            WHERE MONTH(h.PERIODFROM) = 1
              AND YEAR(h.PERIODFROM) = 2026
        """,
        "attendu": "Total heures janvier 2026",
    },
    {
        "id": 3,
        "niveau": "FACILE",
        "question": "Combien d'heures ont été enregistrées en décembre 2025 ?",
        "sql_verification": """
            SELECT SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
            WHERE MONTH(h.PERIODFROM) = 12
              AND YEAR(h.PERIODFROM) = 2025
        """,
        "attendu": "Total heures décembre 2025",
    },
    {
        "id": 4,
        "niveau": "MOYEN",
        "question": "Quel est le total des heures par projet en janvier 2026 ?",
        "sql_verification": """
            SELECT p.PROJID, p.PROJNAME, SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l  ON h.TIMESHEETNBR = l.TIMESHEETNBR
            JOIN prj_proj_table p  ON p.PROJID = l.PROJID
            WHERE MONTH(h.PERIODFROM) = 1
              AND YEAR(h.PERIODFROM) = 2026
            GROUP BY p.PROJID, p.PROJNAME
            ORDER BY TotalHeures DESC
        """,
        "attendu": "Projets + heures triés par total décroissant",
    },
    {
        "id": 5,
        "niveau": "MOYEN",
        "question": "Quels employés ont travaillé en janvier 2026 et combien d'heures ?",
        "sql_verification": """
            SELECT r.NAME AS Employe, SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
            JOIN ga_resource r    ON r.RECID = h.RESOURCE
            WHERE MONTH(h.PERIODFROM) = 1
              AND YEAR(h.PERIODFROM) = 2026
            GROUP BY r.NAME
            ORDER BY TotalHeures DESC
        """,
        "attendu": "Employés + heures janvier 2026",
    },
    {
        "id": 6,
        "niveau": "MOYEN",
        "question": "What are the top 3 projects by hours worked in 2026?",
        "sql_verification": """
            SELECT TOP 3 p.PROJID, p.PROJNAME, SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l  ON h.TIMESHEETNBR = l.TIMESHEETNBR
            JOIN prj_proj_table p  ON p.PROJID = l.PROJID
            WHERE YEAR(h.PERIODFROM) = 2026
            GROUP BY p.PROJID, p.PROJNAME
            ORDER BY TotalHeures DESC
        """,
        "attendu": "Top 3 projets en anglais",
    },
    {
        "id": 7,
        "niveau": "AVANCÉ",
        "question": "Montre-moi les heures par employé et par projet en janvier 2026",
        "sql_verification": """
            SELECT r.NAME AS Employe, p.PROJNAME AS Projet,
                   SUM(l.QTY) AS TotalHeures
            FROM timesheet_header h
            JOIN timesheet_line l  ON h.TIMESHEETNBR = l.TIMESHEETNBR
            JOIN ga_resource r     ON r.RECID = h.RESOURCE
            JOIN prj_proj_table p  ON p.PROJID = l.PROJID
            WHERE MONTH(h.PERIODFROM) = 1
              AND YEAR(h.PERIODFROM) = 2026
            GROUP BY r.NAME, p.PROJNAME
            ORDER BY r.NAME, TotalHeures DESC
        """,
        "attendu": "Matrice employé × projet avec heures",
    },
    {
        "id": 8,
        "niveau": "AVANCÉ",
        "question": "Quelles tâches ont été effectuées sur le projet PRJ-00329 ?",
        "sql_verification": """
            SELECT t.ACTIVITYNUMBER, t.TASKNAME,
                   l.CATEGORYID, SUM(l.QTY) AS TotalHeures
            FROM timesheet_line l
            JOIN ga_task t ON t.ACTIVITYNUMBER = l.ACTIVITYNUMBER
            WHERE l.PROJID = 'PRJ-00329'
            GROUP BY t.ACTIVITYNUMBER, t.TASKNAME, l.CATEGORYID
            ORDER BY TotalHeures DESC
        """,
        "attendu": "Tâches du projet PRJ-00329",
    },
    {
        "id": 9,
        "niveau": "HORS CONTEXTE",
        "question": "Quel est le meilleur restaurant à Tunis ?",
        "sql_verification": None,
        "attendu": "Refus — hors contexte en français",
    },
    {
        "id": 10,
        "niveau": "HORS CONTEXTE",
        "question": "What is the weather in Montreal today?",
        "sql_verification": None,
        "attendu": "Refus — out of context in English",
    },
    {
        "id": 11,
        "niveau": "ANALYTIQUE",
        "question": "Quel projet a pris le plus de temps au total ?",
        "sql_verification": """
            SELECT TOP 1 p.PROJID, p.PROJNAME, SUM(l.QTY) AS TotalHeures
            FROM timesheet_line l
            JOIN prj_proj_table p ON p.PROJID = l.PROJID
            GROUP BY p.PROJID, p.PROJNAME
            ORDER BY TotalHeures DESC
        """,
        "attendu": "Projet avec le plus grand SUM(QTY)",
    },
    {
        "id": 12,
        "niveau": "ANALYTIQUE",
        "question": "Quels sont les projets les plus rentables ?",
        "sql_verification": """
            SELECT p.PROJID, p.PROJNAME,
                   SUM(l.TotalSalePrice)    AS ChiffreAffaires,
                   SUM(l.TotalStandardCost) AS CoutTotal,
                   SUM(l.TotalSalePrice) - SUM(l.TotalStandardCost) AS Marge
            FROM timesheet_line l
            JOIN prj_proj_table p ON p.PROJID = l.PROJID
            WHERE l.TotalSalePrice IS NOT NULL
            GROUP BY p.PROJID, p.PROJNAME
            ORDER BY Marge DESC
        """,
        "attendu": "Projets classés par marge décroissante",
    },
    {
        "id": 13,
        "niveau": "ANALYTIQUE",
        "question": "Quelle tâche prend le plus de temps et sur quel projet ?",
        "sql_verification": """
            SELECT TOP 1
                t.ACTIVITYNUMBER, t.TASKNAME,
                p.PROJID, p.PROJNAME,
                SUM(l.QTY) AS TotalHeures
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
# APPEL AGENT
# ══════════════════════════════════════════════════════════════════

async def ask_agent(client: AgentsClient, question: str) -> str:
    thread = await client.threads.create()
    await client.messages.create(
        thread_id=thread.id,
        role=MessageRole.USER,
        content=question,
    )
    run = await client.runs.create(
        thread_id=thread.id,
        agent_id=AGENT_ID,
    )

    while run.status in (RunStatus.QUEUED, RunStatus.IN_PROGRESS, RunStatus.REQUIRES_ACTION):
        await asyncio.sleep(1)
        run = await client.runs.get(thread_id=thread.id, run_id=run.id)

        if run.status == RunStatus.REQUIRES_ACTION:
            tool_outputs = []
            for tc in run.required_action.submit_tool_outputs.tool_calls:
                name     = tc.function.name
                raw_args = tc.function.arguments or "{}"

                # ✅ FIX 2 — parser robuste au lieu de json.loads direct
                args = parse_tool_args(raw_args)

                print(f"       {BLUE}[tool]{RESET} {name}({args})")
                result = run_tool(name, args)
                tool_outputs.append({
                    "tool_call_id": tc.id,
                    "output": str(result)
                })

            run = await client.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs,
            )

    if run.status == RunStatus.COMPLETED:
        messages = client.messages.list(thread_id=thread.id)
        async for msg in messages:
            if msg.role == MessageRole.AGENT:
                for block in msg.content:
                    if hasattr(block, "text"):
                        return block.text.value

    return f"{RED}[ERREUR]{RESET} {run.status} — {getattr(run, 'last_error', '')}"


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

async def main():
    print(f"\n{'='*65}")
    print(f"  TESTS AGENT FDT TIMESHEET")
    print(f"  Agent ID : {AGENT_ID}")
    print(f"{'='*65}\n")

    filtre = sys.argv[1].upper() if len(sys.argv) > 1 else None
    tests  = [t for t in TEST_CASES if not filtre or t["niveau"] == filtre]

    scores = []

    async with DefaultAzureCredential() as credential:
        async with AgentsClient(endpoint=ENDPOINT, credential=credential) as client:

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

                # 2. Réponse agent
                print(f"\n{BLUE}── RÉPONSE AGENT ──{RESET}")
                print("  Traitement en cours...")
                try:
                    response = await ask_agent(client, tc["question"])
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
    total    = sum(scores)
    max_pts  = len(scores)
    pct      = (total / max_pts * 100) if max_pts else 0

    print(f"\n{'='*65}")
    print(f"  RÉSULTATS FINAUX")
    print(f"{'='*65}")
    for i, (tc, s) in enumerate(zip(tests, scores)):
        emoji = "✅" if s == 1 else ("⚠️ " if s == 0.5 else "❌")
        print(f"  {emoji} Test {tc['id']:02d} [{tc['niveau']:15s}] — {s}")
    print(f"{'─'*65}")
    print(f"  Score : {total}/{max_pts} = {pct:.0f}%")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    asyncio.run(main())