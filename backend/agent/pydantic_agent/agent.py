"""
Module: pydantic_agent.agent
==========================================
Création et gestion de l'agent Pydantic AI avec Azure OpenAI.

Ce module initialise l'agent IA qui utilise Pydantic AI et Azure OpenAI (GPT-4.1-nano)
pour traiter les questions en langage naturel et les convertir en requêtes SQL sécurisées
contre Azure Synapse.

Classes et fonctions:
    - ask(question): Traite une question utilisateur et retourne une réponse.
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
from backend.agent.pydantic_agent.tools import register_tools

# ─────────────────────────────────────────────────────────────────────────────
# Initialisation du client et du modèle Azure OpenAI
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
)
register_tools(agent)


async def ask(question: str) -> str:
    """Traite une question utilisateur et retourne une réponse synthétisée.

    Args:
        question (str): Question en langage naturel de l'utilisateur.

    Returns:
        str: Réponse synthétisée par l'agent, ou message d'erreur préfixé par ❌.

    Processus:
        1. Sanitise la question (détection PII, hachage, catégorisation)
        2. Crée un span OpenTelemetry pour le monitoring et traçage
        3. Appelle l'agent Pydantic AI avec les outils SQL disponibles
        4. Retourne la réponse en langage naturel ou une erreur

    Raises:
        Exception: Capturée internement, retournée comme message d'erreur.
    """
    sq = sanitize_question(question)

    with logfire.span(
        "fdt.agent.ask", # nom du span 
        question_hash=sq.hash, # hash de la question pour identifier les questions similaires sans stocker le texte brut
        question_preview=sq.preview, # aperçu de la question pour debug sans exposer potentiellement des données sensibles
        question_category=sq.category, # catégorie de la question (ex: finance, rh, opérations) pour monitorer les types de questions posées
        question_pii_detected=sq.pii_detected, # booléen indiquant si des données sensibles ont été détectées dans la question
    ):
        try:
            result = await agent.run(question)
            return result.output
        except Exception as e:
            return f"❌ Erreur agent : {e}"