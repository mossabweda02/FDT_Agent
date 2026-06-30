"""
Module: pydantic_agent.agent
==========================================
Création et gestion de l'agent Pydantic AI avec Azure OpenAI.

Ce module initialise l'agent IA qui utilise Pydantic AI et Azure OpenAI (GPT-4.1-nano)
pour traiter les questions en langage naturel et les convertir en requêtes SQL sécurisées
contre Azure Synapse.

Classes et fonctions:
    - ask(question): Traite une question utilisateur et retourne une réponse.
    - register_tools(agent): Enregistre les outils SQL disponibles pour l'agent.
    - AgentDeps: Dépendances nécessaires pour l'agent afin de passer des informations contextuelles (ex: auth_header).
"""

import os
import logfire
from dotenv import load_dotenv

load_dotenv()

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncAzureOpenAI
from backend.agent.scrubbing.question_sanitizer import sanitize_question

from backend.core.prompts.system_prompt import SYSTEM_PROMPT
from backend.agent.pydantic_agent.tools import register_tools, AgentDeps

# ─────────────────────────────────────────────────────────────────────────────
# Initialisation du client Azure OpenAI, création de l'agent et enregistrement des outils
# ─────────────────────────────────────────────────────────────────────────────

_client = AsyncAzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-12-01-preview",
)

_model = OpenAIChatModel(
    os.environ["AZURE_OPENAI_DEPLOYMENT"],
    provider=OpenAIProvider(openai_client=_client),
)

agent = Agent(
    model=_model,
    system_prompt=SYSTEM_PROMPT,
    deps_type=AgentDeps,
)
register_tools(agent)


async def ask(question: str, conversation_id=None, history=None, auth_header: str | None = None):
    """
    Exécute une requête utilisateur via l'agent Pydantic AI.

    Args:
        question: Message courant de l'utilisateur.
        conversation_id: Identifiant de la conversation (prévu pour une mémoire persistante).
        history: Historique récent utilisé pour reconstruire le contexte conversationnel.
        auth_header: Jeton d'authentification propagé aux outils Integration Hub.

    Returns:
        Réponse générée par l'agent ou un message d'erreur.
    """
    sq = sanitize_question(question)

    with logfire.span(
        "fdt.agent.ask", # nom du span 
        question_hash=sq.hash, # hash de la question pour identifier les questions similaires
        question_preview=sq.preview, # aperçu de la question pour debug sans exposer des données sensibles
        question_category=sq.category, # catégorie de la question (ex: finance, rh, opérations) pour monitorer les types de questions posées
        question_pii_detected=sq.pii_detected, # Personal Identifiable Information : booléen indiquant si des données sensibles ont été détectées dans la question
    ):
        try:
            # Reconstruit un contexte conversationnel court à partir
            # des derniers échanges. Cette approche est temporaire et
            # sera remplacée par une mémoire persistante.
            context = ""
            if history:
                context = "\n".join(
                    f"{m.role}: {m.content}" for m in history[-6:]
                )

            prompt = f"""
        Contexte récent de la conversation :
        {context}

        Message actuel de l'utilisateur :
        {question}
        """.strip()

            result = await agent.run(
                prompt,
                deps=AgentDeps(auth_header=auth_header),
                )
            return result.output
        except Exception as e:
            return f"❌ Erreur agent : {e}"