from __future__ import annotations

from decimal import Decimal


def test_get_balance_returns_current_user_balance(
    client,
    api_user,
    auth_headers,
) -> None:
    response = client.get("/balance", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()

    assert body["user_id"] == str(api_user.id)
    assert Decimal(str(body["balance_credits"])) == Decimal("100.00")


def test_top_up_balance_increases_balance_and_returns_transaction(
    client,
    api_user,
    auth_headers,
) -> None:
    response = client.post(
        "/balance/top-up",
        json={"amount": "25.00"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()

    assert body["user_id"] == str(api_user.id)
    assert Decimal(str(body["balance_credits"])) == Decimal("125.00")
    assert body["transaction"]["transaction_type"] == "credit"
    assert Decimal(str(body["transaction"]["amount"])) == Decimal("25.00")

    balance_response = client.get("/balance", headers=auth_headers)
    assert balance_response.status_code == 200

    balance_body = balance_response.json()
    assert Decimal(str(balance_body["balance_credits"])) == Decimal("125.00")