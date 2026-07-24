import json

from backend.tools.hub_functions import (
    HUB_BASE,
    OPERATE_BASE,
    hub_get_project_tasks,
    hub_get_task,
    hub_list_tasks,
)

AUTH_HEADER = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6ImFGa21LVkZjLTRXVjZzWENCdk5aa1hJNTA1WSIsImtpZCI6ImFGa21LVkZjLTRXVjZzWENCdk5aa1hJNTA1WSJ9.eyJhdWQiOiJhcGk6Ly83M2Y5YjJkMS04OTI5LTRmYzEtYTIyOC1kMzQ2YjllMzNlOWIiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9iNGUxYjAyNi05Y2FhLTQxZmEtOTk1MC0zNzdiN2VjNDZhZGIvIiwiaWF0IjoxNzg0MTkxMDA5LCJuYmYiOjE3ODQxOTEwMDksImV4cCI6MTc4NDE5NTE5NywiYWNyIjoiMSIsImFpbyI6IkFZUUFlLzhjQUFBQVl2NmtMVU1WTDZZbExYZGVqelJVczc1MFZ6NllOMkgzVzMwNkFwalJBckszTzZleHptd2huVzBqMlJJVlJubmx5dXkzMWpuSzQ4Ri92WW52YTdmc0hwMXFZT0ZsSTFIUDFkT0E3LzlSR1RPTWwyVHhPblRMWW5XempWMWxaSjlXSEpxNCtpSDl6TjRycWdablREbFJKam1KWk1HcGhHV05kSksxc0FsZXhSST0iLCJhbXIiOlsicHdkIiwibWZhIl0sImFwcGlkIjoiNzNmOWIyZDEtODkyOS00ZmMxLWEyMjgtZDM0NmI5ZTMzZTliIiwiYXBwaWRhY3IiOiIwIiwiZmFtaWx5X25hbWUiOiJXZWRhIiwiZ2l2ZW5fbmFtZSI6Ik1vc3NhYWIiLCJpcGFkZHIiOiI0MS4yMjYuMTEuNzQiLCJuYW1lIjoiTW9zc2FhYiBXZWRhIiwib2lkIjoiZjZjZWU1ZjAtNTJhNy00NWU5LTg0ZTQtNjE3ZTFmM2YyMGNlIiwicmgiOiIxLkFSd0FKckRodEtxYy1rR1pVRGQ3ZnNScTI5R3ktWE1waWNGUG9palRScm5qUHBzQUFGY2NBQS4iLCJzY3AiOiJGTk8uU2VydmVyLkFQSSIsInNpZCI6IjAwNmJlOTFhLTRjMmQtMjM4YS01YWViLWM1YTU1NDY4YTM3MSIsInN1YiI6InMybXlfTVJsLXJBeVZzSVhpVzZIaGdRZGNEMkExRnprVy0yaDV5RjZwSFkiLCJ0aWQiOiJiNGUxYjAyNi05Y2FhLTQxZmEtOTk1MC0zNzdiN2VjNDZhZGIiLCJ1bmlxdWVfbmFtZSI6Im1vc3NhYWIud2VkYUBtZXRhbS50ZWNoIiwidXBuIjoibW9zc2FhYi53ZWRhQG1ldGFtLnRlY2giLCJ1dGkiOiJ4YlRGR1BKQTlVNlVRd0Zrdjk5R0FBIiwidmVyIjoiMS4wIiwieG1zX2Z0ZCI6InNDMTMtVlVEc0VnYXlRbGpCS05xV1NpZ0lKaFNVTEF1Y3p6VWRsM2JieFVCZFhOM1pYTjBNeTFrYzIxeiJ9.d6iDvswgCTMuxmr_77n3lYcJ2ugemGe34_Kjh243Cp6amJacW_a-KMFMXiVx9BAcIIOv5JX3o8j2vWBOozy8UXLS_cHa5KGSXcbp9OXP3wZrC8IjsnWn4Gr1Pg0WXWjw4snXGS8CGf8sCtm_8DrQuEHywm1JDJ5EasO34oejttiUfQMqRCK5TmfHsYy7oen-R-u0R3k9XkPNQMoUmTUNmYvGa_411fUeRsWVa9bHINDnUQ1pFbqeDFfuUSPGSuWYiZeJ-z-DXB94FWvtzjIxXHOzid_zH20NMvWtcytY_n-PQ-bLdRiZkNwQkGmVpiBQAE5oSSCLnki74h-PfaaBYA"
ACTIVITY_NUMBER = "TSK-00596"

print("HUB_BASE    =", HUB_BASE)
print("OPERATE_BASE=", OPERATE_BASE)

# def parse_json(raw: str) -> dict:
#     try:
#         return json.loads(raw)
#     except (TypeError, json.JSONDecodeError):
#         return {}


# # 1. Détail direct
# detail_payload = parse_json(
#     hub_get_task(
#         activity_number=ACTIVITY_NUMBER,
#         auth_header=AUTH_HEADER,
#     )
# )

# print("\n=== GET TASK ===")
# print(json.dumps(detail_payload, indent=2, ensure_ascii=False))


# # 2. Liste globale des tâches
# tasks_payload = parse_json(
#     hub_list_tasks(
#         limit=500,
#         auth_header=AUTH_HEADER,
#     )
# )

# print("\n=== LIST TASKS ===")
# print(json.dumps(tasks_payload, indent=2, ensure_ascii=False))


# data = tasks_payload.get("data") or {}

# if isinstance(data, dict):
#     tasks = (
#         data.get("tasks")
#         or data.get("items")
#         or data.get("results")
#         or []
#     )
# elif isinstance(data, list):
#     tasks = data
# else:
#     tasks = []


# matching_task = next(
#     (
#         task
#         for task in tasks
#         if (
#             task.get("activitynumber")
#             or task.get("activityNumber")
#             or task.get("code")
#         ) == ACTIVITY_NUMBER
#     ),
#     None,
# )

# print("\n=== TÂCHE TROUVÉE ===")

# if matching_task:
#     print(json.dumps(matching_task, indent=2, ensure_ascii=False))

#     task_name = (
#         matching_task.get("name")
#         or matching_task.get("taskName")
#         or matching_task.get("TASKNAME")
#         or matching_task.get("description")
#         or "Sans nom"
#     )

#     task_category = (
#         matching_task.get("category")
#         or matching_task.get("taskCategory")
#         or matching_task.get("taskcategory")
#         or "N/A"
#     )

#     print(
#         f"\n[{task_category}] "
#         f"{ACTIVITY_NUMBER} : "
#         f"{task_name}"
#     )
# else:
#     print(f"Tâche {ACTIVITY_NUMBER} introuvable dans /api/tasks")