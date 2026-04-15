"""
core/exceptions.py
===================
Objectif : définir toutes les exceptions personnalisées utilisées dans le projet.

Utilisation actuelle  : aucune (placeholder)
Utilisation future    :
  - Phase RAG         : SchemaNotFoundException, EmbeddingError
  - Phase multi-agent : AgentTimeoutError, ToolCallLimitError
  - Phase prod        : DatabaseConnectionError, QueryBudgetExceeded

  Pourquoi les exceptions ne sont actuellement pas utilisées ?
  - Nous sommes encore en phase de développement rapide (MVP), et la priorité est de construire les fonctionnalités de base et d'entraînement du modèle.
  - La gestion d'exceptions spécifiques sera ajoutée progressivement à mesure que nous intégrons les différentes composantes (agent, outils, base de données) et que nous 
  identifions les points de défaillance potentiels.
  - Nous voulons éviter de complexifier le code avec des exceptions personnalisées avant d'avoir une vision claire des erreurs qui peuvent survenir dans chaque composante.
  - Une fois que nous aurons une base solide et que nous commencerons à intégrer les différentes parties, nous pourrons ajouter des exceptions spécifiques pour améliorer 
  la robustesse et la maintenabilité du code.
"""


# ── Exceptions SQL ────────────────────────────────────────────────

class FDTBaseError(Exception):
    """Exception de base — toutes les exceptions FDT en héritent."""
    pass


class SQLValidationError(FDTBaseError):
    """
    Requête SQL refusée par le validateur.
    Levée par sql_validator.py avant tout envoi à la base.

    Utilisation future :
        raise SQLValidationError("DELETE interdit", query=query)
    """
    def __init__(self, message: str, query: str = ""):
        super().__init__(message)
        self.query = query


class QueryExecutionError(FDTBaseError):
    """
    Erreur lors de l'exécution d'une requête SQL.
    Permet de distinguer erreur SQL vs erreur réseau.

    Utilisation future :
        raise QueryExecutionError("Invalid column", original=e)
    """
    def __init__(self, message: str, original: Exception = None):
        super().__init__(message)
        self.original = original


# ── Exceptions base de données ────────────────────────────────────

class DatabaseConnectionError(FDTBaseError):
    """
    Connexion à Synapse impossible.

    Utilisation future dans connection.py :
        try:
            engine = create_engine(...)
        except Exception as e:
            raise DatabaseConnectionError("Synapse unreachable") from e
    """
    pass


# ── Exceptions agent ──────────────────────────────────────────────

class ToolNotFoundError(FDTBaseError):
    """
    Tool call demandé par l'agent mais non enregistré dans TOOL_FUNCTIONS.

    Utilisation future dans tools_runner.py :
        if fn is None:
            raise ToolNotFoundError(f"Tool '{name}' introuvable")
    """
    def __init__(self, tool_name: str):
        super().__init__(f"Tool '{tool_name}' introuvable.")
        self.tool_name = tool_name


class AgentTimeoutError(FDTBaseError):
    """
    Le run Azure dépasse le timeout configuré.
    À utiliser quand on ajoutera un timeout dans fdt_agent.py.
    """
    pass


# ── Exceptions RAG (Phase 2) ──────────────────────────────────────

class SchemaNotFoundException(FDTBaseError):
    """
    Schéma demandé introuvable dans le vector store.
    Utilisé quand RAG Azure AI Search sera intégré.
    """
    pass


class EmbeddingError(FDTBaseError):
    """
    Erreur lors de la génération d'embeddings.
    Utilisé en Phase 2 avec Azure OpenAI embeddings.
    """
    pass