"""
backend/tools/hub_functions.py

APIs "Integration Hub" pour l'agent Pydantic AI.

Ces fonctions appellent les APIs Operate pour gérer les feuilles de temps : 
projets, tâches, ressources, catégories et lignes timesheet.

"""

import os
import json
import httpx
from typing import Any
from azure.identity import DefaultAzureCredential

HUB_BASE = os.environ["HUB_BASE_URL"].rstrip("/")
OPERATE_BASE = os.environ["OPERATE_BASE_URL"]
HUB_SCOPE = os.environ.get("HUB_SCOPE", "api://73f9b2d1-8929-4fc1-a228-d346b9e33e9b/FNO.Server.API")
DATA_AREA = os.environ.get("HUB_DATA_AREA_ID", "USSI")

# ── Azure Credentials ──────────────────────────────────────────────────────────────────────────────
#  DefaultAzureCredential pour l'authentification automatique via Azure CLI 
# exclude_environment_credential=True évite les conflits avec des variables d'env vides
_credential = DefaultAzureCredential(exclude_environment_credential=True)

# ── Authentification / headers ──────────────────────────────────────────────
def _token() -> str:
    """
    Retourne le token pour Integration Hub.

    Priorité :
      1. HUB_BEARER_TOKEN pour les tests rapides
      2. DefaultAzureCredential pour le mode cible
    """

    static = os.environ.get("HUB_BEARER_TOKEN")
    if static:
        return static
    return _credential.get_token(HUB_SCOPE).token


def _headers() -> dict:
    """Construit les headers communs pour Integration Hub."""

    return {
        "Authorization": f"Bearer {_token()}",
        "X-Operate-Base-Url": OPERATE_BASE,   
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

# ── Réponses standardisées ─────────────────────────────────────────────────
def _ok(data) -> str:
    """Retourne une réponse JSON standard en cas de succès."""

    return json.dumps(
            {"ok": True, "data": data},
            ensure_ascii=False,
            default=str,
        )

def _err(status, body) -> str:
    """Retourne une réponse JSON standard en cas d'erreur."""

    hint = ""

    if status == 0:
        hint = "Erreur locale : vérifier réseau, variables d'environnement ou token."
    elif status == 400:
        hint = "Validation : un champ obligatoire manque ou est mal formaté."
    elif status == 401:
        hint = "Token invalide/expiré ou mauvaise audience."
    elif status == 403:
        hint = "Accès refusé : permissions insuffisantes sur Integration Hub."
    elif status == 404:
        hint = "Endpoint ou ressource introuvable."
    elif status == 500:
        hint = "Erreur Hub : vérifier X-Operate-Base-Url et les champs envoyés."

    return json.dumps(
        {
            "ok": False,
            "status": status,
            "error": body,
            "hint": hint,
        },
        ensure_ascii=False,
        default=str,
    )

def _parse_response(response: httpx.Response) -> str:
    """Convertit une réponse HTTP en string JSON standardisée."""
    if not response.is_success:
        return _err(response.status_code, response.text[:500])

    try:
        return _ok(response.json())
    except Exception:
        return _ok(response.text)

# ── Requetes HTTP generiques ─────────────
def _get(path: str, params: dict[str, Any] | None = None) -> str:
    """Exécute une requête GET vers Integration Hub."""
    
    clean_params = {
        k: v for k, v in (params or {}).items()
        if v is not None
    }
    clean_params.setdefault("dataAreaId", DATA_AREA)

    try:
        response = httpx.get(
            f"{HUB_BASE}{path}",
            params=clean_params,
            headers=_headers(),
            timeout=30,
        )
        return _parse_response(response)
    except Exception as exc:
        return _err(0, str(exc))


def _post(path: str, payload: dict[str, Any]) -> str:
    """Exécute une requête POST vers Integration Hub."""
    
    clean_payload = {
        k: v for k, v in payload.items()
        if v is not None
    }
    clean_payload.setdefault("dataAreaId", DATA_AREA)

    try:
        response = httpx.post(
            f"{HUB_BASE}{path}",
            json=clean_payload,
            headers=_headers(),
            timeout=30,
        )
        return _parse_response(response)
    except Exception as exc:
        return _err(0, str(exc))


def _put(path: str, payload: dict[str, Any]) -> str:
    """Exécute une requête PUT vers Integration Hub."""
    
    clean_payload = {
        k: v for k, v in payload.items()
        if v is not None
    }
    clean_payload.setdefault("dataAreaId", DATA_AREA)

    try:
        response = httpx.put(
            f"{HUB_BASE}{path}",
            json=clean_payload,
            headers=_headers(),
            timeout=30,
        )
        return _parse_response(response)
    except Exception as exc:
        return _err(0, str(exc))


def _delete(path: str, params: dict[str, Any] | None = None) -> str:
    """Exécute une requête DELETE vers Integration Hub."""
    
    clean_params = {
        k: v for k, v in (params or {}).items()
        if v is not None
    }
    clean_params.setdefault("dataAreaId", DATA_AREA)

    try:
        response = httpx.delete(
            f"{HUB_BASE}{path}",
            params=clean_params,
            headers=_headers(),
            timeout=30,
        )
        return _parse_response(response)
    except Exception as exc:
        return _err(0, str(exc))


# ── Projets ────────────────────────────────────────────────────────────────

def hub_list_projects(limit: int = 20) -> str:
    """Liste les projets Operate."""
    return _get("/api/projects", {"limit": limit})


def hub_get_project(proj_id: str) -> str:
    """Récupère le détail d'un projet par projId."""
    return _get(f"/api/project/{proj_id}")


# ── Tâches ─────────────────────────────────────────────────────────────────

def hub_get_project_tasks(proj_id: str) -> str:
    """Liste les tâches d'un projet."""
    return _get(f"/api/project/{proj_id}/tasks")


def hub_get_task(activity_number: str) -> str:
    """Récupère le détail d'une tâche par activityNumber."""
    return _get(f"/api/task/{activity_number}")


def hub_list_tasks(limit: int = 50) -> str:
    """Liste les tâches disponibles."""
    return _get("/api/tasks", {"limit": limit})


# ── Ressources ─────────────────────────────────────────────────────────────

def hub_find_resource(search: str) -> str:
    """Recherche une ressource par fragment de resourceId ou nom."""
    return _get("/api/resources", {"search": search})


def hub_get_resource(resource_id: str) -> str:
    """Récupère une ressource par resourceId."""
    return _get(f"/api/resource/{resource_id}")


def hub_find_resource_by_email(email: str) -> str:
    """Recherche une ressource par email."""
    return _get("/api/resource-by-email", {"email": email})

def hub_find_resource_by_name(
    name: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> str:
    """Recherche une ressource par nom complet, prénom ou nom."""
    return _get(
        "/api/resource-by-name",
        {
            "name": name,
            "firstName": first_name,
            "lastName": last_name,
        },
    )


# ── Catégories Timesheet ───────────────────────────────────────────────────

def hub_get_timesheet_categories(project_id: str, resource_id: str) -> str:
    """Récupère les catégories valides pour un projet et une ressource."""
    return _get(
        "/api/timesheet/categories",
        {
            "projectId": project_id,
            "resourceId": resource_id,
        },
    )


# ── Timesheet header ───────────────────────────────────────────────────────

def hub_create_timesheet( resource_id: str, period_start: str | None = None, description: str = "",
) -> str:
    
    """Crée une feuille de temps"""
    return _post(
        "/api/timesheet",
        {
            "resourceId": resource_id,
            "periodStart": period_start,
            "description": description,
        },
    )

def hub_list_timesheets(
    resource_id: str | None = None,
    limit: int = 50,
    skip: int = 0,
) -> str:
    """Liste les feuilles de temps."""
    return _get(
        "/api/timesheets",
        {
            "resourceId": resource_id,
            "limit": limit,
            "skip": skip,
        },
    )

def hub_get_timesheet(
    timesheet_nbr: str,
    resource_id: str | None = None,
) -> str:
    """Récupère une feuille de temps par timesheet_nbr et resourceId."""
    return _get(
        f"/api/timesheet/{timesheet_nbr}",
        {
            "resourceId": resource_id,
        },
    )

def hub_update_timesheet(
    timesheet_nbr: str,
    description: str | None = None,
    period_id: str | None = None,
) -> str:
    """Modifie une feuille de temps."""
    
    payload = {}

    if description is not None:
        payload["description"] = description

    if period_id is not None:
        payload["periodid"] = period_id

    return _put(
        f"/api/timesheet/{timesheet_nbr}",
        payload,
    )

def hub_delete_timesheet(
    timesheet_nbr: str,
    resource_id: str | None = None,
) -> str:
    """Supprime une feuille de temps."""
    
    params = {}

    if resource_id:
        params["resourceId"] = resource_id

    return _delete(
        f"/api/timesheet/{timesheet_nbr}",
        params,
    )

# ── Timesheet lines : lecture ──────────────────────────────────────────────

def hub_get_timesheet_lines(
    timesheet_nbr: str,
    proj_id: str | None = None,
    activity_number: str | None = None,
    date: str | None = None,
    category_id: str | None = None,
) -> str:
    """Récupère les lignes d'une feuille de temps avec filtres."""
    return _get(
        "/api/timesheet-lines",
        {
            "timesheetNbr": timesheet_nbr,
            "projId": proj_id,
            "activityNumber": activity_number,
            "date": date,
            "categoryId": category_id,
        },
    )


# ── Timesheet lines : création ─────────────────────────────────────────────

def hub_create_timesheet_line(
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
    
    """Ajoute une ligne d'heures à une feuille de temps existante."""
    return _post(
        "/api/timesheet-line",
        {
            "timesheetNbr": timesheet_nbr,
            "projId": proj_id,
            "activityNumber": activity_number,
            "categoryId": category_id,
            "resourceId": resource_id,
            "date": date,
            "qty": qty,
            "internalNote": internal_note,
            "externalNote": external_note,
        },
    )


# def hub_create_time_entry(
#     resource_id: str,
#     project_id: str,
#     activity_number: str,
#     qty: float,
#     start_date: str,
#     note: str = "",
# ) -> str:
#     """
#     Enregistre une saisie de temps.
#     """
#     return _post(
#         "/api/timeentry",
#         {
#             "resourceId": resource_id,
#             "projectId": project_id,
#             "activityNumber": activity_number,
#             "qty": qty,
#             "startDate": start_date,
#             "note": note,
#         },
#     )


# ── Timesheet lines : modification / suppression ──────────────────────────

def hub_update_timesheet_line(
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
    """Modifie une ligne de feuille de temps existante par recId."""
    return _put(
        f"/api/timesheet-line/{rec_id}",
        {
            "timesheetNbr": timesheet_nbr,
            "qty": qty,
            "date": date,
            "projId": proj_id,
            "activityNumber": activity_number,
            "categoryId": category_id,
            "resourceId": resource_id,
            "internalNote": internal_note,
            "externalNote": external_note,
        },
    )


def hub_delete_timesheet_line(rec_id: str) -> str:
    """Supprime une ligne de feuille de temps par recId."""
    return _delete(f"/api/timesheet-line/{rec_id}")

# ── Livrables ───────────────────────────────────────────────────────────────

def hub_get_project_deliverables(proj_id: str) -> str:
    """Liste les livrables disponibles pour un projet."""
    return _get(f"/api/project/{proj_id}/deliverables")


def hub_get_task_deliverables(activity_number: str) -> str:
    """Liste les livrables liés à une tâche."""
    return _get(f"/api/task/{activity_number}/deliverables")


# ── Périodes Timesheet ─────────────────────────────────────────────────────

def hub_get_timesheet_periods(
    resource_id: str | None = None,
    open_only: bool | None = None,
) -> str:
    """Liste les périodes timesheet valides pour une ressource."""
    return _get(
        "/api/timesheet-periods",
        {
            "resourceId": resource_id,
            "openOnly": str(open_only).lower() if open_only is not None else None,
        },
    )


def hub_get_timesheet_period_by_date(
    date: str,
    resource_id: str | None = None,
) -> str:
    """Retourne la période timesheet qui couvre une date donnée."""
    return _get(
        "/api/timesheet-period-by-date",
        {
            "date": date,
            "resourceId": resource_id,
        },
    )

# ── Registre des outils exposés à l'agent ──────────────────────────────────

HUB_FUNCTIONS = {
    # Projets
    "list_projects": hub_list_projects,
    "get_project": hub_get_project,

    # Tâches
    "get_project_tasks": hub_get_project_tasks,
    "get_task": hub_get_task,
    "list_tasks": hub_list_tasks,

    # Ressources
    "find_resource": hub_find_resource,
    "get_resource": hub_get_resource,
    "find_resource_by_email": hub_find_resource_by_email,
    "find_resource_by_name": hub_find_resource_by_name,

    # Catégories
    "get_timesheet_categories": hub_get_timesheet_categories,

    # Timesheet header
    "create_timesheet": hub_create_timesheet,
    "list_timesheets": hub_list_timesheets,
    "get_timesheet": hub_get_timesheet,
    "update_timesheet": hub_update_timesheet,
    "delete_timesheet": hub_delete_timesheet,

    # Timesheet lines
    "get_timesheet_lines": hub_get_timesheet_lines,
    "create_timesheet_line": hub_create_timesheet_line,
    "update_timesheet_line": hub_update_timesheet_line,
    "delete_timesheet_line": hub_delete_timesheet_line,

    # Livrables
    "get_project_deliverables": hub_get_project_deliverables,
    "get_task_deliverables": hub_get_task_deliverables,

    # Périodes
    "get_timesheet_periods": hub_get_timesheet_periods,
    "get_timesheet_period_by_date": hub_get_timesheet_period_by_date,
    # "create_time_entry": hub_create_time_entry,
}