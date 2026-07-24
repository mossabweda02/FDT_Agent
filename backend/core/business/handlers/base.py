"""
Module: backend.business.handlers.base
======================================
Ce module fournit une classe de base pour les gestionnaires de scénarios métier. Chaque gestionnaire de scénario doit 
hériter de cette classe et implémenter la méthode `build` pour construire un plan d'exécution spécifique au scénario.
"""

from abc import ABC, abstractmethod

from backend.core.business.business_types import ExecutionPlan


class ScenarioHandler(ABC):
    @abstractmethod
    def build(self, message: str, intent: str | None, scenario: str) -> ExecutionPlan:
        """Construit un plan d'exécution pour un scénario métier."""
        raise NotImplementedError