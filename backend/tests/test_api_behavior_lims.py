from __future__ import annotations

from datetime import datetime, timezone

def _login(client, username: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password, "totp_code": None},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["tokens"]["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_lims_oos_result_auto_creates_qms_deviation(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    me = client.get("/api/v1/auth/me", headers=_auth_header(token)).json()

    sample = client.post(
        "/api/v1/lims/samples",
        headers=_auth_header(token),
        json={
            "sample_number": "SAMPLE-001",
            "sample_type": "finished_product",
            "sampled_at": datetime.now(timezone.utc).isoformat(),
            "site_id": me["site_id"],
        },
    )
    assert sample.status_code == 201, sample.text
    sample_id = sample.json()["id"]

    result = client.post(
        f"/api/v1/lims/samples/{sample_id}/results",
        headers=_auth_header(token),
        json={
            "test_method_id": "TM-DUMMY-ID",
            "result_value": "120.0",
            "result_numeric": 120.0,
            "unit": "%",
            "tested_at": datetime.now(timezone.utc).isoformat(),
            "is_oos": True,
            "spec_limit": "<= 102.0",
        },
    )
    assert result.status_code == 201, result.text
    assert result.json()["is_oos"] is True

    deviations = client.get("/api/v1/qms/deviations", headers=_auth_header(token))
    assert deviations.status_code == 200, deviations.text
    assert any(
        (d.get("title") or "").startswith("OOS Result:")
        and "Out-of-specification result detected automatically" in (d.get("description") or "")
        for d in deviations.json()
    )

    listed_results = client.get(
        f"/api/v1/lims/samples/{sample_id}/results", headers=_auth_header(token)
    )
    assert listed_results.status_code == 200, listed_results.text
    assert len(listed_results.json()) >= 1

