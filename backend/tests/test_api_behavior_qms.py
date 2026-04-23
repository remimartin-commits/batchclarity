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
            "deviation_type": "process",
            "gmp_impact_classification": "major",
            "description": "Hold time exceeded by 3 hours before filtration step during batch execution.",
            "detected_during": "manufacturing",
            "detection_date": now,
            "risk_level": "high",
            "immediate_action": "Quarantined in-process material and notified QA immediately.",
            "immediate_containment_actions": "Quarantined in-process material and notified QA immediately.",
        },
    )
    assert create.status_code == 201, create.text
    deviation = create.json()
    deviation_id = deviation["id"]
    assert deviation["deviation_number"].startswith("DEV-")

    patch = client.patch(
        f"/api/v1/qms/deviations/{deviation_id}",
        headers=_auth_header(token),
        json={
            "current_status": "under_investigation",
            "root_cause": "Operator delay due to line clearance issue.",
            "root_cause_category": "human_error",
        },
    )
    assert patch.status_code == 200, patch.text
    updated = patch.json()
    assert updated["current_status"] == "under_investigation"

    filtered = client.get(
        "/api/v1/qms/deviations",
        headers=_auth_header(token),
        params={"status_filter": "under_investigation"},
    )
    assert filtered.status_code == 200, filtered.text
    ids = {item["id"] for item in filtered.json()}
    assert deviation_id in ids

    transition = client.post(
        f"/api/v1/qms/deviations/{deviation_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "pending_approval",
            "comments": "Approved for closure decision.",
        },
    )
    assert transition.status_code == 200, transition.text
    refreshed = client.get(
        f"/api/v1/qms/deviations/{deviation_id}",
        headers=_auth_header(token),
    )
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["current_status"] == "pending_approval"

    sign = client.post(
        f"/api/v1/qms/deviations/{deviation_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "closed",
            "comments": "Checked.",
            "no_capa_needed_confirmed": True,
            "no_capa_needed_justification": "Investigated and corrected without CAPA.",
        },
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
    day_after = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    filing_deadline = (datetime.now(timezone.utc) + timedelta(days=120)).isoformat()

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
            "regulatory_filing_required": True,
            "regulatory_filing_type": "pas",
            "regulatory_filing_deadline": filing_deadline,
            "validation_required": True,
            "validation_qualification_required": True,
            "validation_scope_description": "IQ/OQ for updated cleaning process limits.",
            "affected_document_ids": [],
            "affected_equipment_ids": [],
            "affected_sop_document_ids": [],
            "implementation_plan": "Perform phased rollout and qualification on line 1.",
            "implementation_target_date": tomorrow,
            "pre_change_verification_checklist": [{"item": "Training complete", "result": "yes"}],
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
            "post_change_effectiveness_date": day_after,
            "post_change_effectiveness_outcome": "Change effective",
            "qualification_record_id": "QUAL-0001",
            "qualification_status": "approved",
        },
    )
    assert patch.status_code == 200, patch.text

    filtered = client.get(
        "/api/v1/qms/change-controls",
        headers=_auth_header(token),
        params={"status_filter": "draft"},
    )
    assert filtered.status_code == 200, filtered.text
    ids = {item["id"] for item in filtered.json()}
    assert cc_id in ids

    submit = client.post(
        f"/api/v1/qms/change-controls/{cc_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "under_review",
            "comments": "Submitted for review.",
        },
    )
    assert submit.status_code == 200, submit.text
    current = client.get(f"/api/v1/qms/change-controls/{cc_id}", headers=_auth_header(token))
    assert current.status_code == 200, current.text
    assert current.json()["current_status"] == "under_review"

    initiator_approval = client.post(
        f"/api/v1/qms/change-controls/{cc_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "initiator_approved",
            "comments": "Initiator approval.",
        },
    )
    assert initiator_approval.status_code == 200, initiator_approval.text
    current = client.get(f"/api/v1/qms/change-controls/{cc_id}", headers=_auth_header(token))
    assert current.status_code == 200, current.text
    assert current.json()["current_status"] == "under_review"

    qa_approval = client.post(
        f"/api/v1/qms/change-controls/{cc_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "qa_approved",
            "comments": "QA approval.",
        },
    )
    assert qa_approval.status_code == 200, qa_approval.text
    current = client.get(f"/api/v1/qms/change-controls/{cc_id}", headers=_auth_header(token))
    assert current.status_code == 200, current.text
    assert current.json()["current_status"] == "approved"

    implement = client.post(
        f"/api/v1/qms/change-controls/{cc_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "in_implementation",
            "comments": "Implementation started.",
        },
    )
    assert implement.status_code == 200, implement.text

    effectiveness = client.post(
        f"/api/v1/qms/change-controls/{cc_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "effectiveness_review",
            "comments": "Reviewing effectiveness.",
        },
    )
    assert effectiveness.status_code == 200, effectiveness.text

    close = client.post(
        f"/api/v1/qms/change-controls/{cc_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "closed",
            "comments": "Closed after effectiveness review.",
        },
    )
    assert close.status_code == 200, close.text


def test_qms_change_control_emergency_director_approval_path(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    target = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    create = client.post(
        "/api/v1/qms/change-controls",
        headers=_auth_header(token),
        json={
            "title": "Emergency sterile filter replacement",
            "change_type": "equipment",
            "change_category": "emergency",
            "description": "Emergency replacement required to prevent line shutdown and contamination risk.",
            "justification": "Unexpected integrity failure during production campaign.",
            "regulatory_impact": False,
            "regulatory_filing_required": False,
            "validation_required": False,
            "validation_qualification_required": False,
            "implementation_plan": "Install validated spare, execute emergency checks, and document retrospective review.",
            "implementation_target_date": target,
            "pre_change_verification_checklist": [{"item": "Spare availability", "result": "yes"}],
        },
    )
    assert create.status_code == 201, create.text
    cc_id = create.json()["id"]

    emergency_approve = client.post(
        f"/api/v1/qms/change-controls/{cc_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "qa_director_emergency_approved",
            "comments": "Director emergency approval",
        },
    )
    assert emergency_approve.status_code == 403, emergency_approve.text


def test_qms_change_control_validation_required_blocks_close_without_qualification(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    day_after = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    create = client.post(
        "/api/v1/qms/change-controls",
        headers=_auth_header(token),
        json={
            "title": "Validation-bound process parameter update",
            "change_type": "process",
            "change_category": "major",
            "description": "Change requires validation record before closure per GMP rule.",
            "justification": "Reduce process variability while preserving critical quality attributes.",
            "regulatory_impact": False,
            "regulatory_filing_required": False,
            "validation_required": True,
            "validation_qualification_required": True,
            "validation_scope_description": "PQ confirmation after implementation",
            "implementation_plan": "Execute update and validate against approved protocol.",
            "implementation_target_date": tomorrow,
            "pre_change_verification_checklist": [{"item": "Protocol drafted", "result": "yes"}],
        },
    )
    assert create.status_code == 201, create.text
    cc_id = create.json()["id"]

    patch = client.patch(
        f"/api/v1/qms/change-controls/{cc_id}",
        headers=_auth_header(token),
        json={"post_change_effectiveness_date": day_after, "post_change_effectiveness_outcome": "effective"},
    )
    assert patch.status_code == 200, patch.text

    for meaning in ["under_review", "initiator_approved", "qa_approved", "in_implementation", "effectiveness_review"]:
        transition = client.post(
            f"/api/v1/qms/change-controls/{cc_id}/sign",
            headers=_auth_header(token),
            json={
                "username": seeded_db["admin_username"],
                "password": seeded_db["admin_password"],
                "meaning": meaning,
                "comments": f"{meaning} transition",
            },
        )
        assert transition.status_code == 200, transition.text

    close = client.post(
        f"/api/v1/qms/change-controls/{cc_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "closed",
            "comments": "Attempt close without qualification approval",
        },
    )
    assert close.status_code == 400, close.text


def test_qms_transition_requires_permission(client, seeded_db):
    admin_token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    operator_token = _login(client, "operator", "Operator1234!")
    now = datetime.now(timezone.utc).isoformat()

    create = client.post(
        "/api/v1/qms/deviations",
        headers=_auth_header(admin_token),
        json={
            "title": "Minor event for permission test",
            "deviation_type": "process",
            "gmp_impact_classification": "minor",
            "description": "Minor event used only to verify permission guardrails on transitions.",
            "detected_during": "line setup",
            "detection_date": now,
            "risk_level": "low",
            "immediate_action": "Documented and held material.",
            "immediate_containment_actions": "Documented and held material.",
        },
    )
    assert create.status_code == 201, create.text
    deviation_id = create.json()["id"]

    forbidden = client.post(
        f"/api/v1/qms/deviations/{deviation_id}/sign",
        headers=_auth_header(operator_token),
        json={
            "username": "operator",
            "password": "Operator1234!",
            "meaning": "under_investigation",
            "comments": "Attempt transition",
        },
    )
    assert forbidden.status_code == 403, forbidden.text


def test_qms_deviation_close_with_patient_impact_requires_director(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    now = datetime.now(timezone.utc).isoformat()

    create = client.post(
        "/api/v1/qms/deviations",
        headers=_auth_header(token),
        json={
            "title": "Potential patient impact deviation",
            "deviation_type": "process",
            "gmp_impact_classification": "major",
            "description": "Potential patient impact scenario that requires director-level closure sign-off.",
            "detected_during": "manufacturing",
            "detection_date": now,
            "risk_level": "critical",
            "product_affected": "Drug Product X",
            "batches_affected": ["BATCH-PATIENT-001"],
            "immediate_action": "Contained and investigated.",
            "immediate_containment_actions": "Contained and investigated.",
            "potential_patient_impact": True,
            "potential_patient_impact_justification": "Potentially impacted quality attributes.",
            "root_cause": "In-process parameter excursion",
            "requires_capa": True,
        },
    )
    assert create.status_code == 201, create.text
    deviation_id = create.json()["id"]

    under_investigation = client.post(
        f"/api/v1/qms/deviations/{deviation_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "under_investigation",
            "comments": "Move to under investigation",
        },
    )
    assert under_investigation.status_code == 200, under_investigation.text

    pending_approval = client.post(
        f"/api/v1/qms/deviations/{deviation_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "pending_approval",
            "comments": "Ready for QA closure decision",
        },
    )
    assert pending_approval.status_code == 200, pending_approval.text

    close_attempt = client.post(
        f"/api/v1/qms/deviations/{deviation_id}/sign",
        headers=_auth_header(token),
        json={
            "username": seeded_db["admin_username"],
            "password": seeded_db["admin_password"],
            "meaning": "closed",
            "comments": "Close attempt by non-director role",
        },
    )
    assert close_attempt.status_code == 403, close_attempt.text
