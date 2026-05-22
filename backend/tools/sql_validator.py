"""
Module: tools.sql_validator
====================================
Validateur SQL pour prévenir les opérations dangereuses.

Ce module implémente une couche de sécurité locale pour valider toute requête SQL
avant envoi à Azure Synapse. Elle empêche:
  - Les opérations d'écriture (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE)
  - Les requêtes multi-statements (plusieurs ; )
  - Les commentaires SQL (-- et /* */)
  - Les requêtes ne commençant pas par SELECT ou WITH

Avantages:
  - Sécurité: Empêche les mutations même si l'agent hallucine
  - Performance: Validation locale instantanée (pas de latence réseau)
  - Coût: Évite les erreurs SQL répétées consommant des ressources

Fonctions publiques:
  - validate_sql_query(query): Valide une requête avant exécution
  - sanitize_query_for_logging(query): Nettoie pour les logs
"""

from typing import Tuple, Optional

class SQLValidationError(Exception):
    """ Exception personnalisée pour les erreurs de validation SQL. """
    pass


def validate_sql_query(query: str) -> Tuple[bool, Optional[str]]:
    """Valide une requête SQL en vérifiant les opérations interdites et les patterns d'injection."""
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


def sanitize_query_for_logging(query: str, max_length: int = 200) -> str:
    """Nettoie et tronque la requête SQL pour les logs, afin d'éviter 
    d'exposer des données sensibles tout en gardant un aperçu pour le debug."""
    clean = " ".join(query.strip().split())
    return clean[:max_length]