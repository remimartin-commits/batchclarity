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


def test_dashboard_summary_smoke(client, seeded_db):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    r = client.get("/api/v1/dashboard/summary", headers=_auth_header(token))
    assert r.status_code == 200, r.text
    data = r.json()
    for key in (
        "open_capas",
        "overdue_capas",
        "open_deviations",
        "overdue_deviations",
        "pending_change_controls",
        "calibrations_due_30_days",
        "calibrations_overdue",
        "open_oos_investigations",
        "documents_expiring_60_days",
        "training_overdue",
        "pending_my_signatures",
    ):
        assert key in data
        assert isinstance(data[key], int)
        assert data[key] >= 0
    assert isinstance(data.get("pending_my_actions"), list)
