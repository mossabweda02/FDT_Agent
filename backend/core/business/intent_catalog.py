"""
Module: backend.business.intent_catalog
======================================
Catalogue des intentions métier supportées par FDT Agent.

Ce fichier sert de référence pour les intentions métier que l'agent peut reconnaître et traiter.
Chaque intention est associée à une description, un indicateur d'action d'écriture et un outil spécifique pour l'exécution.
"""

BUSINESS_INTENTS = {
    "CREATE_TIMESHEET": {
        "description": "Créer une feuille de temps.",
        "write_action": True,
        "tool": "hub_create_timesheet",
    },
    "ADD_TIME_ENTRY": {
        "description": "Ajouter une seule ligne de temps.",
        "write_action": True,
        "tool": "hub_create_timesheet_line",
    },
    "ADD_MULTIPLE_TIME_ENTRIES": {
        "description": "Ajouter plusieurs lignes de temps.",
        "write_action": True,
        "tool": "hub_create_timesheet_line",
    },
    "UPDATE_TIME_ENTRY": {
        "description": "Modifier une ligne de temps existante.",
        "write_action": True,
        "tool": "hub_update_timesheet_line",
    },
    "DELETE_TIME_ENTRY": {
        "description": "Supprimer une ligne de temps existante.",
        "write_action": True,
        "tool": "hub_delete_timesheet_line",
    },
    "CONSULT_TIMESHEET": {
        "description": "Consulter une feuille ou des lignes de temps.",
        "write_action": False,
        "tool": "hub_get_timesheet",
    },
    "CONFIRM_ACTION": {
        "description": "Confirmer une action préparée.",
        "write_action": False,
        "tool": None,
    },
    "CANCEL_ACTION": {
        "description": "Annuler une action préparée.",
        "write_action": False,
        "tool": None,
    },
}