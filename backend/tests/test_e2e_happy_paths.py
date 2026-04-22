from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.modules.qms.models import CAPA


def _login(client, username: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password, "totp_code": None},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["tokens"]["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_e2e_happy_paths_all_modules(client, seeded_db, monkeypatch, session_maker):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    me = client.get("/api/v1/auth/me", headers=_auth(token)).json()

    # (1) QMS: create CAPA, sign closed/approved
    async def _seed_capa() -> str:
        async with session_maker() as session:
            capa = CAPA(
                capa_number="CAPA-E2E-0001",
                title="E2E CAPA",
                capa_type="corrective",
                source="internal_audit",
                risk_level="medium",
                product_impact=False,
                patient_safety_impact=False,
                regulatory_reportable=False,
                problem_description="A detailed problem description for e2e CAPA coverage.",
                department="QA",
                identified_date=datetime.now(timezone.utc),
                site_id=me["site_id"],
                owner_id=me["id"],
                current_status="draft",
            )
            session.add(capa)
            await session.flush([capa])
            await session.commit()
            return capa.id

    import asyncio

    capa_id = asyncio.run(_seed_capa())

    capa_sign = client.post(
        f"/api/v1/qms/capas/{capa_id}/sign",
        headers=_auth(token),
        json={"password": seeded_db["admin_password"], "meaning": "closed", "comments": "e2e"},
    )
    assert capa_sign.status_code == 200, capa_sign.text

    # (2) MES: create product, mbr, execute step, release
    product = client.post(
        "/api/v1/mes/products",
        headers=_auth(token),
        json={
            "product_code": "E2E-PROD",
            "name": "E2E Product",
            "product_type": "drug_product",
            "unit_of_measure": "kg",
            "site_id": me["site_id"],
        },
    )
    assert product.status_code == 201, product.text
    product_id = product.json()["id"]

    mbr = client.post(
        "/api/v1/mes/mbrs",
        headers=_auth(token),
        json={
            "product_id": product_id,
            "version": "1.0",
            "batch_size": 10.0,
            "batch_size_unit": "kg",
            "steps": [
                {
                    "step_number": 1,
                    "phase": "mixing",
                    "title": "Mix",
                    "instructions": "Mix contents thoroughly for required interval.",
                    "step_type": "action",
                }
            ],
        },
    )
    assert mbr.status_code == 201, mbr.text
    mbr_id = mbr.json()["id"]

    mbr_sign = client.post(
        f"/api/v1/mes/mbrs/{mbr_id}/sign",
        headers=_auth(token),
        json={"password": seeded_db["admin_password"], "meaning": "approved"},
    )
    assert mbr_sign.status_code == 200, mbr_sign.text

    batch = client.post(
        "/api/v1/mes/batch-records",
        headers=_auth(token),
        json={"master_batch_record_id": mbr_id, "batch_number": "E2E-BATCH-001"},
    )
    assert batch.status_code == 201, batch.text
    batch_id = batch.json()["id"]

    batch_detail = client.get(f"/api/v1/mes/batch-records/{batch_id}", headers=_auth(token))
    assert batch_detail.status_code == 200, batch_detail.text
    step_id = batch_detail.json()["steps"][0]["id"]

    execute = client.patch(
        f"/api/v1/mes/batch-records/{batch_id}/steps/{step_id}",
        headers=_auth(token),
        json={"recorded_value": "done", "is_na": False, "comments": "e2e"},
    )
    assert execute.status_code == 200, execute.text

    release = client.post(
        f"/api/v1/mes/batch-records/{batch_id}/release",
        headers=_auth(token),
        json={"password": seeded_db["admin_password"], "decision": "released", "comments": "e2e"},
    )
    assert release.status_code == 200, release.text

    # (3) Equipment: record calibration
    equipment = client.post(
        "/api/v1/equipment",
        headers=_auth(token),
        json={
            "equipment_id": "E2E-EQ-01",
            "name": "E2E Reactor",
            "equipment_type": "process_equipment",
            "site_id": me["site_id"],
            "location": "Line 1",
        },
    )
    assert equipment.status_code == 201, equipment.text
    equipment_id = equipment.json()["id"]

    calibration = client.post(
        f"/api/v1/equipment/{equipment_id}/calibrations",
        headers=_auth(token),
        json={
            "calibration_type": "scheduled",
            "performed_at": datetime.now(timezone.utc).isoformat(),
            "calibration_interval_days": 30,
            "result": "pass",
        },
    )
    assert calibration.status_code == 201, calibration.text

    # (4) Training: assign and complete
    curricula = client.get("/api/v1/training/curricula", headers=_auth(token))
    assert curricula.status_code == 200, curricula.text
    curriculum_id = curricula.json()[0]["id"]

    curriculum_detail = client.get(f"/api/v1/training/curricula/{curriculum_id}", headers=_auth(token))
    assert curriculum_detail.status_code == 200, curriculum_detail.text
    item_id = curriculum_detail.json()["items"][0]["id"]

    assignment = client.post(
        "/api/v1/training/assignments",
        headers=_auth(token),
        json={
            "user_id": me["id"],
            "curriculum_item_id": item_id,
            "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
    )
    assert assignment.status_code == 201, assignment.text
    assignment_id = assignment.json()["id"]

    complete = client.post(
        f"/api/v1/training/assignments/{assignment_id}/read-and-understood",
        headers=_auth(token),
        json={"password": seeded_db["admin_password"], "notes": "e2e"},
    )
    assert complete.status_code == 200, complete.text

    # (5) LIMS: OOS result auto-creates deviation
    sample = client.post(
        "/api/v1/lims/samples",
        headers=_auth(token),
        json={
            "sample_number": "E2E-SAMPLE-001",
            "sample_type": "finished_product",
            "sampled_at": datetime.now(timezone.utc).isoformat(),
            "site_id": me["site_id"],
        },
    )
    assert sample.status_code == 201, sample.text
    sample_id = sample.json()["id"]

    oos = client.post(
        f"/api/v1/lims/samples/{sample_id}/results",
        headers=_auth(token),
        json={
            "test_method_id": "E2E-METHOD",
            "result_value": "999.0",
            "result_numeric": 999.0,
            "unit": "%",
            "tested_at": datetime.now(timezone.utc).isoformat(),
            "is_oos": True,
            "spec_limit": "<= 102.0",
        },
    )
    assert oos.status_code == 201, oos.text

    deviations = client.get("/api/v1/qms/deviations", headers=_auth(token))
    assert deviations.status_code == 200, deviations.text
    assert any("Out-of-specification result detected automatically" in (d.get("description") or "") for d in deviations.json())

    # (6) ENV: alert-limit exceedance and notification event
    captured_events: list[str] = []

    async def _capture_send_event(_session, event_type: str, **kwargs):
        captured_events.append(event_type)
        return 1

    monkeypatch.setattr("app.modules.env_monitoring.services.NotificationService.send_event", _capture_send_event)

    location = client.post(
        "/api/v1/env-monitoring/locations",
        headers=_auth(token),
        json={
            "code": "E2E-ENV-LOC",
            "name": "E2E Cleanroom",
            "room": "A-01",
            "gmp_grade": "A",
            "site_id": me["site_id"],
        },
    )
    assert location.status_code == 201, location.text
    location_id = location.json()["id"]

    limits = client.post(
        f"/api/v1/env-monitoring/locations/{location_id}/limits",
        headers=_auth(token),
        json={
            "parameter": "total_viable_count",
            "unit": "CFU/m3",
            "alert_limit": 10.0,
            "action_limit": 20.0,
        },
    )
    assert limits.status_code == 201, limits.text

    env_result = client.post(
        f"/api/v1/env-monitoring/locations/{location_id}/results",
        headers=_auth(token),
        json={
            "parameter": "total_viable_count",
            "sampling_method": "settle_plate",
            "sampled_at": datetime.now(timezone.utc).isoformat(),
            "result_value": 25.0,
            "unit": "CFU/m3",
            "comments": "e2e",
        },
    )
    assert env_result.status_code == 201, env_result.text
    assert env_result.json()["status"] == "action"
    assert "env_monitoring.alert_exceeded" in captured_events

