"""
Exemples few-shot — annotés avec les vraies données.

Objectif : fournir un apprentissage par l'exemple riche et réaliste pour guider le modèle dans la génération de requêtes SQL correctes et efficaces.

c'est quoi few-shot ? : Le few-shot learning est une technique d'apprentissage automatique où un modèle est entraîné à effectuer une tâche spécifique en lui fournissant 
seulement quelques exemples d'entrée-sortie. Dans le contexte de la génération de requêtes SQL, le few-shot learning peut aider le modèle à comprendre les structures et les 
patterns des requêtes correctes en lui montrant quelques exemples annotés avec les vraies données.
"""

from typing import List, Dict

BASIC_EXAMPLES = [
    {
        "user_question": "Combien d'heures ont été saisies en janvier 2026 ?",
        "reasoning": (
            "1. Jointure timesheet_header + timesheet_line\n"
            "2. Filtre MONTH(h.PERIODFROM)=1 AND YEAR=2026\n"
            "3. ⚠️ PAS de filtre APPROVALSTATUS\n"
            "4. SUM(l.QTY)"
        ),
        "sql_query": """
SELECT SUM(l.QTY) AS TotalHeures
FROM timesheet_header h
JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
WHERE MONTH(h.PERIODFROM) = 1
  AND YEAR(h.PERIODFROM) = 2026""",
        "expected_result": "476 heures (tous statuts : Draft + Submitted + Approved)",
    },

    {
        "user_question": "Combien d'heures APPROUVÉES en janvier 2026 ?",
        "reasoning": (
            "L'utilisateur dit explicitement 'approuvées'\n"
            "→ Ajouter APPROVALSTATUS = 3"
        ),
        "sql_query": """
SELECT SUM(l.QTY) AS TotalHeuresApprouvees
FROM timesheet_header h
JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
WHERE h.APPROVALSTATUS = 3
  AND MONTH(h.PERIODFROM) = 1
  AND YEAR(h.PERIODFROM) = 2026""",
        "expected_result": "70 heures (uniquement approuvées)",
    },

    {
        "user_question": "Liste des projets actifs",
        "reasoning": (
            "STATUS : 0=Created 1=Estimated 2=Scheduled 3=InProcess 4=Completed\n"
            "Actifs = STATUS IN (1,2,3)"
        ),
        "sql_query": """
SELECT PROJID, PROJNAME, STATUS
FROM prj_proj_table
WHERE STATUS IN (1, 2, 3)
ORDER BY PROJNAME""",
        "expected_result": "Liste projets Estimated/Scheduled/InProcess",
    },
]

INTERMEDIATE_EXAMPLES = [
    {
        "user_question": "Heures par employé en janvier 2026",
        "reasoning": (
            "Jointure header + line + ga_resource\n"
            "⚠️ PAS de filtre APPROVALSTATUS\n"
            "GROUP BY r.NAME"
        ),
        "sql_query": """
SELECT r.NAME AS Employe, SUM(l.QTY) AS TotalHeures
FROM timesheet_header h
JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
JOIN ga_resource r    ON r.RECID = h.RESOURCE
WHERE MONTH(h.PERIODFROM) = 1
  AND YEAR(h.PERIODFROM) = 2026
GROUP BY r.NAME
ORDER BY TotalHeures DESC""",
        "expected_result": "Émilie Gagnon 350h, Oumaima Chmissi 98h, Jason Li 28h",
    },

    {
        "user_question": "TOP 3 projets par heures en 2026",
        "reasoning": (
            "Jointure header + line + prj_proj_table\n"
            "⚠️ TOP 3 pas LIMIT 3\n"
            "⚠️ PAS de filtre APPROVALSTATUS\n"
            "GROUP BY p.PROJID, p.PROJNAME"
        ),
        "sql_query": """
SELECT TOP 3 p.PROJID, p.PROJNAME, SUM(l.QTY) AS TotalHeures
FROM timesheet_header h
JOIN timesheet_line l  ON h.TIMESHEETNBR = l.TIMESHEETNBR
JOIN prj_proj_table p  ON p.PROJID = l.PROJID
WHERE YEAR(h.PERIODFROM) = 2026
GROUP BY p.PROJID, p.PROJNAME
ORDER BY TotalHeures DESC""",
        "expected_result": "PRJ-00329 (1540h), PRJ-00022 (924h), PRJ-00407 (518h)",
    },

    {
        "user_question": "What are the top 3 projects by hours worked in 2026?",
        "reasoning": (
            "'projects' → prj_proj_table (pas ga_resource)\n"
            "TOP 3 pas LIMIT\n"
            "Répondre en anglais"
        ),
        "sql_query": """
SELECT TOP 3 p.PROJID, p.PROJNAME, SUM(l.QTY) AS TotalHeures
FROM timesheet_header h
JOIN timesheet_line l  ON h.TIMESHEETNBR = l.TIMESHEETNBR
JOIN prj_proj_table p  ON p.PROJID = l.PROJID
WHERE YEAR(h.PERIODFROM) = 2026
GROUP BY p.PROJID, p.PROJNAME
ORDER BY TotalHeures DESC""",
        "expected_result": "Top 3 projects with hours (English answer)",
    },
]

ADVANCED_EXAMPLES = [
    {
        "user_question": "Heures par employé et par projet en janvier 2026",
        "reasoning": (
            "Jointure quadruple : header + line + resource + project\n"
            "⚠️ PAS de filtre APPROVALSTATUS\n"
            "GROUP BY r.NAME, p.PROJNAME"
        ),
        "sql_query": """
SELECT r.NAME AS Employe, p.PROJNAME AS Projet, SUM(l.QTY) AS TotalHeures
FROM timesheet_header h
JOIN timesheet_line l  ON h.TIMESHEETNBR = l.TIMESHEETNBR
JOIN ga_resource r     ON r.RECID = h.RESOURCE
JOIN prj_proj_table p  ON p.PROJID = l.PROJID
WHERE MONTH(h.PERIODFROM) = 1
  AND YEAR(h.PERIODFROM) = 2026
GROUP BY r.NAME, p.PROJNAME
ORDER BY r.NAME, TotalHeures DESC""",
        "expected_result": "Matrice employé × projet avec heures",
    },

    {
        "user_question": "Quelles tâches ont été effectuées sur le projet PRJ-00329 ?",
        "reasoning": (
            "Jointure line + ga_task\n"
            "Filtre l.PROJID = 'PRJ-00329'\n"
            "⚠️ PAS de jointure header → pas d'alias h disponible\n"
            "⚠️ PAS de filtre h.APPROVALSTATUS (h n'existe pas)"
        ),
        "sql_query": """
SELECT t.ACTIVITYNUMBER, t.TASKNAME, l.CATEGORYID, SUM(l.QTY) AS TotalHeures
FROM timesheet_line l
JOIN ga_task t ON t.ACTIVITYNUMBER = l.ACTIVITYNUMBER
WHERE l.PROJID = 'PRJ-00329'
GROUP BY t.ACTIVITYNUMBER, t.TASKNAME, l.CATEGORYID
ORDER BY TotalHeures DESC""",
        "expected_result": "Tâches PRJ-00329 avec heures par catégorie",
    },

    {
        "user_question": "Quels sont les projets les plus rentables ?",
        "reasoning": (
            "Rentabilité = SalePrice - StandardCost\n"
            "Jointure line + prj_proj_table\n"
            "⚠️ PAS de filtre APPROVALSTATUS\n"
            "WHERE TotalSalePrice IS NOT NULL"
        ),
        "sql_query": """
SELECT
    p.PROJID,
    p.PROJNAME,
    SUM(l.TotalSalePrice)    AS ChiffreAffaires,
    SUM(l.TotalStandardCost) AS CoutTotal,
    SUM(l.TotalSalePrice) - SUM(l.TotalStandardCost) AS Marge
FROM timesheet_line l
JOIN prj_proj_table p ON p.PROJID = l.PROJID
WHERE l.TotalSalePrice IS NOT NULL
GROUP BY p.PROJID, p.PROJNAME
ORDER BY Marge DESC""",
        "expected_result": "Projets classés par marge décroissante",
    },
]

ERROR_CORRECTION_EXAMPLES = [
    {
        "user_question": "Total des heures en janvier 2026",
        # ✅ Utiliser "wrong_sql_text" au lieu de mettre dans ```sql```
        "wrong_sql": "WHERE h.APPROVALSTATUS = 3 AND MONTH(h.PERIODFROM) = 1",
        "why_wrong": "APPROVALSTATUS = 3 non demandé → perd 85% des données",
        "sql_query": """
SELECT SUM(l.QTY) AS TotalHeures
FROM timesheet_header h
JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
WHERE MONTH(h.PERIODFROM) = 1
  AND YEAR(h.PERIODFROM) = 2026""",
        "expected_result": "476 heures (pas 70)",
    },
    {
        "user_question": "Top 10 dernières feuilles",
        "wrong_sql": "SELECT * FROM timesheet_header ORDER BY CREATEDDATE DESC LIMIT 10",
        "why_wrong": "LIMIT est MySQL — T-SQL utilise TOP N",
        "sql_query": """
SELECT TOP 10 TIMESHEETNBR, PERIODFROM, PERIODTO, APPROVALSTATUS
FROM timesheet_header
ORDER BY CREATEDDATE DESC""",
        "expected_result": "10 feuilles récentes sans erreur SQL",
    },
    {
        "user_question": "Tâches du projet PRJ-00329",
        "wrong_sql": "WHERE l.PROJID = 'PRJ-00329' AND h.APPROVALSTATUS = 3",
        "why_wrong": "h n'existe pas dans cette requête → 'could not be bound'",
        "sql_query": """
SELECT t.ACTIVITYNUMBER, t.TASKNAME, SUM(l.QTY) AS TotalHeures
FROM timesheet_line l
JOIN ga_task t ON t.ACTIVITYNUMBER = l.ACTIVITYNUMBER
WHERE l.PROJID = 'PRJ-00329'
GROUP BY t.ACTIVITYNUMBER, t.TASKNAME
ORDER BY TotalHeures DESC""",
        "expected_result": "Tâches sans erreur 'could not be bound'",
    },
]

# ── Fonctions d'accès aux exemples ───────────────────────────────────────
# Cet fonction permette de récupérer les exemples d'entraînement pour les intégrer dans le prompt de formation du modèle.
def get_all_examples() -> List[Dict]:
    return (BASIC_EXAMPLES + INTERMEDIATE_EXAMPLES
            + ADVANCED_EXAMPLES + ERROR_CORRECTION_EXAMPLES)

# ── Fonction de formatage pour le prompt ───────────────────────────────────────
# Cette fonction convertit la liste d'exemples en une chaîne de caractères formatée pour être utilisée dans le prompt d'entraînement du modèle.
def format_examples_for_prompt() -> str:
    examples = get_all_examples()
    out = "## Exemples SQL — Few-Shot Learning\n\n"
    out += "RÈGLE : Ne JAMAIS filtrer par APPROVALSTATUS par défaut.\n\n"

    for i, ex in enumerate(examples, 1):
        out += f"### Exemple {i} — {ex['user_question']}\n\n"

        if "reasoning" in ex:
            out += f"Raisonnement :\n{ex['reasoning']}\n\n"

        if "wrong_sql" in ex:
            # ✅ Balise "text" au lieu de "sql" — le check ignore les blocs non-sql
            out += f"❌ SQL incorrect (ne pas reproduire) :\n"
            out += f"```text\n{ex['wrong_sql'].strip()}\n```\n"
            out += f"Pourquoi incorrect : {ex['why_wrong']}\n\n"

        # ✅ Seul le bon SQL est dans ```sql```
        out += f"✅ SQL correct :\n```sql\n{ex['sql_query'].strip()}\n```\n\n"

        if "expected_result" in ex:
            out += f"Résultat : {ex['expected_result']}\n\n"

        out += "---\n\n"

    return out

# ── Test d'affichage des exemples ───────────────────────────────────────
if __name__ == "__main__":
    all_ex = get_all_examples()
    print(f"Total : {len(all_ex)} exemples")
    print(f"  Basiques      : {len(BASIC_EXAMPLES)}")
    print(f"  Intermédiaires: {len(INTERMEDIATE_EXAMPLES)}")
    print(f"  Avancés       : {len(ADVANCED_EXAMPLES)}")
    print(f"  Corrections   : {len(ERROR_CORRECTION_EXAMPLES)}")
    print(format_examples_for_prompt()[:500])