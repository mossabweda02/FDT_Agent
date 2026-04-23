"""
agent/update_agent.py
======================
Pousse le SYSTEM_PROMPT et les TOOLS vers Azure AI Foundry.
OBLIGATOIRE après chaque modification des fichiers prompts/.

Usage :
    python -m agent.update_agent                    # version courante
    python -m agent.update_agent --force            # forcer même si pas de changement
    python -m agent.update_agent --version v1.2     # changer la version
    python -m agent.update_agent --name "Chronos-FDT v2.0"  # nom complet custom
"""

import asyncio
import hashlib
import importlib
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from azure.ai.agents.aio import AgentsClient
from azure.identity.aio import DefaultAzureCredential

# ── Forcer le rechargement des modules (évite le cache Python) ────
import core.prompts.role_prompt
import core.prompts.schema_prompt
import core.prompts.rules_prompt
import core.prompts.system_prompt
import core.prompts.tools_definitions
import core.training_examples

for mod in [
    core.training_examples,
    core.prompts.role_prompt,
    core.prompts.schema_prompt,
    core.prompts.rules_prompt,
    core.prompts.system_prompt,
    core.prompts.tools_definitions,
]:
    importlib.reload(mod)

from core.prompts.system_prompt    import build_system_prompt
from core.prompts.tools_definitions import TOOLS_DEFINITIONS

load_dotenv()

# ── Validation ────────────────────────────────────────────────────
for v in ["AZURE_AI_PROJECT_ENDPOINT", "AGENT_ID"]:
    if not os.getenv(v):
        print(f"[ERREUR] Variable manquante dans .env : {v}")
        sys.exit(1)

AGENT_ID = os.environ["AGENT_ID"]
ENDPOINT = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

# ── Versioning ────────────────────────────────────────────────────
AGENT_BASE_NAME = "FDT-Agent"   # Nom du agent sans la version, utilisé pour construire le nom final
CURRENT_VERSION = "v1.1"          # Version actuelle, à incrémenter manuellement à chaque changement significatif

HASH_FILE    = ".prompt_hash" # Fichier local pour stocker le hash du prompt envoyé à Azure
VERSION_FILE = ".agent_version" # Fichier local pour stocker le nom de la dernière version envoyée 


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:8]


def _load(path: str, default: str = "") -> str:
    try:
        return open(path).read().strip()
    except FileNotFoundError:
        return default


def _save(path: str, content: str):
    open(path, "w").write(content)


def _build_name(version: str) -> str:
    """Construit le nom complet de l'agent."""
    return f"{AGENT_BASE_NAME} {version}"


def _parse_args() -> dict:
    """Parse les arguments CLI."""
    args = {"force": False, "version": None, "name": None}
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--force":
            args["force"] = True
        elif arg == "--version" and i + 1 < len(sys.argv):
            args["version"] = sys.argv[i + 1]
            i += 1
        elif arg == "--name" and i + 1 < len(sys.argv):
            args["name"] = sys.argv[i + 1]
            i += 1
        i += 1
    return args


async def update():
    cli = _parse_args()

    # Déterminer le nom final de l'agent
    if cli["name"]:
        agent_name = cli["name"]
    elif cli["version"]:
        agent_name = _build_name(cli["version"])
    else:
        agent_name = _build_name(CURRENT_VERSION)

    # Construire le prompt
    prompt      = build_system_prompt()
    new_hash    = _hash(prompt)
    old_hash    = _load(HASH_FILE)
    last_name   = _load(VERSION_FILE, "(inconnu)")
    timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Affichage ─────────────────────────────────────────────────
    print(f"\n{'='*62}")
    print(f"  UPDATE AGENT — {agent_name}")
    print(f"{'='*62}")
    print(f"  Agent ID    : {AGENT_ID}")
    print(f"  Nom actuel  : {last_name}")
    print(f"  Nouveau nom : {agent_name}")
    print(f"  Prompt      : {len(prompt):,} caractères")
    print(f"  Hash actuel : {new_hash}")
    print(f"  Hash Azure  : {old_hash or '(premier envoi)'}")
    print(f"  Tools       : {len(TOOLS_DEFINITIONS)} outils")
    print(f"  Date        : {timestamp}")
    print(f"{'='*62}")

    # ── Vérification changement ───────────────────────────────────
    if new_hash == old_hash and last_name == agent_name and not cli["force"]:
        print(f"\n  ⚠️  Prompt identique + nom inchangé.")
        print(f"  Aucune mise à jour nécessaire.")
        print(f"  → Utiliser --force pour forcer l'envoi.")
        print(f"{'='*62}\n")
        return

    # ── Envoi vers Azure ──────────────────────────────────────────
    print(f"\n  Envoi vers Azure AI Foundry...")

    async with DefaultAzureCredential() as credential:
        async with AgentsClient(endpoint=ENDPOINT, credential=credential) as client:
            await client.update_agent(
                agent_id=AGENT_ID,
                name=agent_name,
                instructions=prompt,
                tools=TOOLS_DEFINITIONS,
            )

    # Sauvegarder hash et nom
    _save(HASH_FILE, new_hash)
    _save(VERSION_FILE, agent_name)

    # ── Résumé ────────────────────────────────────────────────────
    print(f"\n  ✅ Agent mis à jour avec succès !")
    print(f"  Nom    : {agent_name}")
    print(f"  Hash   : {new_hash}")
    print(f"  Outils :")
    for t in TOOLS_DEFINITIONS:
        print(f"    - {t['function']['name']}")
    print(f"\n  Prochaine étape :")
    print(f"    python check_corrections.py")
    print(f"    python test_agent.py")
    print(f"{'='*62}\n")


if __name__ == "__main__":
    asyncio.run(update())