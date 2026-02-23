def _create_user_and_token(client, email: str = "stream@example.com") -> str:
    create_response = client.post(
        "/api/v1/users/",
        json={"email": email, "password": "secret123"},
    )
    assert create_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "secret123"},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_sse_connects_with_auth(client) -> None:
    token = _create_user_and_token(client)
    response = client.get(
        "/api/v1/stream/sse?max_events=1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "event: connected" in response.text


def test_websocket_receives_broadcast_message(client) -> None:
    token = _create_user_and_token(client, email="stream-ws@example.com")

    with client.websocket_connect(f"/api/v1/stream/ws?token={token}") as websocket:
        connected_payload = websocket.receive_json()
        assert connected_payload["type"] == "connected"

        websocket.send_text("hello websocket")
        message_payload = websocket.receive_json()

    assert message_payload["type"] == "message"
    assert message_payload["message"] == "hello websocket"
