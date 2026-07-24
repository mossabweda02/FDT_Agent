# debug_ts_lookup.py — à lancer manuellement : python debug_ts_lookup.py
from dotenv import load_dotenv
load_dotenv() 
from backend.tools.hub_functions import hub_get_timesheet, hub_list_timesheets
import json

from backend.tools.hub_functions import (
    hub_list_projects,
    hub_get_timesheet,
    hub_list_timesheets,
    hub_get_project_tasks,
    hub_get_timesheet_categories,
    hub_get_ressource_project
)

AUTH_HEADER = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6ImFGa21LVkZjLTRXVjZzWENCdk5aa1hJNTA1WSIsImtpZCI6ImFGa21LVkZjLTRXVjZzWENCdk5aa1hJNTA1WSJ9.eyJhdWQiOiJhcGk6Ly83M2Y5YjJkMS04OTI5LTRmYzEtYTIyOC1kMzQ2YjllMzNlOWIiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9iNGUxYjAyNi05Y2FhLTQxZmEtOTk1MC0zNzdiN2VjNDZhZGIvIiwiaWF0IjoxNzg0NjM4NDg1LCJuYmYiOjE3ODQ2Mzg0ODUsImV4cCI6MTc4NDY0MzgyMywiYWNyIjoiMSIsImFpbyI6IkFZUUFlLzhjQUFBQXVZSGQvY1ZNdXZwbXlHWVhkdkdzRmpybjdCa28xR2FuMVJzMy9BUjJjdGIrdmJIUnFqS3RCanQ5aW1hWkJWM2FsdHB2RGF0aXc3Z0VaUEdEVm83U2kzNjM0T1hwbmtpQnI5VEluZFBGaHF0Z2o4cGNLRGlBQTk2T2JqZm5IY0VwWDNTYUsvZDdYWlorSzNNQVBYR2NPYU9keTUyeGpxckdZU3MySDVSOWlJTT0iLCJhbXIiOlsicHdkIiwibWZhIl0sImFwcGlkIjoiNzNmOWIyZDEtODkyOS00ZmMxLWEyMjgtZDM0NmI5ZTMzZTliIiwiYXBwaWRhY3IiOiIwIiwiZmFtaWx5X25hbWUiOiJXZWRhIiwiZ2l2ZW5fbmFtZSI6Ik1vc3NhYWIiLCJpcGFkZHIiOiIxMDIuMTA0LjEwMi4xNTkiLCJuYW1lIjoiTW9zc2FhYiBXZWRhIiwib2lkIjoiZjZjZWU1ZjAtNTJhNy00NWU5LTg0ZTQtNjE3ZTFmM2YyMGNlIiwicmgiOiIxLkFSd0FKckRodEtxYy1rR1pVRGQ3ZnNScTI5R3ktWE1waWNGUG9palRScm5qUHBzQUFGY2NBQS4iLCJzY3AiOiJGTk8uU2VydmVyLkFQSSIsInNpZCI6IjAwNmJlOTFhLTRjMmQtMjM4YS01YWViLWM1YTU1NDY4YTM3MSIsInN1YiI6InMybXlfTVJsLXJBeVZzSVhpVzZIaGdRZGNEMkExRnprVy0yaDV5RjZwSFkiLCJ0aWQiOiJiNGUxYjAyNi05Y2FhLTQxZmEtOTk1MC0zNzdiN2VjNDZhZGIiLCJ1bmlxdWVfbmFtZSI6Im1vc3NhYWIud2VkYUBtZXRhbS50ZWNoIiwidXBuIjoibW9zc2FhYi53ZWRhQG1ldGFtLnRlY2giLCJ1dGkiOiJWYnhWamJzWjRrLUo4Um4tUFBVdEFBIiwidmVyIjoiMS4wIiwieG1zX2Z0ZCI6IkNYcmhOMHNPUnFnUGxvcHEwcmJjX0hjYno3Ml9BY1g4TmJNZk5URGg4NzhCZFhOdWIzSjBhQzFrYzIxeiJ9.F6z3mXSLPlZVcjRN_IZriaa04KSeJqUKnHt_Mz-PeJwALUV0xdrXS8K2l9sd7h7jMhTA1p2KPNWOcgj9dG-pwhIx37fjTm0uUGdK5J0_AkSB2nFJb8vBTvrBn5RVEV9yGtdhsIUE4ii7hAEhbKJSSJPTE2QJYaosMhnCSDl6z9ZeVVgk-Vel8sxblPixYmpsjDoFVZ7EmiPnrDfnADlQrZu0xaS4vd7PcfQUqUA61UNGMfGikp5got6jrvRJZEJKqdZY0zDQdk-9ClYX07D1tdNwonrxBcwmXv9AXynEgJ8B77i2-oCmmSyWiY0dIBHNnlRITmAon_MiWHz5zEBSYA"
PROJECT_LIMIT = 1
RESOURCE_ID = "RES-3209"

# def parse_response(raw: str) -> dict:
#     try:
#         return json.loads(raw)
#     except (TypeError, json.JSONDecodeError):
#         return {}


# def extract_projects(payload: dict) -> list[dict]:
#     data = payload.get("data") or {}

#     if isinstance(data, list):
#         return data

#     return data.get("projects") or []


# def extract_tasks(payload: dict) -> list[dict]:
#     data = payload.get("data") or {}
#     tasks = data.get("tasks") or []

#     return tasks if isinstance(tasks, list) else []


# def extract_categories(payload: dict) -> list[dict]:
#     data = payload.get("data") or {}
#     categories = data.get("categories")

#     if not categories:
#         return []

#     if isinstance(categories, list):
#         return categories

#     if isinstance(categories, dict):
#         # Certaines réponses retournent une catégorie vide sous forme d'objet.
#         category_id = (
#             categories.get("category")
#             or categories.get("id")
#             or categories.get("lenId")
#         )

#         if category_id:
#             return [categories]

#         # Certaines APIs placent une liste dans une sous-clé.
#         for key in ("items", "categories", "data"):
#             nested = categories.get(key)
#             if isinstance(nested, list):
#                 return nested

#     return []

# def get_value(data: dict, *keys, default=None):
#     normalized = {str(k).lower(): v for k, v in data.items()}

#     for key in keys:
#         value = normalized.get(key.lower())
#         if value not in (None, ""):
#             return value

#     return default

# def get_project_id(project: dict) -> str | None:
#     return (
#         project.get("projId")
#         or project.get("projectId")
#         or project.get("id")
#     )


# projects_payload = parse_response(
#     hub_list_projects(
#         auth_header=AUTH_HEADER,
#         limit=PROJECT_LIMIT,
#     )
# )

# projects = extract_projects(projects_payload)

# print("=" * 80)
# print(f"PROJETS TROUVÉS : {len(projects)}")
# print("=" * 80)

# projects_with_metadata = 0

# for project in projects:
#     project_id = get_project_id(project)

#     if not project_id:
#         continue

#     tasks_payload = parse_response(
#         hub_get_project_tasks(
#             proj_id=project_id,
#             auth_header=AUTH_HEADER,
#         )
#     )

#     categories_payload = parse_response(
#         hub_get_timesheet_categories(
#             proj_id=project_id,
#             resource_id=RESOURCE_ID,
#             auth_header=AUTH_HEADER,
#         )
#     )

#     tasks = extract_tasks(tasks_payload)
#     categories = extract_categories(categories_payload)

#     # Ignore les projets sans tâches et sans catégories.
#     if not tasks and not categories:
#         continue

#     projects_with_metadata += 1

#     project_name = (
#         project.get("projectName")
#         or project.get("name")
#         or project_id
#     )

#     print(f"\n{'=' * 80}")
#     print(f"PROJET : {project_id} — {project_name}")
#     print(f"{'=' * 80}")

#     print(f"\nTÂCHES ({len(tasks)})")
#     print("-" * 40)

#     if tasks:
#         for task in tasks:
#             task_number = task.get("activitynumber", "N/A")
#             task_name = task.get("name") or task.get("description") or "Sans nom"
#             task_category = task.get("category") or "N/A"

#             print(f"- [{task_category}] {task_number} : {task_name}")
#     else:
#         print("Aucune tâche.")

# print("\n" + "=" * 80)
# print(f"PROJETS AVEC TÂCHES OU CATÉGORIES : {projects_with_metadata}")
# print("=" * 80)

# print("=" * 80)
# print("1. Get all projects")
# print("=" * 80)
# print(
#     hub_list_projects(
#         auth_header=AUTH_HEADER,
#         limit= 10
#     )
# )

# print("=" * 80)
# print("2. Get Timesheet")
# print("=" * 80)
# print(
#     hub_get_timesheet(
#         timesheet_nbr="TS-0000318",
#         resource_id="RES-3988",
#         auth_header=AUTH_HEADER,
#     )
# )

# print()

# print("=" * 80)
# print("3. List Timesheets")
# print("=" * 80)
# print(
#     hub_list_timesheets(
#         resource_id="RES-3988",
#         limit=5,
#         skip=0,
#         auth_header=AUTH_HEADER,
#     )
# )

# print("=" * 80)
# print("4. Get project tasks")
# print("=" * 80)
# print(
#     hub_get_project_tasks(
#         proj_id="PRJ-00874",
#         auth_header=AUTH_HEADER,
#     )
# )

# print()

# print("=" * 80)
# print("5. List Timesheets")
# print("=" * 80)
# print(
#     hub_get_timesheet_categories(
#         proj_id="PRJ-00874",
#         resource_id="RES-3988",
#         auth_header=AUTH_HEADER,
#     )
# )

print()

print("=" * 80)
print("5. List des projets par ressource_id")
print("=" * 80)
print(
    hub_get_ressource_project(
        resource_id=RESOURCE_ID,
        limit= PROJECT_LIMIT,
        skip=0,
        auth_header=AUTH_HEADER,
    )
)