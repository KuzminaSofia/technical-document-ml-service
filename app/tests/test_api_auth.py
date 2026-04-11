from __future__ import annotations


def test_register_user_success(client) -> None:
    payload = {
        "email": "new.user@example.com",
        "password": "strongpass123",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()

    assert body["message"] == "Пользователь успешно зарегистрирован."
    assert body["user"]["email"] == "new.user@example.com"
    assert body["user"]["role"] == "user"
    assert str(body["user"]["balance_credits"]) in {"0", "0.00"}


def test_register_duplicate_user_returns_409(client) -> None:
    payload = {
        "email": "duplicate.user@example.com",
        "password": "strongpass123",
    }

    first_response = client.post("/auth/register", json=payload)
    second_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    body = second_response.json()
    assert body["error"]["code"] == "user_already_exists"


def test_login_success(client, api_user) -> None:
    payload = {
        "email": "api.user@example.com",
        "password": "test-password",
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert body["message"] == "Аутентификация прошла успешно."
    assert body["user"]["email"] == "api.user@example.com"


def test_login_with_invalid_password_returns_401(client, api_user) -> None:
    payload = {
        "email": "api.user@example.com",
        "password": "wrong-password",
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    body = response.json()

    assert body["error"]["code"] == "authentication_failed"