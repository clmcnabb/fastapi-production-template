def test_create_user_then_login(client) -> None:
    create_response = client.post(
        "/api/v1/users/",
        json={"email": "dev@example.com", "password": "secret123"},
    )
    assert create_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "dev@example.com", "password": "secret123"},
    )

    assert login_response.status_code == 200
    payload = login_response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"
