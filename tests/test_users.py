def test_me_requires_auth(client) -> None:
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
