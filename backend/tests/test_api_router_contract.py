from app.api.v1.router import api_router
from app.core.auth.dependencies import get_current_user_with_permission


def _route(path: str, method: str):
    method = method.upper()
    for route in api_router.routes:
        if getattr(route, "path", None) == path and method in getattr(route, "methods", set()):
            return route
    return None


def test_users_routes_are_registered():
    assert (_route("/api/v1/users", "GET") or _route("/users", "GET")) is not None
    assert (_route("/api/v1/users", "POST") or _route("/users", "POST")) is not None
    assert (_route("/api/v1/users/roles", "GET") or _route("/users/roles", "GET")) is not None
    assert (_route("/api/v1/users/roles", "POST") or _route("/users/roles", "POST")) is not None
    assert (_route("/api/v1/users/roles/{role_id}", "PATCH") or _route("/users/roles/{role_id}", "PATCH")) is not None
    assert (_route("/api/v1/users/roles/{role_id}", "DELETE") or _route("/users/roles/{role_id}", "DELETE")) is not None
    assert (_route("/api/v1/users/permissions", "GET") or _route("/users/permissions", "GET")) is not None
    assert (
        _route("/api/v1/users/{user_id}/roles/{role_id}", "POST")
        or _route("/users/{user_id}/roles/{role_id}", "POST")
    ) is not None
    assert (
        _route("/api/v1/users/{user_id}/roles/{role_id}", "DELETE")
        or _route("/users/{user_id}/roles/{role_id}", "DELETE")
    ) is not None


def test_permission_dependency_factory_returns_callable():
    dep = get_current_user_with_permission("admin.users.manage")
    assert callable(dep)


def test_qms_routes_are_registered():
    assert (_route("/api/v1/qms/capas", "GET") or _route("/qms/capas", "GET")) is not None
    assert (_route("/api/v1/qms/capas", "POST") or _route("/qms/capas", "POST")) is not None
    assert (_route("/api/v1/qms/capas/{capa_id}", "PATCH") or _route("/qms/capas/{capa_id}", "PATCH")) is not None
    assert (_route("/api/v1/qms/deviations", "GET") or _route("/qms/deviations", "GET")) is not None
    assert (_route("/api/v1/qms/deviations", "POST") or _route("/qms/deviations", "POST")) is not None
    assert (
        _route("/api/v1/qms/deviations/{deviation_id}", "PATCH")
        or _route("/qms/deviations/{deviation_id}", "PATCH")
    ) is not None
    assert (
        _route("/api/v1/qms/deviations/{deviation_id}/sign", "POST")
        or _route("/qms/deviations/{deviation_id}/sign", "POST")
    ) is not None
    assert (
        _route("/api/v1/qms/deviations/{deviation_id}/{action}", "POST")
        or _route("/qms/deviations/{deviation_id}/{action}", "POST")
    ) is not None
    assert (
        _route("/api/v1/qms/change-controls", "GET")
        or _route("/qms/change-controls", "GET")
    ) is not None
    assert (
        _route("/api/v1/qms/change-controls", "POST")
        or _route("/qms/change-controls", "POST")
    ) is not None
    assert (
        _route("/api/v1/qms/change-controls/{cc_id}", "PATCH")
        or _route("/qms/change-controls/{cc_id}", "PATCH")
    ) is not None
    assert (
        _route("/api/v1/qms/change-controls/{cc_id}/sign", "POST")
        or _route("/qms/change-controls/{cc_id}/sign", "POST")
    ) is not None
    assert (
        _route("/api/v1/qms/change-controls/{cc_id}/{action}", "POST")
        or _route("/qms/change-controls/{cc_id}/{action}", "POST")
    ) is not None


def test_documents_training_equipment_routes_are_registered():
    assert (_route("/api/v1/documents", "GET") or _route("/documents", "GET")) is not None
    assert (_route("/api/v1/documents", "POST") or _route("/documents", "POST")) is not None
    assert (
        _route("/api/v1/documents/{doc_id}/versions", "POST")
        or _route("/documents/{doc_id}/versions", "POST")
    ) is not None
    assert (
        _route("/api/v1/documents/{doc_id}/versions/{version_id}/sign", "POST")
        or _route("/documents/{doc_id}/versions/{version_id}/sign", "POST")
    ) is not None

    assert (_route("/api/v1/training/curricula", "GET") or _route("/training/curricula", "GET")) is not None
    assert (
        _route("/api/v1/training/assignments/{assignment_id}", "GET")
        or _route("/training/assignments/{assignment_id}", "GET")
    ) is not None
    assert (
        _route("/api/v1/training/assignments/{assignment_id}/complete", "POST")
        or _route("/training/assignments/{assignment_id}/complete", "POST")
    ) is not None

    assert (_route("/api/v1/equipment", "GET") or _route("/equipment", "GET")) is not None
    assert (_route("/api/v1/equipment", "POST") or _route("/equipment", "POST")) is not None
    assert (
        _route("/api/v1/equipment/{eq_id}/status", "PATCH")
        or _route("/equipment/{eq_id}/status", "PATCH")
    ) is not None
