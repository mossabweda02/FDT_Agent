"""
fdtAgent/core/exceptions.py
============================
Exceptions personnalisées de l'agent.
"""


class OutOfContextError(Exception):
    """Question hors du contexte timesheet Metam."""
    pass


class DatabaseConnectionError(Exception):
    """Erreur de connexion à Synapse."""
    pass


class InvalidQueryError(Exception):
    """Requête SQL non autorisée (non SELECT)."""
    pass