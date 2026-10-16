import pytest

from app.modules.users.models import Role
from tests.helpers import make_customer, make_staff

PROTECTED = [
    ("GET", "/api/v1/me/profile"),
    ("GET", "/api/v1/orders"),
    ("GET", "/api/v1/orders/1"),
    ("POST", "/api/v1/orders"),
    ("GET", "/api/v1/orders/summary"),
    ("GET", "/api/v1/ingredients"),
    ("GET", "/api/v1/staff"),
    ("GET", "/api/v1/reports/sales"),
    ("GET", "/api/v1/menu-items/1"),
    ("POST", "/api/v1/menu-items"),
]

MANAGER_ONLY = [
    ("GET", "/api/v1/ingredients"),
    ("POST", "/api/v1/menu-items"),
    ("GET", "/api/v1/staff"),
    ("GET", "/api/v1/reports/sales"),
    ("POST", "/api/v1/orders/1/actions/accept"),
]


@pytest.mark.parametrize(("method", "url"), PROTECTED)
def test_protected_routes_require_login(api, method, url):
    response = api.request(method, url, json={} if method == "POST" else None)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


@pytest.mark.parametrize(("method", "url"), MANAGER_ONLY)
def test_customer_cannot_use_manager_routes(api, db, method, url):
    make_customer(db, username="joao")
    api.login("joao")
    response = api.request(
        method,
        url,
        json={"name": "x", "price": "1", "category_id": 1} if method == "POST" else None,
    )
    assert response.status_code in (403, 404)
    if response.status_code == 404:  # ação em pedido inexistente: não revela nada
        assert url.endswith("/accept")


def test_unsafe_requests_without_csrf_header_are_rejected(api, db):
    manager = make_staff(db, Role.MANAGER)
    api.login(manager.cpf)
    response = api.post(
        "/api/v1/ingredients",
        json={"name": "Bacon", "quantity": 1},
        headers={"X-CSRF-Token": ""},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"


def test_security_headers(api):
    response = api.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "same-origin"
    assert len(response.headers["X-Request-ID"]) == 12


def test_sql_injection_in_search_is_treated_as_text(api, db, menu):
    manager = make_staff(db, Role.MANAGER)
    api.login(manager.cpf)
    response = api.get("/api/v1/orders", params={"q": "' OR 1=1 --"})
    assert response.status_code == 200
    assert response.json()["total"] == 0
    response = api.get("/api/v1/ingredients", params={"q": "%"})
    assert response.json()["items"] == []  # "%" é procurado literalmente


def test_unknown_routes_use_the_standard_error_format(api):
    response = api.get("/api/v1/nao-existe")
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "http_error", "message": "Recurso não encontrado.", "fields": {}}
    }


def test_invalid_json_body(api):
    response = api.post(
        "/api/v1/auth/login", content=b"{nao-e-json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
