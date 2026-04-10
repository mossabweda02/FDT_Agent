"""
Dispatcher des tool calls de l'agent Azure AI Foundry.
"""

import json
from tools.functions_tools import TOOL_FUNCTIONS


def run_tool(name: str, arguments: dict) -> str:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return json.dumps({
            "error": f"Tool '{name}' introuvable.",
            "available": list(TOOL_FUNCTIONS.keys()),
        })
    try:
        return fn(**arguments)
    except Exception as e:
        return json.dumps({"error": f"Erreur '{name}' : {e}"})