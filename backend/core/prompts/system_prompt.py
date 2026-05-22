"""
Module: prompts.system_prompt
===========================================
Assembleur du prompt système pour l'agent IA.

Ce module combine les 4 blocs de prompt en un prompt système cohérent:
  1. ROLE_PROMPT     - Identité, langue, protocole de l'agent
  2. RULES_PROMPT    - Règles SQL, jointures validées, auto-correction
  3. SCHEMA_PROMPT   - Schéma métier des tables Synapse
  4. EXAMPLES        - Exemples Few-Shot de questions → requêtes SQL

Architecture:
  - Chaque bloc est dans un fichier séparé pour faciliter la maintenance
  - build_system_prompt() combine les blocs au démarrage
  - SYSTEM_PROMPT est construit une seule fois et réutilisé

"""

from backend.core.prompts.role_prompt import ROLE_PROMPT
from backend.core.prompts.schema_prompt import SCHEMA_PROMPT
from backend.core.prompts.rules_prompt import RULES_PROMPT
from backend.core.training_examples import format_examples_for_prompt


def build_system_prompt() -> str:
    """Construit le prompt système final à partir des 4 blocs modulaires.

    Returns:
        str: Prompt système complet à injecter dans l'agent.

    Structure:
        # [ROLE]\n\n<contenu>
        # [RULES]\n\n<contenu>
        # [SCHEMA]\n\n<contenu>
        # [EXAMPLES]\n\n<contenu>
    """
    blocks = [
        ("ROLE", ROLE_PROMPT),
        ("RULES", RULES_PROMPT),
        ("SCHEMA", SCHEMA_PROMPT),
        ("EXAMPLES", format_examples_for_prompt()),
    ]
    parts = []
    for name, content in blocks:
        parts.append(f"# [{name}]\n\n{content}")
    return "\n\n".join(parts)


# Construit une fois au chargement du module
SYSTEM_PROMPT = build_system_prompt()


if __name__ == "__main__":
    prompt = build_system_prompt()
    print(f"✅ Prompt assemblé")
    print(f"   Caractères : {len(prompt):,}")
    print(f"   Lignes     : {prompt.count(chr(10)):,}")
    for section in prompt.split("# [")[1:]:
        name = section.split("]")[0]
        print(f"   [{name}] → {len(section):,} chars")