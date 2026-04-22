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


def test_qms_deviation_create_update_and_filter(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    now = datetime.now(timezone.utc).isoformat()

    create = client.post(
        "/api/v1/qms/deviations",
        headers=_auth_header(token),
        json={
            "title": "Unexpected hold time exceeded",
            "deviation_type": "unplanned",
            "category": "process",
            "description": "Hold time exceeded by 3 hours before filtration step during batch execution.",
            "detected_during": "manufacturing",
            "detection_date": now,
            "risk_level": "high",
            "immediate_action": "Quarantined in-process material and notified QA immediately.",
        },
    )
    assert create.status_code == 201, create.text
    deviation = create.json()
    deviation_id = deviation["id"]
    assert deviation["deviation_number"].startswith("DEV-")

    patch = client.patch(
        f"/api/v1/qms/deviations/{deviation_id}",
        headers=_auth_header(token),
        json={"current_status": "under_review", "root_cause": "Operator delay due to line clearance issue."},
    )
    assert patch.status_code == 200, patch.text
    updated = patch.json()
    assert updated["current_status"] == "under_review"

    filtered = client.get(
        "/api/v1/qms/deviations",
        headers=_auth_header(token),
        params={"status_filter": "under_review"},
    )
    assert filtered.status_code == 200, filtered.text
    ids = {item["id"] for item in filtered.json()}
    assert deviation_id in ids

    transition = client.post(
        f"/api/v1/qms/deviations/{deviation_id}/approve",
        headers=_auth_header(token),
    )
    assert transition.status_code == 200, transition.text
    assert transition.json()["current_status"] == "approved"

    bad_state_jump = client.post(
        f"/api/v1/qms/deviations/{deviation_id}/submit",
        headers=_auth_header(token),
    )
    assert bad_state_jump.status_code == 400, bad_state_jump.text

    sign = client.post(
        f"/api/v1/qms/deviations/{deviation_id}/sign",
        headers=_auth_header(token),
        json={"password": seeded_db["admin_password"], "meaning": "reviewed", "comments": "Checked."},
    )
    assert sign.status_code == 200, sign.text

    invalid_payload = client.patch(
        f"/api/v1/qms/deviations/{deviation_id}",
        headers=_auth_header(token),
        json={"not_a_real_field": "x"},
    )
    assert invalid_payload.status_code == 422, invalid_payload.text


def test_qms_change_control_create_update_and_filter(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    create = client.post(
        "/api/v1/qms/change-controls",
        headers=_auth_header(token),
        json={
            "title": "Update cleaning validation limit",
            "change_type": "process",
            "change_category": "major",
            "description": "Adjust validated limit to align with new product residue risk assessment.",
            "justification": "Risk review indicates lower threshold needed for patient safety margin.",
            "regulatory_impact": True,
            "validation_required": True,
            "proposed_implementation_date": tomorrow,
        },
    )
    assert create.status_code == 201, create.text
    cc = create.json()
    cc_id = cc["id"]
    assert cc["change_number"].startswith("CC-")

    patch = client.patch(
        f"/api/v1/qms/change-controls/{cc_id}",
        headers=_auth_header(token),
        json={
            "current_status": "approved",
            "actual_implementation_date": tomorrow,
        },
    )
    assert patch.status_code == 200, patch.text
    updated = patch.json()
    assert updated["current_status"] == "approved"

    filtered = client.get(
        "/api/v1/qms/change-controls",
        headers=_auth_header(token),
        params={"status_filter": "approved"},
    )
    assert filtered.status_code == 200, filtered.text
    ids = {item["id"] for item in filtered.json()}
    assert cc_id in ids

    submit = client.post(f"/api/v1/qms/change-controls/{cc_id}/submit", headers=_auth_header(token))
    assert submit.status_code == 200, submit.text
    assert submit.json()["current_status"] == "under_review"

    approve = client.post(f"/api/v1/qms/change-controls/{cc_id}/approve", headers=_auth_header(token))
    assert approve.status_code == 200, approve.text
    assert approve.json()["current_status"] == "approved"

    implement = client.post(
        f"/api/v1/qms/change-controls/{cc_id}/implement",
        headers=_auth_header(token),
    )
    assert implement.status_code == 200, implement.text
    assert implement.json()["current_status"] == "implementation"

    close = client.post(f"/api/v1/qms/change-controls/{cc_id}/close", headers=_auth_header(token))
    assert close.status_code == 200, close.text
    assert close.json()["current_status"] == "closed"

    sign = client.post(
        f"/api/v1/qms/change-controls/{cc_id}/sign",
        headers=_auth_header(token),
        json={"password": seeded_db["admin_password"], "meaning": "approved", "comments": "Approved."},
    )
    assert sign.status_code == 200, sign.text


def test_qms_transition_requires_permission(client, seeded_db):
    admin_token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    operator_token = _login(client, "operator", "Operator1234!")
    now = datetime.now(timezone.utc).isoformat()

    create = client.post(
        "/api/v1/qms/deviations",
        headers=_auth_header(admin_token),
        json={
            "title": "Minor event for permission test",
            "deviation_type": "unplanned",
            "category": "process",
            "description": "Minor event used only to verify permission guardrails on transitions.",
            "detected_during": "line setup",
            "detection_date": now,
            "risk_level": "low",
            "immediate_action": "Documented and held material.",
        },
    )
    assert create.status_code == 201, create.text
    deviation_id = create.json()["id"]

    forbidden = client.post(
        f"/api/v1/qms/deviations/{deviation_id}/submit",
        headers=_auth_header(operator_token),
    )
    assert forbidden.status_code == 403, forbidden.text
