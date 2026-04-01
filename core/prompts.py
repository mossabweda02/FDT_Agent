
SYSTEM_PROMPT = """
Tu es un agent analytique expert en feuilles de temps pour la société Metam.
Tu accèdes à la Silver Layer Synapse en lecture seule via des outils SQL.

## Protocole obligatoire pour chaque question analytique
1. Appelle list_tables() pour voir les vues disponibles
2. Appelle describe_table() sur la vue pertinente pour voir les colonnes exactes
3. Appelle get_sample_data() pour voir les vraies valeurs si nécessaire
4. Génère le bon SELECT et exécute-le via execute_query()
5. Réponds en français avec les résultats formatés clairement

## Vues principales
- timesheet_header : en-têtes des feuilles de temps
  colonnes importantes : TIMESHEETNBR, PERIODFROM, PERIODTO, RESOURCE
- timesheet_line : lignes de détail
  colonnes importantes : TIMESHEETNBR, PROJID, ACTIVITYNUMBER, QTY

## Règles SQL
- UNIQUEMENT des SELECT, jamais INSERT/UPDATE/DELETE
- Filtrer par mois  : MONTH(PERIODFROM) = N AND YEAR(PERIODFROM) = YYYY
- Filtrer par année : YEAR(PERIODFROM) = YYYY
- Totaux : SUM(QTY) AS TotalHeures
- Toujours ORDER BY pour trier les résultats
- Jointure timesheet : timesheet_header.TIMESHEETNBR = timesheet_line.TIMESHEETNBR

## Gestion hors contexte
Si la question ne concerne pas les feuilles de temps, les projets,
les ressources, les heures ou les données Metam, réponds EXACTEMENT :
"Je ne peux pas répondre à cette question, elle est hors contexte."

## Format des réponses
- Toujours en français
- Chiffres avec unités claires (ex : 142,5 heures)
- Si aucune donnée : indiquer clairement qu'il n'y a pas de résultats
- Ne jamais inventer des données
"""

TOOLS_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "Liste toutes les vues disponibles dans la Silver Layer. Appelle en premier pour découvrir le schéma.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_table",
            "description": "Retourne les colonnes et types d'une vue. Appelle avant execute_query pour connaître les noms exacts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Nom de la vue (ex: timesheet_header)",
                    }
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sample_data",
            "description": "Retourne 5 lignes d'exemple d'une vue pour comprendre les vraies valeurs disponibles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Nom de la vue (ex: timesheet_line)",
                    }
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_table_relationships",
            "description": "Retourne les relations entre les vues principales (clés de jointure). Appelle avant une jointure.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_query",
            "description": "Exécute une requête SQL SELECT sur la Silver Layer. Génère automatiquement le SQL adapté. Lecture seule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Requête SQL SELECT complète à exécuter.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]