import json

from backend.tools.hub_functions import HUB_FUNCTIONS

AUTH_HEADER = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6ImFGa21LVkZjLTRXVjZzWENCdk5aa1hJNTA1WSIsImtpZCI6ImFGa21LVkZjLTRXVjZzWENCdk5aa1hJNTA1WSJ9.eyJhdWQiOiJhcGk6Ly83M2Y5YjJkMS04OTI5LTRmYzEtYTIyOC1kMzQ2YjllMzNlOWIiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9iNGUxYjAyNi05Y2FhLTQxZmEtOTk1MC0zNzdiN2VjNDZhZGIvIiwiaWF0IjoxNzg0MDI1MDM4LCJuYmYiOjE3ODQwMjUwMzgsImV4cCI6MTc4NDAzMDAxOSwiYWNyIjoiMSIsImFpbyI6IkFZUUFlLzhjQUFBQUJDckdwUFYxQXdPYmU5d2VhV2NwNTlNOE1Na3lZRWFuYUxTR1B3bzdrUGxpR3JRa09RdHEzUlEwak9GaFMrdHZsZTh2YlJYZVVOdUFnVW1wb0hIcnVnRWxDNTlNWnFnYytLVEUyZ3Jkc3NYOWVwM3UrWFNNWGtqa3grU0tmSFBRWGVncGZ3NEpQeDZCTVF6ZnBQUWdpdEkvZmY4U2VjdW5WNVJVaWwvR3o0Yz0iLCJhbXIiOlsicHdkIiwibWZhIl0sImFwcGlkIjoiNzNmOWIyZDEtODkyOS00ZmMxLWEyMjgtZDM0NmI5ZTMzZTliIiwiYXBwaWRhY3IiOiIwIiwiZmFtaWx5X25hbWUiOiJXZWRhIiwiZ2l2ZW5fbmFtZSI6Ik1vc3NhYWIiLCJpcGFkZHIiOiI0MS4yMjQuNS43OSIsIm5hbWUiOiJNb3NzYWFiIFdlZGEiLCJvaWQiOiJmNmNlZTVmMC01MmE3LTQ1ZTktODRlNC02MTdlMWYzZjIwY2UiLCJyaCI6IjEuQVJ3QUpyRGh0S3FjLWtHWlVEZDdmc1JxMjlHeS1YTXBpY0ZQb2lqVFJybmpQcHNBQUZjY0FBLiIsInNjcCI6IkZOTy5TZXJ2ZXIuQVBJIiwic2lkIjoiMDA2YmU5MWEtNGMyZC0yMzhhLTVhZWItYzVhNTU0NjhhMzcxIiwic3ViIjoiczJteV9NUmwtckF5VnNJWGlXNkhoZ1FkY0QyQTFGemtXLTJoNXlGNnBIWSIsInRpZCI6ImI0ZTFiMDI2LTljYWEtNDFmYS05OTUwLTM3N2I3ZWM0NmFkYiIsInVuaXF1ZV9uYW1lIjoibW9zc2FhYi53ZWRhQG1ldGFtLnRlY2giLCJ1cG4iOiJtb3NzYWFiLndlZGFAbWV0YW0udGVjaCIsInV0aSI6IllTS0ZGUFAtX1UyMS1tZVQwNlluQUEiLCJ2ZXIiOiIxLjAiLCJ4bXNfZnRkIjoiY1o5UDExVExWTldNR0FBd0YzMW1NYlpsLUdfRUZmQmwyX3lYOVpST1BWOEJkWE5sWVhOMExXUnpiWE0ifQ.VjHywmTdXMB0y1AWZFABibnR6re78MylTIQrIu6-6EUCZWEaLtEjE6D6h8eocIJ-ypVSI1CbDqd4NHSKyICHgEZ7pbmuMOtjclybjhzUK8oXnE0DW8glyTsL7hjn4k4EyzoPDKLlhsGbeHGBVDOXXOIKI-4r8evwY-TArUJ4Lj44-TO07w02FRj2obzau0poMWyShO-wOe_WeztOmvMfP9kS-ni1UfTgu6X_amXZZaXFSs_9Z3hNYl3Vtpm1yystE16ksDaSbwoGcSS7hbKfMv4oO4XbstmvbOPmuJEhFVdZDiZDAtpjCfFA66Tp1l0fg6K431PegchdUynanOB4RQ"
PROJECT_ID = "PRJ-00042"
RESOURCE_ID = "RES-3988"


def show(title: str, raw: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    try:
        print(json.dumps(json.loads(raw), indent=2, ensure_ascii=False))
    except Exception:
        print(raw)

# show(
#     "Projects",
#     HUB_FUNCTIONS["list_projects"](
#         limit=100,
#         auth_header=AUTH_HEADER,
#     ),
# )

show(
    f"Tasks for {PROJECT_ID}",
    HUB_FUNCTIONS["get_project_tasks"](
        proj_id=PROJECT_ID,
        auth_header=AUTH_HEADER,
    ),
)

show(
    f"Categories for {PROJECT_ID}",
    HUB_FUNCTIONS["get_timesheet_categories"](
        project_id=PROJECT_ID,
        resource_id=RESOURCE_ID,
        auth_header=AUTH_HEADER,
    ),
)