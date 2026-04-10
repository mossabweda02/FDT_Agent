"""
Définitions des 6 outils exposés à l'agent Azure.
Synchronisé avec TOOL_FUNCTIONS dans functions_tools.py.
"""

TOOLS_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_database_schema",
            "description": (
                "Retourne le schéma simplifié des tables principales SANS appel SQL. "
                "Appeler EN PREMIER pour un aperçu instantané."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "Liste toutes les vues disponibles dans la Silver Layer.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_table",
            "description": (
                "Retourne les colonnes EXACTES et types d'une vue. "
                "Appeler avant execute_query pour éviter les colonnes inexistantes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Nom exact de la vue (ex: timesheet_header)",
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
            "description": (
                "Retourne 5 vraies lignes d'une vue. "
                "Appeler pour vérifier les valeurs réelles de APPROVALSTATUS "
                "et les formats de date avant de filtrer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Nom exact de la vue",
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
            "description": (
                "Retourne les clés de jointure vérifiées et une requête canonique. "
                "Appeler avant toute jointure SQL."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_query",
            "description": (
                "Exécute un SELECT sur la Silver Layer. Lecture seule. "
                "La réponse JSON contient 'hint' si erreur ou 0 résultats. "
                "Lire le hint et corriger avant de réessayer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Requête SQL SELECT complète.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]