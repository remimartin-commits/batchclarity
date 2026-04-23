from __future__ import annotations


def _login(client, username: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password, "totp_code": None},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["tokens"]["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_mes_product_mbr_batch_execution_release_flow(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])

    created_product = client.post(
        "/api/v1/mes/products",
        headers=_auth_header(token),
        json={
            "product_code": "P-001",
            "name": "Demo Product",
            "product_type": "drug_product",
            "unit_of_measure": "kg",
            "site_id": "SITE-1",
        },
    )
    assert created_product.status_code == 201, created_product.text
    product_id = created_product.json()["id"]

    created_mbr = client.post(
        "/api/v1/mes/mbrs",
        headers=_auth_header(token),
        json={
            "product_id": product_id,
            "version": "1.0",
            "batch_size": 100.0,
            "batch_size_unit": "kg",
            "description": "Demo MBR",
            "steps": [
                {
                    "step_number": 1,
                    "phase": "prep",
                    "title": "Weigh material",
                    "instructions": "Weigh the lot and verify the measured quantity.",
                    "step_type": "measurement",
                    "is_critical": True,
                }
            ],
        },
    )
    assert created_mbr.status_code == 201, created_mbr.text
    mbr_id = created_mbr.json()["id"]

    sign = client.post(
        f"/api/v1/mes/mbrs/{mbr_id}/sign",
        headers=_auth_header(token),
        json={"password": seeded_db["admin_password"], "meaning": "approved"},
    )
    assert sign.status_code == 200, sign.text

    created_batch = client.post(
        "/api/v1/mes/batch-records",
        headers=_auth_header(token),
        json={"master_batch_record_id": mbr_id, "batch_number": "BATCH-001"},
    )
    assert created_batch.status_code == 201, created_batch.text
    batch_id = created_batch.json()["id"]

    batch_detail = client.get(
        f"/api/v1/mes/batch-records/{batch_id}", headers=_auth_header(token)
    )
    assert batch_detail.status_code == 200, batch_detail.text
    step_id = batch_detail.json()["steps"][0]["id"]

    executed_step = client.patch(
        f"/api/v1/mes/batch-records/{batch_id}/steps/{step_id}",
        headers=_auth_header(token),
        json={
            "recorded_value": "100.0",
            "is_na": False,
            "comments": "OK",
            "password": seeded_db["admin_password"],
        },
    )
    assert executed_step.status_code == 200, executed_step.text
    assert executed_step.json()["status"] in {"completed", "deviated"}

    released = client.post(
        f"/api/v1/mes/batch-records/{batch_id}/release",
        headers=_auth_header(token),
        json={"password": seeded_db["admin_password"], "decision": "released"},
    )
    assert released.status_code == 200, released.text
    assert released.json()["decision"] == "released"


def test_mes_list_endpoints_return_data(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])

    products = client.get("/api/v1/mes/products", headers=_auth_header(token))
    assert products.status_code == 200, products.text

    mbrs = client.get("/api/v1/mes/mbrs", headers=_auth_header(token))
    assert mbrs.status_code == 200, mbrs.text

    batches = client.get("/api/v1/mes/batch-records", headers=_auth_header(token))
    assert batches.status_code == 200, batches.text


def test_mes_cannot_release_batch_with_open_deviation_link(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])

    created_product = client.post(
        "/api/v1/mes/products",
        headers=_auth_header(token),
        json={
            "product_code": "P-OD-001",
            "name": "Open Deviation Product",
            "product_type": "drug_product",
            "unit_of_measure": "kg",
            "site_id": "SITE-1",
        },
    )
    assert created_product.status_code == 201, created_product.text
    product_id = created_product.json()["id"]

    created_mbr = client.post(
        "/api/v1/mes/mbrs",
        headers=_auth_header(token),
        json={
            "product_id": product_id,
            "version": "1.0",
            "batch_size": 100.0,
            "batch_size_unit": "kg",
            "description": "MBR for open deviation release-block test",
            "steps": [
                {
                    "step_number": 1,
                    "phase": "prep",
                    "title": "Weigh material",
                    "instructions": "Weigh and verify quantity.",
                    "step_type": "measurement",
                    "is_critical": False,
                }
            ],
        },
    )
    assert created_mbr.status_code == 201, created_mbr.text
    mbr_id = created_mbr.json()["id"]

    approve_mbr = client.post(
        f"/api/v1/mes/mbrs/{mbr_id}/sign",
        headers=_auth_header(token),
        json={"password": seeded_db["admin_password"], "meaning": "approved"},
    )
    assert approve_mbr.status_code == 200, approve_mbr.text

    batch_number = "BATCH-OPEN-DEV-001"
    created_batch = client.post(
        "/api/v1/mes/batch-records",
        headers=_auth_header(token),
        json={"master_batch_record_id": mbr_id, "batch_number": batch_number},
    )
    assert created_batch.status_code == 201, created_batch.text
    batch_id = created_batch.json()["id"]

    deviation = client.post(
        "/api/v1/qms/deviations",
        headers=_auth_header(token),
        json={
            "title": "Deviation linked to MES batch",
            "deviation_type": "process",
            "gmp_impact_classification": "major",
            "description": "Open deviation linked to batch should block MES release.",
            "detected_during": "manufacturing",
            "detection_date": "2026-01-01T00:00:00Z",
            "risk_level": "high",
            "product_affected": "Open Deviation Product",
            "batches_affected": [batch_number],
            "immediate_action": "Contained.",
            "immediate_containment_actions": "Contained.",
        },
    )
    assert deviation.status_code == 201, deviation.text

    release_attempt = client.post(
        f"/api/v1/mes/batch-records/{batch_id}/release",
        headers=_auth_header(token),
        json={"password": seeded_db["admin_password"], "decision": "released"},
    )
    assert release_attempt.status_code == 400, release_attempt.text

