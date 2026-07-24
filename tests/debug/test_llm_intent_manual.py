import asyncio

from backend.agent.pydantic_agent.agent import (
    call_azure_openai_for_intent,
)
from backend.core.business.llm_intent_classifier import (
    classify_intent_with_llm,
)


async def main():
    messages = [
        "Fabrique-moi une feuille pour demain",
        "Genere une feille de temp pour lundi",
        "Je veux mettre 2 heures sur Nova demain",
        "Combien d'heures ai-je cette semaine ?",
    ]

    for message in messages:
        result = await classify_intent_with_llm(
            message,
            llm_call=call_azure_openai_for_intent,
        )

        print(message)
        print(result)
        print("-" * 60)


asyncio.run(main())