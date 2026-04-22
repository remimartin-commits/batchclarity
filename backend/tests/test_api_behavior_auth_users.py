def _login(client, username: str, password: str):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password, "totp_code": None},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return data["tokens"]["access_token"], data["tokens"]["refresh_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_login_me_refresh_flow(client, seeded_db):
    access, refresh = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])

    me = client.get("/api/v1/auth/me", headers=_auth_header(access))
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["username"] == "admin"
    assert "admin.users.manage" in body["permissions"]

    rf = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert rf.status_code == 200, rf.text
    new_tokens = rf.json()
    assert new_tokens["token_type"] == "bearer"
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]


def test_users_endpoint_forbidden_without_permission(client):
    access, _refresh = _login(client, "operator", "Operator1234!")
    resp = client.get("/api/v1/users", headers=_auth_header(access))
    assert resp.status_code == 403, resp.text


def test_users_endpoint_allowed_with_admin_permission(client, seeded_db):
    access, _refresh = _login(client, seeded_db["admin_username"], seeded_db["admin_password"])
    resp = client.get("/api/v1/users", headers=_auth_header(access))
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    usernames = {u["username"] for u in payload}
    assert "admin" in usernames
    assert "operator" in usernames

