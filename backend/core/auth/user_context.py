"""
Module: backend.core.auth.user_context
======================================
Résolution du contexte utilisateur connecté pour FDT Agent et construction d'un UserContext partagé entre backend, 
agent et tools afin de propager les informations d'identité et de ressource métier.

La validation cryptographique complète du token reste dans la Phase 2.
"""

from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass
from typing import Any

from backend.tools.hub_functions import HUB_FUNCTIONS


@dataclass
class UserContext:
    """Contexte utilisateur partagé entre backend, agent et tools."""

    auth_header: str
    email: str | None = None
    fullname: str | None = None
    object_id: str | None = None
    resource_id: str | None = None
    role: str | None = None
    resource_resolution_status: str = "not_attempted"

    def to_safe_dict(self) -> dict[str, Any]:
        """Retourne un résumé sans token pour injection prompt/logs."""

        data = asdict(self)
        data.pop("auth_header", None)
        return data


def _decode_jwt_payload_unverified(auth_header: str) -> dict[str, Any]:
    """Décode le payload JWT sans validation cryptographique.

    Utilisé uniquement pour extraire email/nom/object id en Phase 1.
    La sécurité réelle doit être ajoutée en Phase 2 avec validation issuer,
    audience, signature, expiration et scopes.
    """

    if not auth_header.startswith("Bearer "):
        return {}

    token = auth_header.removeprefix("Bearer ").strip()
    parts = token.split(".")
    if len(parts) < 2:
        return {}

    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload + padding)
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}


def _first_non_empty(*values: Any) -> str | None:
    """Retourne la première valeur string non vide."""

    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _extract_claims(auth_header: str) -> dict[str, str | None]:
    """Extrait les claims utilisateur les plus courants d'Entra ID."""

    claims = _decode_jwt_payload_unverified(auth_header)
    return {
        "email": _first_non_empty(
            claims.get("email"),
            claims.get("preferred_username"),
            claims.get("upn"),
        ),
        "fullname": _first_non_empty(claims.get("name"), claims.get("given_name")),
        "object_id": _first_non_empty(claims.get("oid"), claims.get("sub")),
    }


def _extract_resource_id_from_hub_response(raw_response: str) -> str | None:
    """Extrait un resourceId depuis une réponse Hub standardisée.

    La réponse exacte du Hub peut varier. On supporte les formats fréquents :
    - {"ok": true, "data": {"resourceId": "RES-..."}}
    - {"ok": true, "data": [{"resourceId": "RES-..."}]}
    - clés variantes : RESOURCEID, ResourceId, resource_id.
    """

    try:
        envelope = json.loads(raw_response)
    except Exception:
        return None

    if not envelope.get("ok"):
        return None

    data = envelope.get("data")
    candidates: list[dict[str, Any]] = []

    if isinstance(data, dict):
        candidates.append(data)
        for key in ("items", "value", "results", "resources", "data"):
            nested = data.get(key)
            if isinstance(nested, list):
                candidates.extend(x for x in nested if isinstance(x, dict))
            elif isinstance(nested, dict):
                candidates.append(nested)
    elif isinstance(data, list):
        candidates.extend(x for x in data if isinstance(x, dict))

    keys = (
        "resourceId",
        "ResourceId",
        "resourceID",
        "ResourceID",
        "RESOURCEID",
        "resource_id",
        "resource",
        "Resource",
        "id",
        "Id",
    )
    for item in candidates:
            for key in keys:
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

    return None


def resolve_user_context(auth_header: str) -> UserContext:
    """Construit le UserContext et tente la résolution email -> resourceId."""

    claims = _extract_claims(auth_header)
    ctx = UserContext(
        auth_header=auth_header,
        email=claims["email"],
        fullname=claims["fullname"],
        object_id=claims["object_id"],
    )

    if not ctx.email:
        ctx.resource_resolution_status = "missing_email_claim"
        return ctx

    try:
        raw = HUB_FUNCTIONS["find_resource_by_email"](
            email=ctx.email,
            auth_header=auth_header,
        )
        ctx.resource_id = _extract_resource_id_from_hub_response(raw)
        ctx.resource_resolution_status = "resolved" if ctx.resource_id else "not_found"

    except Exception:
        ctx.resource_resolution_status = "hub_error"

    return ctx