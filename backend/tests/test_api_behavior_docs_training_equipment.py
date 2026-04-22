from __future__ import annotations

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


def test_documents_lifecycle_with_version_signatures(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])

    types_resp = client.get("/api/v1/documents/types", headers=_auth_header(token))
    assert types_resp.status_code == 200, types_resp.text
    doc_type_id = types_resp.json()[0]["id"]

    created = client.post(
        "/api/v1/documents",
        headers=_auth_header(token),
        json={"title": "SOP for line clearance", "document_type_id": doc_type_id, "department": "QA"},
    )
    assert created.status_code == 201, created.text
    doc = created.json()

    v1 = client.post(
        f"/api/v1/documents/{doc['id']}/versions",
        headers=_auth_header(token),
        json={"version_number": "1.0", "content": "Initial SOP", "change_summary": "Initial release"},
    )
    assert v1.status_code == 201, v1.text
    version_id = v1.json()["id"]

    reviewed = client.post(
        f"/api/v1/documents/{doc['id']}/versions/{version_id}/sign",
        headers=_auth_header(token),
        json={"password": seeded_db["admin_password"], "meaning": "reviewed", "comments": "Reviewed"},
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["new_status"] == "under_review"

    approved = client.post(
        f"/api/v1/documents/{doc['id']}/versions/{version_id}/sign",
        headers=_auth_header(token),
        json={"password": seeded_db["admin_password"], "meaning": "approved", "comments": "Approved"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["new_status"] == "approved"

    effective = client.post(
        f"/api/v1/documents/{doc['id']}/versions/{version_id}/sign",
        headers=_auth_header(token),
        json={"password": seeded_db["admin_password"], "meaning": "effective", "comments": "Effective now"},
    )
    assert effective.status_code == 200, effective.text
    assert effective.json()["new_status"] == "effective"

    v2_missing_reason = client.post(
        f"/api/v1/documents/{doc['id']}/versions",
        headers=_auth_header(token),
        json={"version_number": "2.0", "content": "Updated"},
    )
    assert v2_missing_reason.status_code == 400, v2_missing_reason.text


def test_training_assignment_detail_complete_and_ack(client, seeded_db):
    admin_token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    operator_token = _login(client, seeded_db["operator_username"], seeded_db["operator_password"])

    curricula_resp = client.get("/api/v1/training/curricula", headers=_auth_header(admin_token))
    assert curricula_resp.status_code == 200, curricula_resp.text
    seeded_curriculum_id = curricula_resp.json()[0]["id"]
    curriculum_detail = client.get(
        f"/api/v1/training/curricula/{seeded_curriculum_id}",
        headers=_auth_header(admin_token),
    )
    assert curriculum_detail.status_code == 200, curriculum_detail.text
    assignment_item_id = curriculum_detail.json()["items"][0]["id"]

    operator_me = client.get("/api/v1/auth/me", headers=_auth_header(operator_token)).json()

    due = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    assignment_resp = client.post(
        "/api/v1/training/assignments",
        headers=_auth_header(admin_token),
        json={"user_id": operator_me["id"], "curriculum_item_id": assignment_item_id, "due_date": due},
    )
    assert assignment_resp.status_code == 201, assignment_resp.text
    assignment_id = assignment_resp.json()["id"]

    detail = client.get(f"/api/v1/training/assignments/{assignment_id}", headers=_auth_header(operator_token))
    assert detail.status_code == 200, detail.text

    forbidden_complete = client.post(
        f"/api/v1/training/assignments/{assignment_id}/complete",
        headers=_auth_header(admin_token),
        json={"completion_method": "self_study", "passed": True},
    )
    assert forbidden_complete.status_code == 403, forbidden_complete.text

    complete = client.post(
        f"/api/v1/training/assignments/{assignment_id}/complete",
        headers=_auth_header(operator_token),
        json={"completion_method": "self_study", "assessment_score": 95, "passed": True},
    )
    assert complete.status_code == 200, complete.text

    duplicate_ack = client.post(
        f"/api/v1/training/assignments/{assignment_id}/read-and-understood",
        headers=_auth_header(operator_token),
        json={"password": seeded_db["operator_password"], "notes": "Ack"},
    )
    assert duplicate_ack.status_code == 400, duplicate_ack.text


def test_equipment_status_guardrails_and_records(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    me = client.get("/api/v1/auth/me", headers=_auth_header(token)).json()

    created = client.post(
        "/api/v1/equipment",
        headers=_auth_header(token),
        json={
            "equipment_id": "EQ-001",
            "name": "Reactor 1",
            "equipment_type": "process_equipment",
            "site_id": me["site_id"],
            "location": "Suite A",
        },
    )
    assert created.status_code == 201, created.text
    eq_id = created.json()["id"]

    invalid_transition = client.patch(
        f"/api/v1/equipment/{eq_id}/status",
        headers=_auth_header(token),
        json={"status": "pre_qualification", "reason": "Attempt invalid transition"},
    )
    assert invalid_transition.status_code == 400, invalid_transition.text

    valid_transition = client.patch(
        f"/api/v1/equipment/{eq_id}/status",
        headers=_auth_header(token),
        json={"status": "under_maintenance", "reason": "Scheduled maintenance window"},
    )
    assert valid_transition.status_code == 200, valid_transition.text

    cal = client.post(
        f"/api/v1/equipment/{eq_id}/calibrations",
        headers=_auth_header(token),
        json={
            "calibration_type": "scheduled",
            "performed_at": datetime.now(timezone.utc).isoformat(),
            "calibration_interval_days": 30,
            "result": "pass",
        },
    )
    assert cal.status_code == 201, cal.text

    quals = client.get(f"/api/v1/equipment/{eq_id}/qualifications", headers=_auth_header(token))
    assert quals.status_code == 200, quals.text
