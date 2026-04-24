"""
agent/fdt_agent.py
===================
ce fichier contient l'agent Azure AI Foundry qui reçoit les questions, gère la boucle d'exécution, appelle les outils et retourne les réponses.
"""

import asyncio
import os
import json
import re
import sys

from dotenv import load_dotenv
from azure.ai.agents.aio import AgentsClient
from azure.ai.agents.models import MessageRole, RunStatus
from azure.identity.aio import DefaultAzureCredential

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.tools_runner import run_tool

load_dotenv()

AGENT_ID = os.getenv("AGENT_ID")
ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")

# ── Messages d'erreur professionnels ──────────────────────────────
FAILED_MESSAGES = {
    "fr": (
        "Je n'ai pas pu obtenir cette information. "
        "Veuillez reformuler votre question ou préciser la période concernée."
    ),
    "en": (
        "I was unable to retrieve this information. "
        "Please rephrase your question or specify the time period."
    ),
}


# ── Parse robuste des arguments du tool call ──────────────────────
def parse_tool_args(raw: str) -> dict:
    """
    Parse les arguments d'un tool call de manière robuste.
    Gère : None, vide, JSON valide, JSON tronqué, double JSON collé.
    """
    if not raw or not raw.strip():
        return {}

    raw = raw.strip()

    # Cas 1 : JSON valide directement
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Cas 2 : extraire le premier objet JSON complet avec regex
    match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Cas 3 : extraire entre le premier { et le dernier }
    start = raw.find('{')
    end   = raw.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Cas 4 : abandon — dict vide (évite le crash)
    print(f"  [WARN] Impossible de parser les args : {raw[:80]}")
    return {}


# ── Fonction principale ────────────────────────────────────────────
async def ask(question: str) -> str:
    """
    Envoie une question à l'agent Azure AI Foundry et retourne la réponse.

    Corrections v2 :
      - La boucle while gère maintenant REQUIRES_ACTION correctement :
        elle soumet les tool outputs et continue à tourner — elle ne return
        plus au milieu de la boucle.
      - RunStatus.FAILED retourne un message professionnel, pas une erreur brute.
    """
    async with DefaultAzureCredential() as credential:
        async with AgentsClient(endpoint=ENDPOINT, credential=credential) as client:

            # 1. Créer un thread et envoyer le message
            thread = await client.threads.create()
            await client.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=question,
            )

            # 2. Lancer le run
            run = await client.runs.create(
                thread_id=thread.id,
                agent_id=AGENT_ID,
            )

            # ── ✅ FIX P1 : boucle corrigée ──────────────────────
            # AVANT (cassé) :
            #   while run.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS]:
            #       ...
            #       if run.status == RunStatus.REQUIRES_ACTION:
            #           ...
            #           return str(result)  ← RETOURNAIT LE RÉSULTAT DU TOOL, PAS LA RÉPONSE
            #
            # APRÈS (correct) :
            #   while inclut REQUIRES_ACTION dans les statuts à surveiller
            #   → soumet les outputs et continue la boucle
            #   → le return se fait uniquement quand status == COMPLETED

            while run.status in (
                RunStatus.QUEUED,
                RunStatus.IN_PROGRESS,
                RunStatus.REQUIRES_ACTION,  # ← ajouté ici
            ):
                await asyncio.sleep(1)
                run = await client.runs.get(
                    thread_id=thread.id,
                    run_id=run.id,
                )

                # Traiter les tool calls
                if run.status == RunStatus.REQUIRES_ACTION:
                    tool_outputs = []
                    for tc in run.required_action.submit_tool_outputs.tool_calls:
                        name     = tc.function.name
                        raw_args = tc.function.arguments or "{}"

                        # ✅ FIX P3 : parse robuste
                        args = parse_tool_args(raw_args)

                        print(f"       [tool] {name}({args})")
                        result = run_tool(name, args)
                        print(f"[tool result]\n{str(result)[:300]}")

                        tool_outputs.append({
                            "tool_call_id": tc.id,
                            "output":       str(result),
                        })

                    # Soumettre TOUS les outputs et continuer la boucle
                    run = await client.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs,
                    )
                    # ← PAS de return ici — on continue la boucle

            # 3. Résultat final
            if run.status == RunStatus.COMPLETED:
                messages = client.messages.list(thread_id=thread.id)
                async for msg in messages:
                    if msg.role == MessageRole.AGENT:
                        for block in msg.content:
                            if hasattr(block, "text"):
                                return block.text.value
                return "Aucune réponse reçue."

            # ✅ FIX P2 : message professionnel pour les échecs
            if run.status == RunStatus.FAILED:
                last_error = getattr(run, "last_error", {})
                print(f"[ERREUR] RunStatus.FAILED — {last_error}")
                lang = "en" if any(c.isascii() and c.isalpha() for c in question[:20]
                                   and not any(w in question.lower()
                                               for w in ["combien", "quels", "heures", "projet"])) \
                       else "fr"
                return FAILED_MESSAGES.get(lang, FAILED_MESSAGES["fr"])

            return f"Statut inattendu : {run.status}"


# ── Interface interactive ──────────────────────────────────────────
async def main():
    print(f"Agent ID : {AGENT_ID}")
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