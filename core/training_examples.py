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
SELECT PROJNAME, 
       CASE STATUS 
         WHEN 1 THEN 'Estimé' 
         WHEN 2 THEN 'Planifié' 
         WHEN 3 THEN 'En cours' 
       END AS Statut
FROM prj_proj_table
WHERE STATUS IN (1, 2, 3)
ORDER BY PROJNAME""",
        "expected_result": "Voici les projets actuellement actifs (Estimés, Planifiés ou En cours) : [Tableau avec Nom du Projet et Statut en clair]",
    },
    {
    "user_question": "Combien d'heures ont été enregistrées en décembre 2025 ?",
    "reasoning": (
        "Même logique que janvier\n"
        "Mais aucune donnée possible\n"
        "→ utiliser COALESCE"
    ),
    "sql_query": """
SELECT COALESCE(SUM(l.QTY), 0) AS TotalHeures
FROM timesheet_header h
JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
WHERE MONTH(h.PERIODFROM) = 12
  AND YEAR(h.PERIODFROM) = 2025""",
    "expected_result": "0 heure si aucune donnée",
}
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
    {
    "user_question": "Quels employés ont travaillé en janvier 2026 ?",
    "reasoning": (
        "Jointure header + line + resource\n"
        "GROUP BY obligatoire\n"
        "r.NAME obligatoire"
    ),
    "sql_query": """
SELECT r.NAME AS Employe, SUM(l.QTY) AS TotalHeures
FROM timesheet_header h
JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
JOIN ga_resource r ON r.RECID = h.RESOURCE
WHERE MONTH(h.PERIODFROM) = 1
  AND YEAR(h.PERIODFROM) = 2026
GROUP BY r.NAME
ORDER BY TotalHeures DESC""",
    "expected_result": "Liste employés avec heures",
}
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
        "expected_result": "Matrice employé × projet avec heures — afficher sous forme de tableau Markdown",
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
            "Rentabilité = TotalSalePrice - TotalStandardCost\n"
            "Colonnes disponibles : TotalSalePrice, TotalStandardCost dans timesheet_line\n"
            "Jointure line + prj_proj_table\n"
            "⚠️ PAS de filtre APPROVALSTATUS\n"
            "⚠️ Certains projets auront Marge = NULL si données manquantes → ORDER BY COALESCE"
        ),
        "sql_query": """
SELECT
    p.PROJNAME AS Projet,
    SUM(l.TotalSalePrice)    AS ChiffreAffaires,
    SUM(l.TotalStandardCost) AS CoutTotal,
    SUM(l.TotalSalePrice) - SUM(l.TotalStandardCost) AS Marge
FROM timesheet_line l
JOIN prj_proj_table p ON p.PROJID = l.PROJID
GROUP BY p.PROJID, p.PROJNAME
ORDER BY Marge DESC""",
        "expected_result": "Projets classés par marge décroissante — afficher les NaN comme 'Données insuffisantes'",
    },
    {
        "user_question": "Quel projet a pris le plus de temps ?",
        "reasoning": (
            "TOP 1\n"
            "GROUP BY projet\n"
            "ORDER BY SUM DESC\n"
            "Jointure directe line + prj_proj_table (pas besoin de header)"
        ),
        "sql_query": """
SELECT TOP 1 p.PROJNAME AS Projet, SUM(l.QTY) AS TotalHeures
FROM timesheet_line l
JOIN prj_proj_table p ON p.PROJID = l.PROJID
GROUP BY p.PROJID, p.PROJNAME
ORDER BY TotalHeures DESC""",
        "expected_result": "Projet avec le plus grand nombre d'heures",
    },
    {
        "user_question": "Quelle tâche prend le plus de temps et sur quel projet ?",
        "reasoning": (
            "TOP 1\n"
            "Jointure line + ga_task + prj_proj_table\n"
            "⚠️ PAS de jointure header si pas nécessaire\n"
            "GROUP BY tâche ET projet\n"
            "ORDER BY SUM(QTY) DESC"
        ),
        "sql_query": """
SELECT TOP 1
    t.TASKNAME  AS Tache,
    p.PROJNAME  AS Projet,
    SUM(l.QTY)  AS TotalHeures
FROM timesheet_line l
JOIN ga_task t        ON t.ACTIVITYNUMBER = l.ACTIVITYNUMBER
JOIN prj_proj_table p ON p.PROJID = l.PROJID
GROUP BY t.ACTIVITYNUMBER, t.TASKNAME, p.PROJID, p.PROJNAME
ORDER BY TotalHeures DESC""",
        "expected_result": "Tâche avec le plus d'heures et son projet associé",
    },
    {
        "user_question": "Quel est le total des heures par projet en janvier 2026 ?",
        "reasoning": (
            "Jointure header + line + prj_proj_table\n"
            "Filtre mois = 1, année = 2026\n"
            "GROUP BY projet\n"
            "⚠️ PAS de filtre APPROVALSTATUS"
        ),
        "sql_query": """
SELECT p.PROJNAME AS Projet, SUM(l.QTY) AS TotalHeures
FROM timesheet_header h
JOIN timesheet_line l  ON h.TIMESHEETNBR = l.TIMESHEETNBR
JOIN prj_proj_table p  ON p.PROJID = l.PROJID
WHERE MONTH(h.PERIODFROM) = 1
  AND YEAR(h.PERIODFROM) = 2026
GROUP BY p.PROJID, p.PROJNAME
ORDER BY TotalHeures DESC""",
        "expected_result": "Tableau des projets avec heures triées par ordre décroissant",
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
    {
    "user_question": "Heures par employé",
    "wrong_sql": "SELECT r",
    "why_wrong": "Requête incomplète → manque FROM + JOIN + GROUP BY",
    "sql_query": """
SELECT r.NAME, SUM(l.QTY)
FROM timesheet_header h
JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
JOIN ga_resource r ON r.RECID = h.RESOURCE
GROUP BY r.NAME""",
    "expected_result": "Requête complète",
}
]

# ── Fonctions d'accès aux exemples ───────────────────────────────────────
# Cet fonction permette de récupérer les exemples d'entraînement pour les intégrer dans le prompt de formation du modèle.
TOP_EXAMPLES = (
    BASIC_EXAMPLES           # 4 exemples basiques
    + INTERMEDIATE_EXAMPLES  # 4 exemples intermédiaires
    + ADVANCED_EXAMPLES      # 6 exemples avancés (tous inclus maintenant)
    + ERROR_CORRECTION_EXAMPLES  # 4 corrections d'erreurs
)
def get_all_examples() -> List[Dict]:
    return TOP_EXAMPLES 

# ── Fonction de formatage pour le prompt ───────────────────────────────────────
# Cette fonction convertit la liste d'exemples en une chaîne de caractères formatée pour être utilisée dans le prompt d'entraînement du modèle.
def format_examples_for_prompt() -> str:
    examples = get_all_examples()

    out = "## Exemples SQL — Few-Shot Learning\n\n"
    out += "RÈGLES IMPORTANTES :\n"
    out += "- Générer UNIQUEMENT des requêtes SQL complètes et valides\n"
    out += "- Toujours inclure FROM + JOIN si nécessaire\n"
    out += "- Toujours utiliser GROUP BY avec SUM\n"
    out += "- Ne JAMAIS filtrer APPROVALSTATUS sauf demande explicite\n\n"

    for i, ex in enumerate(examples, 1):
        out += f"### Exemple {i}\n\n"

        # Question
        out += f"Question:\n{ex['user_question']}\n\n"

        # Raisonnement
        if "reasoning" in ex:
            out += f"Analyse:\n{ex['reasoning']}\n\n"

        # Mauvais SQL
        if "wrong_sql" in ex:
            out += "❌ SQL incorrect (ne pas reproduire):\n"
            out += f"```text\n{ex['wrong_sql'].strip()}\n```\n"
            out += f"Erreur:\n{ex['why_wrong']}\n\n"

        # Bon SQL
        out += "✅ SQL attendu:\n"
        out += f"```sql\n{ex['sql_query'].strip()}\n```\n\n"

        # Résultat
        if "expected_result" in ex:
            out += f"Réponse attendue:\n{ex['expected_result']}\n\n"

        out += "-----------------------------\n\n"

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