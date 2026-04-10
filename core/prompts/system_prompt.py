"""
core/prompts/system_prompt.py
==============================
Assembleur final — construit SYSTEM_PROMPT depuis les 4 blocs.

    system_prompt = role + schema + rules + examples
Chaque bloc est dans un fichier séparé pour faciliter la maintenance.
"""

from core.prompts.role_prompt   import ROLE_PROMPT
from core.prompts.schema_prompt import SCHEMA_PROMPT
from core.prompts.rules_prompt  import RULES_PROMPT
from core.training_examples     import format_examples_for_prompt


def build_system_prompt() -> str:
    """
    Assemble les 4 blocs en un seul SYSTEM_PROMPT.
    Appelé par update_agent.py à chaque mise à jour Azure.
    """
    blocks = [
        ("ROLE",     ROLE_PROMPT),
        ("SCHEMA",   SCHEMA_PROMPT),
        ("RULES",    RULES_PROMPT),
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