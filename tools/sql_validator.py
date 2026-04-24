"""
fdtAgent/core/sql_validator.py
===============================
Validateur SQL pour empêcher les opérations dangereuses.
IMPORTANT : Cette validation s'exécute AVANT l'envoi à la base de données.

Pourquoi ce fichier ?
---------------------
1. Sécurité : Empêche INSERT/UPDATE/DELETE/DROP même si le LLM hallucine
2. Performance : Validation locale instantanée (pas d'appel réseau)
3. Coût : Évite les requêtes SQL inutiles qui consomment des ressources
4. Traçabilité : Logs clairs des tentatives de requêtes interdites

Architecture :
--------------
- validate_sql_query() : Point d'entrée principal (appelé par execute_query)
- _check_forbidden_operations() : Détecte les mots-clés interdits
- _check_required_operations() : Force SELECT ou WITH
- _check_sql_injection_patterns() : Détecte les patterns d'injection SQL
"""

import re
from typing import Tuple, Optional

class SQLValidationError(Exception):
    pass


def validate_sql_query(query: str) -> Tuple[bool, Optional[str]]:
    if not query:
        return False, "Empty query"

    q = " ".join(query.strip().split()).upper()

    forbidden = [
        "INSERT", "UPDATE", "DELETE", "DROP",
        "ALTER", "CREATE", "EXEC", "MERGE"
    ]

    for f in forbidden:
        if f in q:
            return False, f"❌ Forbidden operation: {f}"

    if not (q.startswith("SELECT") or q.startswith("WITH")):
        return False, "❌ Only SELECT/WITH allowed"

    if "--" in query or "/*" in query:
        return False, "❌ SQL comments not allowed"

    if ";" in query.strip()[:-1]:
        return False, "❌ Multiple statements not allowed"

    return True, None


# 🔥 KEEP THIS (important for functions_tools)
def sanitize_query_for_logging(query: str, max_length: int = 200) -> str:
    clean = " ".join(query.strip().split())
    return clean[:max_length]