from types import SimpleNamespace

from app.core.auth.service import AuthService


def _user() -> SimpleNamespace:
    return SimpleNamespace(id="u1", username="admin", email="admin@example.com")


def test_password_strength_requires_lowercase():
    errors = AuthService.validate_password_strength("ABCDEFGH1234!")
    assert any("lowercase" in e.lower() for e in errors)


def test_password_strength_accepts_valid_password():
    errors = AuthService.validate_password_strength("ValidPass123!")
    assert errors == []


def test_access_token_type_is_access():
    token, _exp = AuthService.create_access_token(_user())
    payload = AuthService.decode_token(token)
    assert payload is not None
    assert payload["type"] == "access"
    assert payload["sub"] == "u1"


def test_refresh_token_type_is_refresh():
    token, _exp = AuthService.create_refresh_token(_user())
    payload = AuthService.decode_token(token)
    assert payload is not None
    assert payload["type"] == "refresh"
    assert payload["sub"] == "u1"
