# LEGACY — Azure AI Foundry Agent
# Non utilisé depuis migration Pydantic AI (voir agent/pydantic_agent/).
# Conserver pour rollback ou comparaison.

"""
agent/create_agent.py
===================
ce fichier crée un agent Azure AI Foundry avec des outils pour interagir avec une base de données SQL.
il s'exécute une seule fois 
"""

import os
from dotenv import load_dotenv
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential
from backend.core.prompts import SYSTEM_PROMPT

load_dotenv()

# Endpoint de l'Azure AI Foundry
endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

# ────────────────────────────────────────────────────────────────────
# Définition des outils que l'agent 
# ────────────────────────────────────────────────────────────────────
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "Liste toutes les tables disponibles",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_table",
            "description": "Retourne les colonnes d'une table",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"}
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sample_data",
            "description": "Retourne quelques lignes d'exemple d'une table",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"}
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_table_relationships",
            "description": "Retourne les relations entre les tables",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_query",
            "description": "Execute une requête SQL SELECT",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"],
            },
        },
    },
]

# ────────────────────────────────────────────────────────────────────
# Création de l'agent 
# ────────────────────────────────────────────────────────────────────
with AgentsClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
) as client:

    agent = client.create_agent(
        model="gpt-4.1-nano",
        name="FDT SQL Agent",
        instructions=SYSTEM_PROMPT,
        tools=tools,
    )

    print("Agent créé :", agent.id)