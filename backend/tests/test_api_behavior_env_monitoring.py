from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.notify.service import NotificationService


def _login(client, username: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password, "totp_code": None},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["tokens"]["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_env_location_limit_result_flow_with_alert_notification(client, seeded_db, monkeypatch):
    token = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    me = client.get("/api/v1/auth/me", headers=_auth_header(token)).json()
    sent_events: list[dict] = []

    async def _capture_send_event(
        _session,
        *,
        event_type: str,
        record_type: str,
        record_id: str,
        variables: dict,
        site_id: str | None = None,
        **_kwargs,
    ) -> int:
        sent_events.append(
            {
                "event_type": event_type,
                "record_type": record_type,
                "record_id": record_id,
                "variables": variables,
                "site_id": site_id,
            }
        )
        return 1

    monkeypatch.setattr(NotificationService, "send_event", _capture_send_event)

    loc = client.post(
        "/api/v1/env-monitoring/locations",
        headers=_auth_header(token),
        json={
            "code": "EM-A1",
            "name": "Grade A Filling Zone",
            "room": "A-100",
            "gmp_grade": "A",
            "site_id": me["site_id"],
        },
    )
    assert loc.status_code == 201, loc.text
    loc_id = loc.json()["id"]

    limit = client.post(
        f"/api/v1/env-monitoring/locations/{loc_id}/limits",
        headers=_auth_header(token),
        json={
            "parameter": "particles_0_5um",
            "unit": "particles/m3",
            "alert_limit": 100.0,
            "action_limit": 150.0,
        },
    )
    assert limit.status_code == 201, limit.text

    entered = client.post(
        f"/api/v1/env-monitoring/locations/{loc_id}/results",
        headers=_auth_header(token),
        json={
            "parameter": "particles_0_5um",
            "sampling_method": "particle_counter",
            "sampled_at": datetime.now(timezone.utc).isoformat(),
            "result_value": 120.0,
            "unit": "particles/m3",
        },
    )
    assert entered.status_code == 201, entered.text
    assert entered.json()["status"] == "alert"
    assert entered.json()["exceeds_alert_limit"] is True

    listed = client.get("/api/v1/env-monitoring/results", headers=_auth_header(token))
    assert listed.status_code == 200, listed.text
    assert len(listed.json()) >= 1

    assert sent_events
    assert sent_events[0]["event_type"] == "env_monitoring.alert_exceeded"

