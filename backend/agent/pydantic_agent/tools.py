"""
Module: backend.agent.pydantic_agent.tools
===========================================
Enregistrement des outils SQL sur l'agent Pydantic AI.

Ce module définit les 6 outils SQL disponibles pour l'agent:
  1. list_tables()              - Liste toutes les vues Synapse
  2. get_database_schema()      - Retourne le schéma simplifié
  3. get_table_relationships()  - Retourne les clés de jointure
  4. describe_table(table_name) - Colonnes exactes d'une vue
  5. get_sample_data(table_name)- 5 lignes d'exemple
  6. execute_query(query)       - Exécute un SELECT T-SQL

Chaque outil est enregistré via le décorateur @agent.tool_plain et délègue à
TOOL_FUNCTIONS de backend.tools.functions_tool pour l'implémentation réelle.
"""

from pydantic_ai import Agent
from backend.tools.functions_tool import TOOL_FUNCTIONS
from backend.tools.sql_validator import validate_sql_query


def register_tools(agent: Agent) -> None:
    """Enregistre les 6 outils SQL sur l'agent Pydantic AI.

    Args:
        agent (Agent): Instance de l'agent Pydantic AI à instrumenter.

    Notes:
        - Les outils sont enregistrés via @agent.tool_plain
        - Chaque outil délègue à TOOL_FUNCTIONS pour l'implémentation
        - execute_query valide la requête avant exécution via sql_validator
    """

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