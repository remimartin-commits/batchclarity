"""CAPA attachment API tests (TASK-064 / GMP_RULES ┬º0.11).

Focused on GET .../attachments/{id}/file: happy-path bytes + 404 for unknown attachment.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone


def _login(client, username: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password, "totp_code": None},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["tokens"]["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_capa_for_task_049(client, token: str) -> dict:
    now = datetime.now(timezone.utc)
    me = client.get("/api/v1/auth/me", headers=_auth_header(token))
    assert me.status_code == 200, me.text
    assignee_id = me.json()["id"]
    create = client.post(
        "/api/v1/qms/capas",
        headers=_auth_header(token),
        json={
            "title": "CAPA for TASK-049 tests",
            "capa_type": "corrective",
            "source": "deviation",
            "gmp_classification": "major",
            "risk_level": "medium",
            "problem_description": "Deviation investigation required due to recurring process drift in granulation.",
            "root_cause_category": "process",
            "root_cause": "Legacy procedural ambiguity.",
            "department": "Quality",
            "identified_date": now.isoformat(),
            "target_completion_date": (now + timedelta(days=7)).isoformat(),
            "actions": [
                {
                    "description": "Revise SOP and train operators",
                    "assignee_id": assignee_id,
                    "action_type": "corrective",
                    "status": "pending",
                }
            ],
        },
    )
    assert create.status_code == 201, create.text
    return create.json()


def test_capa_attachment_file_download_happy_path_pdf_bytes_and_headers(client, seeded_db):
    """Upload a PDF; /file returns 200, correct Content-Type, body bytes, Content-Disposition filename."""
    creator_token = _login(client, seeded_db["operator_username"], seeded_db["operator_password"])
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    capa = _create_capa_for_task_049(client, creator_token)
    capa_id = capa["id"]

    pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    upload = client.post(
        f"/api/v1/qms/capas/{capa_id}/attachments",
        headers=_auth_header(token),
        files={"file": ("task064-report.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    attachment_id = upload.json()["id"]

    file_get = client.get(
        f"/api/v1/qms/capas/{capa_id}/attachments/{attachment_id}/file",
        headers=_auth_header(token),
        follow_redirects=False,
    )
    assert file_get.status_code == 200, file_get.text
    assert file_get.content == pdf_bytes
    ct = file_get.headers.get("content-type") or ""
    assert "application/pdf" in ct
    disp = file_get.headers.get("content-disposition") or ""
    assert "task064-report.pdf" in disp or "filename" in disp.lower()


def test_capa_attachment_file_404_for_unknown_attachment_id(client, seeded_db):
    """GET /file with a non-existent attachment_id returns 404."""
    creator_token = _login(client, seeded_db["operator_username"], seeded_db["operator_password"])
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    capa = _create_capa_for_task_049(client, creator_token)
    capa_id = capa["id"]
    bogus = str(uuid.uuid4())

    file_get = client.get(
        f"/api/v1/qms/capas/{capa_id}/attachments/{bogus}/file",
        headers=_auth_header(token),
        follow_redirects=False,
    )
    assert file_get.status_code == 404, file_get.text
    assert file_get.json()["detail"] == "Attachment not found."


def test_capa_attachment_file_404_for_unknown_capa_id(client, seeded_db):
    """GET /file for unknown capa_id returns 404 (CAPA scope)."""
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    capa = _create_capa_for_task_049(
        client, _login(client, seeded_db["operator_username"], seeded_db["operator_password"])
    )
    capa_id = capa["id"]
    upload = client.post(
        f"/api/v1/qms/capas/{capa_id}/attachments",
        headers=_auth_header(token),
        files={"file": ("x.pdf", b"x", "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    att_id = upload.json()["id"]

    missing_capa = str(uuid.uuid4())
    file_get = client.get(
        f"/api/v1/qms/capas/{missing_capa}/attachments/{att_id}/file",
        headers=_auth_header(token),
        follow_redirects=False,
    )
    assert file_get.status_code == 404, file_get.text
    assert file_get.json()["detail"] == "CAPA not found."
