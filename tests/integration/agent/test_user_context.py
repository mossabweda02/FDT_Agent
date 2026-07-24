"""Tests Phase 1 : UserContext et résolution ressource."""

import base64
import json

from backend.core.auth import user_context as uc


def _fake_auth_header(payload: dict) -> str:
    header = {"alg": "none", "typ": "JWT"}

    def enc(data: dict) -> str:
        raw = json.dumps(data).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    return f"Bearer {enc(header)}.{enc(payload)}.signature"


def test_extract_claims_uses_preferred_username():
    auth = _fake_auth_header(
        {
            "preferred_username": "mossab.weda@example.com",
            "name": "Mossaab Weda",
            "oid": "object-123",
        }
    )

    claims = uc._extract_claims(auth)

    assert claims["email"] == "mossab.weda@example.com"
    assert claims["fullname"] == "Mossaab Weda"
    assert claims["object_id"] == "object-123"


def test_extract_resource_id_from_dict_response():
    raw = json.dumps({"ok": True, "data": {"resourceId": "RES-108"}})

    assert uc._extract_resource_id_from_hub_response(raw) == "RES-108"


def test_extract_resource_id_from_list_response():
    raw = json.dumps({"ok": True, "data": [{"RESOURCEID": "RES-108"}]})

    assert uc._extract_resource_id_from_hub_response(raw) == "RES-108"
