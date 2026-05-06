"""
agent/pydantic_agent/tools.py
===================
ce fichier contient les outils de l'agent qui utilise l'api openai et pydantic-ai pour répondre aux questions
"""

from pydantic_ai import Agent
from tools.functions_tools import TOOL_FUNCTIONS
from tools.sql_validator import validate_sql_query


def register_tools(agent: Agent) -> None:

    @agent.tool_plain
    def list_tables() -> str:
        """Liste toutes les tables/vues de la Silver Layer."""
        return TOOL_FUNCTIONS["list_tables"]()

    @agent.tool_plain
    def get_database_schema() -> str:
        """Retourne le schéma simplifié des tables. Appeler EN PREMIER."""
        return TOOL_FUNCTIONS["get_database_schema"]()

    @agent.tool_plain
    def get_table_relationships() -> str:
        """Retourne les clés de jointure et la requête canonique."""
        return TOOL_FUNCTIONS["get_table_relationships"]()

    @agent.tool_plain
    def describe_table(table_name: str) -> str:
        """Retourne les colonnes exactes et types d'une table."""
        return TOOL_FUNCTIONS["describe_table"](table_name=table_name)

    @agent.tool_plain
    def get_sample_data(table_name: str) -> str:
        """Retourne 5 vraies lignes d'une table."""
        return TOOL_FUNCTIONS["get_sample_data"](table_name=table_name)

    @agent.tool_plain
    def execute_query(query: str) -> str:
        """Exécute un SELECT T-SQL en lecture seule sur Azure Synapse."""
        ok, err = validate_sql_query(query)
        if not ok:
            import json
            return json.dumps({"error": err, "rows": [], "row_count": 0})
        return TOOL_FUNCTIONS["execute_query"](query=query)