from __future__ import annotations

from decimal import Decimal


def test_predict_success_creates_result_and_debits_balance(
    client,
    api_user,
    api_model,
    auth_headers,
) -> None:
    files = [
        ("documents", ("sample.pdf", b"%PDF-1.4 test content", "application/pdf")),
    ]
    data = {
        "model_name": api_model.name,
        "target_schema": "passport_fields",
    }

    response = client.post(
        "/predict",
        data=data,
        files=files,
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()

    assert body["task_id"] is not None
    assert body["model_id"] == str(api_model.id)
    assert body["model_name"] == api_model.name
    assert body["status"] == "completed"
    assert Decimal(str(body["spent_credits"])) == Decimal("10.00")
    assert Decimal(str(body["remaining_balance_credits"])) == Decimal("90.00")
    assert body["result_id"] is not None
    assert isinstance(body["extracted_data"], dict)
    assert body["validation_issues"] == []


def test_predict_with_insufficient_balance_returns_409(
    client,
    low_balance_user,
    api_model,
    low_balance_auth_headers,
) -> None:
    files = [
        ("documents", ("sample.pdf", b"%PDF-1.4 test content", "application/pdf")),
    ]
    data = {
        "model_name": api_model.name,
        "target_schema": "passport_fields",
    }

    response = client.post(
        "/predict",
        data=data,
        files=files,
        headers=low_balance_auth_headers,
    )

    assert response.status_code == 409
    body = response.json()

    assert body["error"]["code"] == "insufficient_balance"


def test_predict_with_missing_model_returns_404(
    client,
    api_user,
    auth_headers,
) -> None:
    files = [
        ("documents", ("sample.pdf", b"%PDF-1.4 test content", "application/pdf")),
    ]
    data = {
        "model_name": "missing-model",
        "target_schema": "passport_fields",
    }

    response = client.post(
        "/predict",
        data=data,
        files=files,
        headers=auth_headers,
    )

    assert response.status_code == 404
    body = response.json()

    assert body["error"]["code"] == "not_found"