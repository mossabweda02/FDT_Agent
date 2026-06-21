"""
Module: backend.agent.pydantic_agent.tools
===========================================
Enregistrement des outils SQL sur l'agent Pydantic AI.

Ce module définit les 2 types d'outils :
- Functions_tools : accès en lecture aux métadonnées et données de la Silver Layer.
- Hub_functions : accès en lecture/écriture aux projets et feuilles de temps de l'Integration Hub (Operate).

Chaque outil est décoré avec @agent.tool_plain pour être reconnu par Pydantic AI.
Les fonctions d'implémentation sont déléguées à TOOL_FUNCTIONS et HUB_FUNCTIONS,
respectivement, pour séparer la logique métier de l'interface agent.
"""

from pydantic_ai import Agent
from backend.tools.functions_tool import TOOL_FUNCTIONS
from backend.tools.sql_validator import validate_sql_query
from backend.tools.hub_functions import HUB_FUNCTIONS

def register_tools(agent: Agent) -> None:
    """Enregistre les 6 outils SQL sur l'agent Pydantic AI.

    Args:
        agent (Agent): Instance de l'agent Pydantic AI à instrumenter.

    Notes:
        - Les outils sont enregistrés via @agent.tool_plain
        - Chaque outil délègue à TOOL_FUNCTIONS pour l'implémentation
        - execute_query valide la requête avant exécution via sql_validator
    """

# ── Outils SQL : accès en lecture aux métadonnées et données de la Silver Layer ──
    @agent.tool_plain
    def list_tables() -> str:
        """Liste toutes les tables/vues de la Silver Layer."""
        return TOOL_FUNCTIONS["list_tables"]()

    @agent.tool_plain
    def get_database_schema() -> str:
        """Retourne le schéma simplifié des tables. Appeler EN PREMIER."""
        return TOOL_FUNCTIONS["get_database_schema"]()

    @agent.tool_plain
    def get_table_relationships() -> str:
        """Retourne les clés de jointure et la requête canonique."""
        return TOOL_FUNCTIONS["get_table_relationships"]()

    @agent.tool_plain
    def describe_table(table_name: str) -> str:
        """Retourne les colonnes exactes et types d'une table."""
        return TOOL_FUNCTIONS["describe_table"](table_name=table_name)

    @agent.tool_plain
    def get_sample_data(table_name: str) -> str:
        """Retourne 5 vraies lignes d'une table."""
        return TOOL_FUNCTIONS["get_sample_data"](table_name=table_name)

    @agent.tool_plain
    def execute_query(query: str) -> str:
        """Exécute un SELECT T-SQL en lecture seule sur Azure Synapse."""
        ok, err = validate_sql_query(query)
        if not ok:
            import json
            return json.dumps({"error": err, "rows": [], "row_count": 0})
        return TOOL_FUNCTIONS["execute_query"](query=query)
    
    @agent.tool_plain
    def get_auth_runtime_status() -> str:
        """Retourne le mode d'authentification Hub actuel sans exposer de secrets."""
        return TOOL_FUNCTIONS["get_auth_runtime_status"]()
    
    # ── Outils Integration Hub (Operate) : lecture + écriture des heures (Actions) ──
 
    # ──────────── Projects ──────────── 
    @agent.tool_plain
    def hub_list_projects(limit: int = 20) -> str:
        """Liste les projets Operate via l'Integration Hub."""

        return HUB_FUNCTIONS["list_projects"](limit=limit)
 
    @agent.tool_plain
    def hub_get_project(proj_id: str) -> str:
        """Détails d'un projet par projId."""

        return HUB_FUNCTIONS["get_project"](proj_id=proj_id)  

    # ──────────── Tasks ──────────── 
    @agent.tool_plain
    def hub_get_project_tasks(proj_id: str) -> str:
        """Liste les tâches d'un projet par projId."""

        return HUB_FUNCTIONS["get_project_tasks"](proj_id=proj_id)
 
    @agent.tool_plain
    def hub_get_task(activity_number: str) -> str:
        """Détails d'une tâche par activity_number."""

        return HUB_FUNCTIONS["get_task"](activity_number=activity_number)
    
    @agent.tool_plain
    def hub_list_tasks(limit: int = 20) -> str:
        """Liste les tâches Operate via l'Integration Hub."""

        return HUB_FUNCTIONS["list_tasks"](limit=limit)
    
    # ──────────── Resources ──────────── 
    @agent.tool_plain
    def hub_get_resource(resource_id: str) -> str:
        """Détails d'une ressource par resourceId."""

        return HUB_FUNCTIONS["get_resource"](resource_id=resource_id)
    
    @agent.tool_plain
    def find_resource(search: str) -> str:
        """Recherche une ressource par fragment (ex. RES-29 ou un nom)."""

        return HUB_FUNCTIONS["find_resource"](search=search)
    
    @agent.tool_plain
    def hub_find_resource_by_name(name: str, first_name: str | None = None, last_name: str | None = None) -> str:
        """Recherche une ressource par nom complet, nom ou prénom."""

        return HUB_FUNCTIONS["find_resource_by_name"](name=name, first_name=first_name, last_name=last_name)
    
    @agent.tool_plain
    def hub_find_resource_by_email(email: str) -> str:
        """Recherche une ressource par email."""

        return HUB_FUNCTIONS["find_resource_by_email"](email=email)
    
    # ──────────── Catégories de taches ────────────
    @agent.tool_plain
    def hub_get_timesheet_categories(project_id: str, resource_id: str) -> str:
        """Catégories de saisie valides pour un projet + une ressource."""

        return HUB_FUNCTIONS["get_timesheet_categories"](

            project_id=project_id, resource_id=resource_id)
 
    # ──────────── Timesheet Header ────────────
    @agent.tool_plain
    def hub_create_timesheet(resource_id: str, period_start: str | None = None,
                             description: str = "") -> str:
        """Crée une feuille de temps hebdomadaire pour une ressource."""

        return HUB_FUNCTIONS["create_timesheet"](
            resource_id=resource_id, period_start=period_start, description=description)
 
    @agent.tool_plain
    def hub_list_timesheets(resource_id: str, limit: int = 20) -> str:
        """Liste les feuilles de temps d'une ressource."""

        return HUB_FUNCTIONS["list_timesheets"](resource_id=resource_id, limit=limit)
    
    @agent.tool_plain
    def hub_get_timesheet(timesheet_nbr: str, resource_id: str | None = None) -> str:
        """Détails d'une feuille de temps par timesheetId."""

        return HUB_FUNCTIONS["get_timesheet"](timesheet_nbr=timesheet_nbr, resource_id=resource_id)
    
    @agent.tool_plain
    def hub_update_timesheet(timesheet_nbr: str, description: str = "", period_id: str = None, resource_id: str | None = None) -> str:
        """Met à jour une feuille de temps existante."""

        return HUB_FUNCTIONS["update_timesheet"](
            timesheet_nbr=timesheet_nbr, description=description, period_id=period_id, resource_id=resource_id)
    
    @agent.tool_plain
    def hub_delete_timesheet(timesheet_nbr: str, resource_id: str) -> str:
        """Supprime une feuille de temps existante."""

        return HUB_FUNCTIONS["delete_timesheet"](timesheet_nbr=timesheet_nbr, resource_id=resource_id)
    
    # ──────────── Timesheet Lines ────────────
    @agent.tool_plain
    def get_timesheet_lines(timesheet_nbr: str,proj_id:str , activity_number: str, date: str, category_id: str | None = None) -> str:
        """Liste les lignes d'heures d'une feuille de temps par timesheetId."""

        return HUB_FUNCTIONS["get_timesheet_lines"](
            timesheet_nbr=timesheet_nbr, proj_id=proj_id, activity_number=activity_number,
            date=date, category_id=category_id)

    @agent.tool_plain
    def hub_create_timesheet_line(timesheet_nbr: str, proj_id: str, activity_number: str,
                                  category_id: str, resource_id: str, date: str,
                                  qty: float, internal_note: str = "", external_note: str = "") -> str:
        """Ajoute une ligne d'heures à une feuille de temps existante.
        À n'appeler qu'après confirmation explicite de l'utilisateur."""

        return HUB_FUNCTIONS["create_timesheet_line"](
            timesheet_nbr=timesheet_nbr, proj_id=proj_id, activity_number=activity_number,
            category_id=category_id, resource_id=resource_id, date=date,
            qty=qty, internal_note=internal_note, external_note=external_note)
    
    @agent.tool_plain
    def update_timesheet_line(rec_id: str, timesheet_nbr: str, proj_id: str, activity_number: str,
                                  category_id: str, resource_id: str, date: str,
                                  qty: float, internal_note: str = "", external_note: str = "") -> str:
        """Met à jour une ligne d'heures existante dans une feuille de temps.
        À n'appeler qu'après confirmation explicite de l'utilisateur."""

        return HUB_FUNCTIONS["update_timesheet_line"](
            rec_id=rec_id, timesheet_nbr=timesheet_nbr, proj_id=proj_id, activity_number=activity_number,
            category_id=category_id, resource_id=resource_id, date=date,
            qty=qty, internal_note=internal_note, external_note=external_note)
    
    @agent.tool_plain
    def delete_timesheet_line(rec_id: str) -> str:
        """Supprime une ligne d'heures existante dans une feuille de temps.
        À n'appeler qu'après confirmation explicite de l'utilisateur."""

        return HUB_FUNCTIONS["delete_timesheet_line"](rec_id=rec_id)

    # ──────────── Livrables ────────────
    @agent.tool_plain
    def hub_get_project_deliverables(proj_id: str) -> str:
        """Liste les livrables d'un projet par projId."""

        return HUB_FUNCTIONS["get_project_deliverables"](proj_id=proj_id)
    
    @agent.tool_plain
    def get_task_deliverables(activity_number: str) -> str:
        """Liste les livrables d'une tâche par activityNumber."""

        return HUB_FUNCTIONS["get_task_deliverables"](activity_number=activity_number)
    
    # ──────────── Periode ────────────
    @agent.tool_plain
    def hub_get_timesheet_periods(resource_id: str, open_only: bool = True) -> str:
        """Liste les périodes de saisie de temps valides pour une ressource."""

        return HUB_FUNCTIONS["get_timesheet_periods"](resource_id=resource_id, open_only=open_only)
    
    @agent.tool_plain
    def hub_get_timesheet_period_by_date(date: str, resource_id: str) -> str:
        """Retourne la période de saisie de temps valide pour une date et ressource."""

        return HUB_FUNCTIONS["get_timesheet_period_by_date"](date=date, resource_id=resource_id)

    # @agent.tool_plain
    # def hub_create_time_entry(resource_id: str, project_id: str, activity_number: str,
    #                           qty: float, start_date: str, note: str = "") -> str:
    #     """Enregistre des heures (saisie de temps). Date = AAAA-MM-JJ, qty en heures (>0).
    #     À n'appeler qu'après confirmation explicite de l'utilisateur."""

    #     return HUB_FUNCTIONS["create_time_entry"](
    #         resource_id=resource_id, project_id=project_id,
    #         activity_number=activity_number, qty=qty, start_date=start_date, note=note)