"""
agent/pydantic_agent/agent.py
===================
ce fichier contient l'agent qui utilise l'api openai et pydantic-ai pour répondre aux questions
"""

import os
from dotenv import load_dotenv
load_dotenv()

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncAzureOpenAI

from core.prompts.system_prompt import SYSTEM_PROMPT
from agent.pydantic_agent.tools import register_tools

_client = AsyncAzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-12-01-preview",
)

_model = OpenAIModel(
    os.environ["AZURE_OPENAI_DEPLOYMENT"],
    provider=OpenAIProvider(openai_client=_client),
)

agent = Agent(
    model=_model,
    system_prompt=SYSTEM_PROMPT, 
)

register_tools(agent)


async def ask(question: str) -> str:
    try:
        result = await agent.run(question)
        return result.output 
    except Exception as e:
        return f"❌ Erreur agent : {e}"