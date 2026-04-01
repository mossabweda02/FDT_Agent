from tools.functions_tools import (
    list_tables,
    describe_table,
    get_sample_data,
    get_table_relationships,
    execute_query,
)

FUNCTIONS = {
    "list_tables":           list_tables,
    "describe_table":        describe_table,
    "get_sample_data":       get_sample_data,
    "get_table_relationships": get_table_relationships,
    "execute_query":         execute_query,
}


def run_tool(name: str, arguments: dict) -> str:
    fn = FUNCTIONS.get(name)
    if fn is None:
        return f"Tool '{name}' introuvable."
    try:
        return fn(**arguments)
    except Exception as e:
        return f"Erreur lors de l'exécution de '{name}' : {e}"