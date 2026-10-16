from app.modules.users.models import Role, User
from tests.helpers import PASSWORD, fresh, make_customer, make_staff, random_cpf


def new_staff(role: str = "cook", cpf: str | None = None) -> dict:
    return {
        "role": role,
        "cpf": cpf or random_cpf(),
        "name": "Carlos Souza",
        "birth_date": "1990-05-10",
        "email": "carlos@caliburger.com",
        "sex": "male",
        "password": "senha-forte",
        "password_confirmation": "senha-forte",
    }


def test_manager_registers_cook_who_can_log_in(make_api, db):
    manager = make_staff(db, Role.MANAGER)
    api = make_api().login(manager.cpf)
    data = new_staff()

    response = api.post("/api/v1/staff", json=data)

    assert response.status_code == 201
    assert response.json()["role"] == "cook"
    cook = make_api()
    assert (
        cook.post(
            "/api/v1/auth/login", json={"identifier": data["cpf"], "password": "senha-forte"}
        ).status_code
        == 200
    )
    names = [s["name"] for s in api.get("/api/v1/staff").json()]
    assert "Carlos Souza" in names


def test_staff_cpf_must_be_unique_among_staff(api, db):
    manager = make_staff(db, Role.MANAGER)
    api.login(manager.cpf)
    response = api.post("/api/v1/staff", json=new_staff(cpf=manager.cpf))
    assert response.status_code == 422
    assert "cpf" in response.json()["error"]["fields"]


def test_staff_validation(api, db):
    manager = make_staff(db, Role.MANAGER)
    api.login(manager.cpf)
    data = {**new_staff(), "role": "customer", "sex": "x", "password_confirmation": "outra"}
    fields = api.post("/api/v1/staff", json=data).json()["error"]["fields"]
    assert {"role", "sex", "password_confirmation"} <= set(fields)


def test_only_managers_manage_the_team(make_api, db):
    make_customer(db, username="joao")
    cook = make_staff(db, Role.COOK)
    for client in (make_api().login("joao"), make_api().login(cook.cpf)):
        assert client.get("/api/v1/staff").status_code == 403
        assert client.post("/api/v1/staff", json=new_staff()).status_code == 403
        assert client.delete(f"/api/v1/staff/{cook.id}").status_code == 403
    assert make_api().get("/api/v1/staff").status_code == 401


def test_cannot_delete_the_last_manager(api, db):
    manager = make_staff(db, Role.MANAGER)
    api.login(manager.cpf)
    response = api.delete(f"/api/v1/staff/{manager.id}")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "last_manager"


def test_manager_deletes_cook_and_self(api, db):
    manager = make_staff(db, Role.MANAGER)
    make_staff(db, Role.MANAGER, name="Outra Dona")
    cook = make_staff(db, Role.COOK)
    api.login(manager.cpf)

    assert api.delete(f"/api/v1/staff/{cook.id}").status_code == 204
    cook_id = cook.id
    fresh(db)
    assert db.get(User, cook_id) is None

    response = api.delete(f"/api/v1/staff/{manager.id}")
    assert response.status_code == 204
    assert api.get("/api/v1/auth/me").status_code == 401


def test_customers_are_not_staff(api, db):
    manager = make_staff(db, Role.MANAGER)
    customer = make_customer(db)
    api.login(manager.cpf)
    assert api.delete(f"/api/v1/staff/{customer.id}").status_code == 404
    assert db.get(User, customer.id) is not None
    assert PASSWORD
