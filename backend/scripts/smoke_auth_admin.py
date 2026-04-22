"""
Lightweight API smoke test:
1) login
2) me
3) users list (admin permission path)
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import httpx


def _die(message: str) -> None:
    print(f"[smoke] FAIL: {message}")
    raise SystemExit(1)


def _ok(message: str) -> None:
    print(f"[smoke] OK: {message}")


def _parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run auth/admin API smoke checks.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="API base URL")
    parser.add_argument("--username", required=True, help="Username for login")
    parser.add_argument("--password", required=True, help="Password for login")
    parser.add_argument("--totp-code", default=None, help="Optional TOTP code if MFA is enabled")
    parser.add_argument("--timeout", type=float, default=20.0, help="Request timeout in seconds")
    return parser.parse_args()


def _require_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except Exception as exc:  # pragma: no cover - smoke script runtime safeguard
        _die(f"Invalid JSON response from {resp.request.url}: {exc}")


def main() -> int:
    args = _parse()
    with httpx.Client(timeout=args.timeout) as client:
        payload: dict[str, Any] = {"username": args.username, "password": args.password}
        if args.totp_code:
            payload["totp_code"] = args.totp_code
        login_resp = client.post(f"{args.base_url}/api/v1/auth/login", json=payload)
        if login_resp.status_code != 200:
            _die(f"Login failed ({login_resp.status_code}): {login_resp.text}")
        login = _require_json(login_resp)
        token_payload = login.get("tokens") if isinstance(login.get("tokens"), dict) else login
        access = token_payload.get("access_token")
        refresh = token_payload.get("refresh_token")
        if not access or not refresh:
            _die("Login response missing tokens.")
        _ok("login")

        headers = {"Authorization": f"Bearer {access}"}
        me_resp = client.get(f"{args.base_url}/api/v1/auth/me", headers=headers)
        if me_resp.status_code != 200:
            _die(f"/auth/me failed ({me_resp.status_code}): {me_resp.text}")
        me = _require_json(me_resp)
        if not me.get("id") or not me.get("username"):
            _die("/auth/me returned incomplete user payload.")
        _ok("me")

        users_resp = client.get(f"{args.base_url}/api/v1/users", headers=headers)
        if users_resp.status_code != 200:
            _die(f"/users failed ({users_resp.status_code}): {users_resp.text}")
        users = _require_json(users_resp)
        if not isinstance(users, list):
            _die("/users payload is not a list.")
        _ok(f"users ({len(users)} records)")

        # QMS list -> detail -> update smoke
        deviations_resp = client.get(f"{args.base_url}/api/v1/qms/deviations", headers=headers)
        if deviations_resp.status_code != 200:
            _die(f"/qms/deviations failed ({deviations_resp.status_code}): {deviations_resp.text}")
        deviations = _require_json(deviations_resp)
        if not isinstance(deviations, list):
            _die("/qms/deviations payload is not a list.")
        _ok(f"qms deviations list ({len(deviations)} records)")

        if deviations:
            deviation_id = deviations[0].get("id")
            if deviation_id:
                detail_resp = client.get(
                    f"{args.base_url}/api/v1/qms/deviations/{deviation_id}", headers=headers
                )
                if detail_resp.status_code != 200:
                    _die(f"/qms/deviations/{{id}} failed ({detail_resp.status_code}): {detail_resp.text}")
                _ok("qms deviation detail")

                patch_resp = client.patch(
                    f"{args.base_url}/api/v1/qms/deviations/{deviation_id}",
                    headers=headers,
                    json={"root_cause": "Smoke test update"},
                )
                if patch_resp.status_code != 200:
                    _die(f"/qms/deviations/{{id}} update failed ({patch_resp.status_code}): {patch_resp.text}")
                _ok("qms deviation update")
            else:
                _ok("qms deviation detail/update skipped (missing id field)")
        else:
            _ok("qms deviation detail/update skipped (no records yet)")

        # Documents quick check
        doc_types = client.get(f"{args.base_url}/api/v1/documents/types", headers=headers)
        if doc_types.status_code != 200:
            _die(f"/documents/types failed ({doc_types.status_code}): {doc_types.text}")
        _ok("documents types")

        docs = client.get(f"{args.base_url}/api/v1/documents", headers=headers)
        if docs.status_code != 200:
            _die(f"/documents failed ({docs.status_code}): {docs.text}")
        _ok("documents list")

        # Training quick check
        curricula = client.get(f"{args.base_url}/api/v1/training/curricula", headers=headers)
        if curricula.status_code != 200:
            _die(f"/training/curricula failed ({curricula.status_code}): {curricula.text}")
        _ok("training curricula")

        assignments = client.get(f"{args.base_url}/api/v1/training/assignments", headers=headers)
        if assignments.status_code != 200:
            _die(f"/training/assignments failed ({assignments.status_code}): {assignments.text}")
        _ok("training assignments")

        # Equipment quick check
        equipment = client.get(f"{args.base_url}/api/v1/equipment", headers=headers)
        if equipment.status_code != 200:
            _die(f"/equipment failed ({equipment.status_code}): {equipment.text}")
        _ok("equipment list")

    print("[smoke] PASS: auth -> admin -> qms -> documents -> training -> equipment")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("[smoke] Interrupted by user.")
        sys.exit(130)
