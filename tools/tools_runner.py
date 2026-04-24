"""
Dispatcher des tool calls de l'agent Azure AI Foundry.
Objectifs : 
1. Robustesse : parse les arguments de manière tolérante (gère dict, JSON valide))
2. Validation SQL : utilise sql_validator pour bloquer les requêtes dangereuses AVANT l'exécution
3. Uniformité : garantit que la réponse est TOUJOURS une string JSON (jamais un dict car le LLM ne peut pas lire un dict), même en cas d'erreur
"""

import json
import re
from tools.functions_tools import TOOL_FUNCTIONS
from tools.sql_validator import validate_sql_query


def _parse_args(raw) -> dict:
    """
    Parse les arguments du tool call de façon robuste.
    Gère : dict déjà parsé, JSON string valide, JSON tronqué, garbage.
    """
    # Déjà un dict
    if isinstance(raw, dict):
        return raw

    if not raw or not str(raw).strip():
        return {}

    raw = str(raw).strip()

    # JSON valide directement
    try:
        result = json.loads(raw)
        return result if isinstance(result, dict) else {}
    except json.JSONDecodeError:
        pass

    # Premier objet JSON complet
    match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Entre le premier { et le dernier }
    s, e = raw.find('{'), raw.rfind('}')
    if s != -1 and e != -1 and e > s:
        try:
            return json.loads(raw[s:e + 1])
        except json.JSONDecodeError:
            pass

    print(f"  [WARN] Impossible de parser les args : {raw[:80]}")
    return {}


def run_tool(name: str, arguments) -> str:
    fn = TOOL_FUNCTIONS.get(name)

    if not fn:
        return json.dumps({"error": f"Tool '{name}' not found",
                           "available": list(TOOL_FUNCTIONS.keys())})

    try:
        args = _parse_args(arguments)

        # Validation SQL en amont si la requête est fournie
        if "query" in args and args["query"]:
            ok, err = validate_sql_query(args["query"])
            if not ok:
                return json.dumps({"error": err, "rows": [], "row_count": 0})

        result = fn(**args)

        # S'assurer que la réponse est toujours une string JSON
        if isinstance(result, dict):
            return json.dumps(result, ensure_ascii=False, default=str)
        if isinstance(result, str):
            return result
        return json.dumps({"result": str(result)})

    except Exception as e:
        return json.dumps({"error": str(e), "rows": [], "row_count": 0})