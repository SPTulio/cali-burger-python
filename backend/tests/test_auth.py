import bcrypt
from sqlalchemy import select

from app.modules.auth.models import AuthSession
from app.modules.users.models import Role, User
from tests.helpers import PASSWORD, make_customer, make_staff, random_cpf

REGISTER = {
    "username": "nova.cliente",
    "password": "segredo123",
    "password_confirmation": "segredo123",
    "name": "Nova Cliente",
    "email": "nova@exemplo.com",
    "cpf": "529.982.247-25",
    "birth_date": "1995-05-05",
    "address": {"state": "PR", "city": "Curitiba", "district": "Batel", "street": "Av. Batel, 1"},
}


def test_register_creates_customer_and_logs_in(api, db):
    response = api.post("/api/v1/auth/register", json=REGISTER)

    assert response.status_code == 201
    assert response.json()["user"]["role"] == "customer"
    cookie_header = response.headers.get_list("set-cookie")
    session_cookie = next(c for c in cookie_header if c.startswith("cb_session="))
    assert "httponly" in session_cookie.lower()
    assert "samesite=lax" in session_cookie.lower()

    user = db.scalar(select(User).where(User.username == "nova.cliente"))
    assert user.cpf == "52998224725"  # gravado só com dígitos
    assert user.password_hash.startswith("$2b$")  # nunca em texto puro
    assert user.address.city == "Curitiba"
    assert api.get("/api/v1/me/profile").status_code == 200


def test_register_reports_errors_per_field_in_portuguese(api):
    data = {
        **REGISTER,
        "username": "a!",
        "cpf": "111.111.111-11",
        "password_confirmation": "outra",
        "email": "sem-arroba",
        "birth_date": "2999-01-01",
        "name": "  ",
    }
    response = api.post("/api/v1/auth/register", json=data)

    assert response.status_code == 422
    fields = response.json()["error"]["fields"]
    assert fields["cpf"] == "CPF inválido."
    assert fields["password_confirmation"] == "As senhas não coincidem."
    assert fields["email"] == "E-mail inválido."
    assert fields["name"] == "Campo obrigatório."
    assert "username" in fields
    assert "birth_date" in fields


def test_register_rejects_duplicate_username_and_cpf(api, db):
    existing = make_customer(db, username="nova.cliente")
    response = api.post("/api/v1/auth/register", json={**REGISTER, "cpf": existing.cpf})

    assert response.status_code == 422
    fields = response.json()["error"]["fields"]
    assert fields["username"] == "Este usuário já está em uso."
    assert "cpf" in fields


def test_customer_logs_in_with_username_and_staff_with_cpf(make_api, db):
    make_customer(db, username="joao")
    manager = make_staff(db, Role.MANAGER, cpf="35265811001")

    customer = make_api().login("joao")
    assert customer.get("/api/v1/auth/me").json()["user"]["role"] == "customer"

    staff = make_api().login("352.658.110-01")  # aceita CPF com pontuação
    me = staff.get("/api/v1/auth/me").json()["user"]
    assert me["id"] == manager.id
    assert me["role"] == "manager"


def test_customer_cannot_log_in_with_cpf(api, db):
    customer = make_customer(db)
    response = api.post(
        "/api/v1/auth/login", json={"identifier": customer.cpf, "password": PASSWORD}
    )
    assert response.status_code == 401


def test_wrong_password_and_unknown_user_have_the_same_message(api, db):
    make_customer(db, username="joao")
    wrong = api.post("/api/v1/auth/login", json={"identifier": "joao", "password": "errada"})
    unknown = api.post("/api/v1/auth/login", json={"identifier": "ninguem", "password": "x"})

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["error"]["message"] == unknown.json()["error"]["message"]


def test_too_many_failures_lock_the_login(api, db):
    make_customer(db, username="joao")
    for _ in range(5):
        api.post("/api/v1/auth/login", json={"identifier": "joao", "password": "errada"})

    # Mesmo com a senha certa, fica bloqueado por alguns minutos.
    response = api.post("/api/v1/auth/login", json={"identifier": "joao", "password": PASSWORD})
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
    # Outra conta (outro identificador) não é afetada.
    make_customer(db, username="maria")
    ok = api.post("/api/v1/auth/login", json={"identifier": "maria", "password": PASSWORD})
    assert ok.status_code == 200


def test_logout_requires_csrf_and_ends_the_session(api, db):
    make_customer(db, username="joao")
    api.login("joao")

    without_token = api.post("/api/v1/auth/logout", headers={"X-CSRF-Token": "falso"})
    assert without_token.status_code == 403
    assert without_token.json()["error"]["code"] == "csrf_failed"

    assert api.post("/api/v1/auth/logout").status_code == 204
    assert api.get("/api/v1/auth/me").status_code == 401
    assert db.scalar(select(AuthSession.id)) is None


def test_session_token_is_stored_only_as_hash(api, db):
    make_customer(db, username="joao")
    api.login("joao")
    token = api.cookies.get("cb_session")
    stored = db.scalar(select(AuthSession.token_hash))
    assert stored != token
    assert len(stored) == 64


def test_password_hash_from_legacy_php_system_is_accepted_and_upgraded(api, db):
    """Hashes `$2y$` do PHP (password_hash) continuam valendo e são regravados no login."""
    php_hash = (
        bcrypt.hashpw(b"123456", bcrypt.gensalt(rounds=4)).decode().replace("$2b$", "$2y$", 1)
    )
    user = make_customer(db, username="legado")
    user.password_hash = php_hash
    db.commit()

    api.login("legado", "123456")

    db.refresh(user)
    assert user.password_hash.startswith("$2b$")


def test_staff_cpf_can_also_have_a_customer_account(make_api, db):
    cpf = random_cpf()
    make_staff(db, Role.COOK, cpf=cpf)
    customer = make_customer(db, username="cozinheiro.cliente")
    customer.cpf = cpf
    db.commit()

    assert make_api().login(cpf).get("/api/v1/auth/me").json()["user"]["role"] == "cook"
    assert (
        make_api().login("cozinheiro.cliente").get("/api/v1/auth/me").json()["user"]["role"]
        == "customer"
    )
