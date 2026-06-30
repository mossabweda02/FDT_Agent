"""
Module: backend.agent.pydantic_agent.tools
===========================================
Enregistrement des outils SQL et Integration Hub sur l'agent Pydantic AI.

Ce module définit 2 familles d'outils :
- Functions_tools : accès en lecture aux métadonnées et données de la Silver Layer.
- Hub_functions : accès en lecture/écriture aux projets, ressources, tâches,
  livrables et feuilles de temps de l'Integration Hub (Operate).

Les outils SQL simples sont décorés avec @agent.tool_plain.
Les outils Hub qui ont besoin du contexte d'exécution sont décorés avec @agent.tool
afin de recevoir RunContext[AgentDeps] et de transmettre auth_header aux fonctions Hub.

Les fonctions d'implémentation sont déléguées à TOOL_FUNCTIONS et HUB_FUNCTIONS,
respectivement, pour séparer la logique métier de l'interface agent.
"""

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from backend.tools.functions_tool import TOOL_FUNCTIONS
from backend.tools.sql_validator import validate_sql_query
from backend.tools.hub_functions import HUB_FUNCTIONS


@dataclass
class AgentDeps:
    """Dépendances injectées dans les outils contextualisés de l'agent.

    Attributes:
        auth_header: En-tête d'autorisation transmis aux appels Integration Hub.
            Il peut être None lorsque l'authentification n'est pas disponible
            ou lorsqu'un outil ne nécessite pas d'appel Hub authentifié.
    """

    auth_header: str | None = None


def register_tools(agent: Agent) -> None:
    """Enregistre les outils SQL et Integration Hub sur l'agent Pydantic AI.

    Les outils SQL utilisent `tool_plain` car ils ne nécessitent pas de
    contexte runtime. Les outils Hub utilisent `tool` afin de recevoir
    `RunContext[AgentDeps]` et propager le header d'authentification.
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
    @agent.tool
    def hub_list_projects(ctx: RunContext[AgentDeps], limit: int = 20) -> str:
        """Liste les projets Operate via l'Integration Hub."""
        return HUB_FUNCTIONS["list_projects"](
            limit=limit,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_get_project(ctx: RunContext[AgentDeps], proj_id: str) -> str:
        """Détails d'un projet par projId."""
        return HUB_FUNCTIONS["get_project"](
            proj_id=proj_id,
            auth_header=ctx.deps.auth_header,
        )

    # ──────────── Tasks ────────────
    @agent.tool
    def hub_get_project_tasks(ctx: RunContext[AgentDeps], proj_id: str) -> str:
        """Liste les tâches d'un projet par projId."""
        return HUB_FUNCTIONS["get_project_tasks"](
            proj_id=proj_id,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_get_task(ctx: RunContext[AgentDeps], activity_number: str) -> str:
        """Détails d'une tâche par activity_number."""
        return HUB_FUNCTIONS["get_task"](
            activity_number=activity_number,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_list_tasks(ctx: RunContext[AgentDeps], limit: int = 20) -> str:
        """Liste les tâches Operate via l'Integration Hub."""
        return HUB_FUNCTIONS["list_tasks"](
            limit=limit,
            auth_header=ctx.deps.auth_header,
        )

    # ──────────── Resources ────────────
    @agent.tool
    def hub_get_resource(ctx: RunContext[AgentDeps], resource_id: str) -> str:
        """Détails d'une ressource par resourceId."""
        return HUB_FUNCTIONS["get_resource"](
            resource_id=resource_id,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_find_resource(ctx: RunContext[AgentDeps], search: str) -> str:
        """Recherche une ressource par fragment (ex. RES-29 ou un nom)."""
        return HUB_FUNCTIONS["find_resource"](
            search=search,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_find_resource_by_name(
        ctx: RunContext[AgentDeps],
        name: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> str:
        """Recherche une ressource par nom complet, nom ou prénom."""
        return HUB_FUNCTIONS["find_resource_by_name"](
            name=name,
            first_name=first_name,
            last_name=last_name,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_find_resource_by_email(ctx: RunContext[AgentDeps], email: str) -> str:
        """Recherche une ressource par email."""
        return HUB_FUNCTIONS["find_resource_by_email"](
            email=email,
            auth_header=ctx.deps.auth_header,
        )

    # ──────────── Catégories de tâches ────────────
    @agent.tool
    def hub_get_timesheet_categories(
        ctx: RunContext[AgentDeps],
        project_id: str,
        resource_id: str,
    ) -> str:
        """Catégories de saisie valides pour un projet + une ressource."""
        return HUB_FUNCTIONS["get_timesheet_categories"](
            project_id=project_id,
            resource_id=resource_id,
            auth_header=ctx.deps.auth_header,
        )

    # ──────────── Timesheet Header ────────────
    @agent.tool
    def hub_create_timesheet(
        ctx: RunContext[AgentDeps],
        resource_id: str,
        period_start: str | None = None,
        description: str = "",
    ) -> str:
        """Crée une feuille de temps hebdomadaire pour une ressource."""
        return HUB_FUNCTIONS["create_timesheet"](
            resource_id=resource_id,
            period_start=period_start,
            description=description,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_list_timesheets(
        ctx: RunContext[AgentDeps],
        resource_id: str | None = None,
        limit: int = 20,
        skip: int = 0,
    ) -> str:
        """Liste les feuilles de temps, avec pagination optionnelle."""
        return HUB_FUNCTIONS["list_timesheets"](
            resource_id=resource_id,
            limit=limit,
            skip=skip,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_get_timesheet(
        ctx: RunContext[AgentDeps],
        timesheet_nbr: str,
        resource_id: str | None = None,
    ) -> str:
        """Détails d'une feuille de temps par timesheetId/timesheet number."""
        return HUB_FUNCTIONS["get_timesheet"](
            timesheet_nbr=timesheet_nbr,
            resource_id=resource_id,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_update_timesheet(
        ctx: RunContext[AgentDeps],
        timesheet_nbr: str,
        description: str | None = None,
        period_id: str | None = None,
        resource_id: str | None = None,
    ) -> str:
        """Met à jour une feuille de temps existante."""
        return HUB_FUNCTIONS["update_timesheet"](
            timesheet_nbr=timesheet_nbr,
            description=description,
            period_id=period_id,
            resource_id=resource_id,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_delete_timesheet(
        ctx: RunContext[AgentDeps],
        timesheet_nbr: str,
        resource_id: str | None = None,
    ) -> str:
        """Supprime une feuille de temps existante."""
        return HUB_FUNCTIONS["delete_timesheet"](
            timesheet_nbr=timesheet_nbr,
            resource_id=resource_id,
            auth_header=ctx.deps.auth_header,
        )

    # ──────────── Timesheet Lines ────────────
    @agent.tool
    def hub_get_timesheet_lines(
        ctx: RunContext[AgentDeps],
        timesheet_nbr: str,
        proj_id: str | None = None,
        activity_number: str | None = None,
        date: str | None = None,
        category_id: str | None = None,
    ) -> str:
        """Liste les lignes d'heures d'une feuille de temps par timesheetId."""
        return HUB_FUNCTIONS["get_timesheet_lines"](
            timesheet_nbr=timesheet_nbr,
            proj_id=proj_id,
            activity_number=activity_number,
            date=date,
            category_id=category_id,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_create_timesheet_line(
        ctx: RunContext[AgentDeps],
        timesheet_nbr: str,
        proj_id: str,
        activity_number: str,
        category_id: str,
        resource_id: str,
        date: str,
        qty: float,
        internal_note: str = "",
        external_note: str = "",
    ) -> str:
        """Ajoute une ligne d'heures à une feuille de temps existante.

        À n'appeler qu'après confirmation explicite de l'utilisateur.
        """
        return HUB_FUNCTIONS["create_timesheet_line"](
            timesheet_nbr=timesheet_nbr,
            proj_id=proj_id,
            activity_number=activity_number,
            category_id=category_id,
            resource_id=resource_id,
            date=date,
            qty=qty,
            internal_note=internal_note,
            external_note=external_note,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_update_timesheet_line(
        ctx: RunContext[AgentDeps],
        rec_id: str,
        timesheet_nbr: str | None = None,
        proj_id: str | None = None,
        activity_number: str | None = None,
        category_id: str | None = None,
        resource_id: str | None = None,
        date: str | None = None,
        qty: float | None = None,
        internal_note: str | None = None,
        external_note: str | None = None,
    ) -> str:
        """Met à jour une ligne d'heures existante dans une feuille de temps.

        À n'appeler qu'après confirmation explicite de l'utilisateur.
        """
        return HUB_FUNCTIONS["update_timesheet_line"](
            rec_id=rec_id,
            timesheet_nbr=timesheet_nbr,
            proj_id=proj_id,
            activity_number=activity_number,
            category_id=category_id,
            resource_id=resource_id,
            date=date,
            qty=qty,
            internal_note=internal_note,
            external_note=external_note,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_delete_timesheet_line(ctx: RunContext[AgentDeps], rec_id: str) -> str:
        """Supprime une ligne d'heures existante dans une feuille de temps.

        À n'appeler qu'après confirmation explicite de l'utilisateur.
        """
        return HUB_FUNCTIONS["delete_timesheet_line"](
            rec_id=rec_id,
            auth_header=ctx.deps.auth_header,
        )

    # ──────────── Livrables ────────────
    @agent.tool
    def hub_get_project_deliverables(ctx: RunContext[AgentDeps], proj_id: str) -> str:
        """Liste les livrables d'un projet par projId."""
        return HUB_FUNCTIONS["get_project_deliverables"](
            proj_id=proj_id,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_get_task_deliverables(ctx: RunContext[AgentDeps], activity_number: str) -> str:
        """Liste les livrables d'une tâche par activityNumber."""
        return HUB_FUNCTIONS["get_task_deliverables"](
            activity_number=activity_number,
            auth_header=ctx.deps.auth_header,
        )

    # ──────────── Périodes ────────────
    @agent.tool
    def hub_get_timesheet_periods(
        ctx: RunContext[AgentDeps],
        resource_id: str | None = None,
        open_only: bool = True,
    ) -> str:
        """Liste les périodes de saisie de temps valides pour une ressource."""
        return HUB_FUNCTIONS["get_timesheet_periods"](
            resource_id=resource_id,
            open_only=open_only,
            auth_header=ctx.deps.auth_header,
        )

    @agent.tool
    def hub_get_timesheet_period_by_date(
        ctx: RunContext[AgentDeps],
        date: str,
        resource_id: str | None = None,
    ) -> str:
        """Retourne la période de saisie de temps valide pour une date et ressource."""
        return HUB_FUNCTIONS["get_timesheet_period_by_date"](
            date=date,
            resource_id=resource_id,
            auth_header=ctx.deps.auth_header,
        )