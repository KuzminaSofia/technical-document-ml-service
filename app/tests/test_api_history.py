from __future__ import annotations


def test_transactions_history_returns_created_top_up_transaction(
    client,
    api_user,
    auth_headers,
) -> None:
    top_up_response = client.post(
        "/balance/top-up",
        json={"amount": "15.00"},
        headers=auth_headers,
    )
    assert top_up_response.status_code == 200

    history_response = client.get("/history/transactions", headers=auth_headers)

    assert history_response.status_code == 200
    body = history_response.json()

    assert len(body["items"]) == 1
    assert body["items"][0]["transaction_type"] == "credit"
    assert str(body["items"][0]["user_id"]) == str(api_user.id)


def test_predictions_history_contains_successful_prediction(
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

    predict_response = client.post(
        "/predict",
        data=data,
        files=files,
        headers=auth_headers,
    )
    assert predict_response.status_code == 200

    history_response = client.get("/history/predictions", headers=auth_headers)

    assert history_response.status_code == 200
    body = history_response.json()

    assert len(body["items"]) == 1
    assert body["items"][0]["status"] == "completed"
    assert str(body["items"][0]["user_id"]) == str(api_user.id)
    assert str(body["items"][0]["model_id"]) == str(api_model.id)
    assert body["items"][0]["result_id"] is not None