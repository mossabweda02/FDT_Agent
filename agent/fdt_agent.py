import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from azure.ai.agents.aio import AgentsClient
from azure.ai.agents.models import (
    ThreadMessageOptions,
    MessageRole,
    RunStatus,
)
from azure.identity.aio import DefaultAzureCredential

from tools.tools_runner import run_tool

load_dotenv()

# ── Validation ────────────────────────────────────────────────────
REQUIRED = [
    "AZURE_AI_PROJECT_ENDPOINT",
    "AGENT_ID",
]

for v in REQUIRED:
    if not os.getenv(v):
        print(f"[ERREUR] Variable manquante dans .env : {v}")
        sys.exit(1)

AGENT_ID = os.environ["AGENT_ID"]
ENDPOINT = os.environ["AZURE_AI_PROJECT_ENDPOINT"]


# ── Envoi d'une question à l'agent ────────────────────────────────
async def ask(question: str) -> str:
    async with DefaultAzureCredential() as credential:
        async with AgentsClient(
            endpoint=ENDPOINT,
            credential=credential,
        ) as client:

            # 1. Créer un thread
            thread = await client.threads.create()

            # 2. Envoyer le message dans le thread
            await client.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=question,
            )

            # 3. Lancer le run
            run = await client.runs.create(
                thread_id=thread.id,
                agent_id=AGENT_ID,
            )

            # 4. Boucle de polling
            while run.status in (
                RunStatus.QUEUED,
                RunStatus.IN_PROGRESS,
                RunStatus.REQUIRES_ACTION,
            ):
                await asyncio.sleep(1)
                run = await client.runs.get(
                    thread_id=thread.id,
                    run_id=run.id,
                )

                # Tool calls
                if run.status == RunStatus.REQUIRES_ACTION:
                    tool_outputs = []
                    for tc in run.required_action.submit_tool_outputs.tool_calls:
                        name = tc.function.name
                        args = json.loads(tc.function.arguments or "{}")
                        print(f"     [tool] {name}({args})")
                        result = run_tool(name, args)
                        tool_outputs.append({
                            "tool_call_id": tc.id,
                            "output": str(result),
                        })

                    run = await client.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs,
                    )

            # 5. Récupérer la réponse finale
            if run.status == RunStatus.COMPLETED:
                messages = client.messages.list(thread_id=thread.id)
                async for msg in messages:
                    if msg.role == MessageRole.AGENT:
                        for block in msg.content:
                            if hasattr(block, "text"):
                                return block.text.value
                return "[ERREUR] Aucun message assistant trouvé."

            if run.status == RunStatus.FAILED:
                return f"[ERREUR] Run échoué : {getattr(run, 'last_error', 'inconnu')}"

            return f"[ERREUR] Statut inattendu : {run.status}"


# ── Boucle interactive ────────────────────────────────────────────
async def main():
    print(f"\nAgent ID : {AGENT_ID}")
    print("Tape 'exit' pour quitter.\n")

    while True:
        try:
            question = input("Vous : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir !")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit", "q"):
            print("Au revoir !")
            break

        print("  Traitement en cours...")
        response = await ask(question)
        print(f"\nAgent : {response}\n")


if __name__ == "__main__":
    asyncio.run(main())