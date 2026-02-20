def test_predict_returns_value(client) -> None:
    response = client.post("/api/v1/predict/", json={"features": [1, 2, 3, 4]})

    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] == 2.5
