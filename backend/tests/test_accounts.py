from sqlalchemy import select

from app.modules.orders.models import Order
from app.modules.users.models import Role, User
from tests.helpers import PASSWORD, fresh, make_customer, make_staff

PROFILE = {"name": "João da Silva", "email": "joao.silva@exemplo.com", "birth_date": "1990-02-03"}


def test_customer_edits_own_profile(api, db):
    user = make_customer(db, username="joao")
    api.login("joao")

    response = api.put(
        "/api/v1/me/profile",
        json={**PROFILE, "username": "joao.silva", "cpf": "529.982.247-25"},
    )

    assert response.status_code == 200
    db.refresh(user)
    assert (user.username, user.name, user.cpf) == ("joao.silva", "João da Silva", "52998224725")


def test_customer_cannot_take_another_username(api, db):
    make_customer(db, username="joao")
    make_customer(db, username="maria")
    api.login("joao")

    response = api.put(
        "/api/v1/me/profile", json={**PROFILE, "username": "maria", "cpf": "529.982.247-25"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["fields"]["username"] == "Este usuário já está em uso."


def test_staff_profile_requires_sex_and_keeps_cpf(api, db):
    staff = make_staff(db, Role.COOK)
    original_cpf = staff.cpf
    api.login(original_cpf)

    missing = api.put("/api/v1/me/profile", json=PROFILE)
    assert missing.status_code == 422
    assert "sex" in missing.json()["error"]["fields"]

    ok = api.put("/api/v1/me/profile", json={**PROFILE, "sex": "male", "cpf": "529.982.247-25"})
    assert ok.status_code == 200
    db.refresh(staff)
    assert staff.cpf == original_cpf  # CPF do funcionário não é editável
    assert staff.sex == "male"


def test_address_update_is_for_customers_only(make_api, db):
    make_customer(db, username="joao")
    staff = make_staff(db)
    address = {"state": "SP", "city": "Santos", "district": "Gonzaga", "street": "Rua B, 2"}

    customer = make_api().login("joao")
    assert customer.put("/api/v1/me/address", json=address).json()["city"] == "Santos"
    assert customer.get("/api/v1/me/profile").json()["address"]["state"] == "SP"

    assert make_api().login(staff.cpf).put("/api/v1/me/address", json=address).status_code == 403


def test_password_change_requires_current_password_and_revokes_other_sessions(make_api, db):
    make_customer(db, username="joao")
    laptop = make_api().login("joao")
    phone = make_api().login("joao")

    wrong = laptop.post(
        "/api/v1/me/password",
        json={
            "current_password": "errada",
            "new_password": "nova-senha",
            "new_password_confirmation": "nova-senha",
        },
    )
    assert wrong.status_code == 422
    assert "current_password" in wrong.json()["error"]["fields"]

    ok = laptop.post(
        "/api/v1/me/password",
        json={
            "current_password": PASSWORD,
            "new_password": "nova-senha",
            "new_password_confirmation": "nova-senha",
        },
    )
    assert ok.status_code == 204
    assert laptop.get("/api/v1/auth/me").status_code == 200  # sessão atual continua
    assert phone.get("/api/v1/auth/me").status_code == 401  # as outras são encerradas
    make_api().login("joao", "nova-senha")


def test_customer_deletes_account_and_orders_stay_in_history(api, db, menu):
    user = make_customer(db, username="joao")
    api.login("joao")
    order_id = api.post(
        "/api/v1/orders", json={"items": [{"menu_item_id": menu.water.id, "quantity": 1}]}
    ).json()["id"]

    wrong = api.request("DELETE", "/api/v1/me", json={"password": "errada"})
    assert wrong.status_code == 422

    assert api.request("DELETE", "/api/v1/me", json={"password": PASSWORD}).status_code == 204
    user_id = user.id
    fresh(db)
    assert db.get(User, user_id) is None
    order = db.get(Order, order_id)
    assert order.customer_id is None
    assert order.customer_name == "João Silva"
    assert api.get("/api/v1/auth/me").status_code == 401


def test_cook_cannot_delete_own_account(api, db):
    cook = make_staff(db, Role.COOK)
    api.login(cook.cpf)
    response = api.request("DELETE", "/api/v1/me", json={"password": PASSWORD})
    assert response.status_code == 403


def test_last_manager_cannot_delete_own_account(api, db):
    manager = make_staff(db, Role.MANAGER)
    api.login(manager.cpf)

    response = api.request("DELETE", "/api/v1/me", json={"password": PASSWORD})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "last_manager"

    make_staff(db, Role.MANAGER, name="Outro Dono")
    assert api.request("DELETE", "/api/v1/me", json={"password": PASSWORD}).status_code == 204
    assert db.scalar(select(User).where(User.id == manager.id)) is None
