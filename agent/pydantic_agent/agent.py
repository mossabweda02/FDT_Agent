"""
agent/pydantic_agent/agent.py
===================
ce fichier contient l'agent qui utilise l'api openai et pydantic-ai pour répondre aux questions
"""

import os
import logfire
from dotenv import load_dotenv
load_dotenv()

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncAzureOpenAI
from agent.question_sanitizer import sanitize_question

from core.prompts.system_prompt import SYSTEM_PROMPT
from agent.pydantic_agent.tools import register_tools

# Initialisation du client Azure OpenAI
_client = AsyncAzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-12-01-preview",
)

# Initialisation du model OpenAI 
_model = OpenAIModel(
    os.environ["AZURE_OPENAI_DEPLOYMENT"],
    provider=OpenAIProvider(openai_client=_client),
)

# Initialisation de l'agent pydantic-ai avec le system prompt et les outils
agent = Agent(
    model=_model,
    system_prompt=SYSTEM_PROMPT, 
)
register_tools(agent)

# Fonction pour répondre aux questions 
async def ask(question: str) -> str:
    sq = sanitize_question(question)

    # Masquage des données sensibles de la question
    # Hash unique pour identifier la question
    # Aperçu de la question
    # Catégorie de la question
    # Détection des données sensibles
    with logfire.span(
        "fdt.agent.ask",
        question_hash=sq.hash,
        question_preview=sq.preview,
        question_category=sq.category,
        question_pii_detected=sq.pii_detected,
    ):
        try:
            result = await agent.run(question)
            return result.output 
        except Exception as e:
            return f"❌ Erreur agent : {e}"