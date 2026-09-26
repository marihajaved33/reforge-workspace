def test_register(client):
    response = client.post("/auth/register", json={
        "username": "janedoe",
        "email": "jane@example.com"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["username"] == "janedoe"


def test_duplicate_email(client):
    payload = {"username": "a", "email": "same@example.com"}
    assert client.post("/auth/register", json=payload).status_code == 201
    # second POST with same email but different username must return 400
    payload2 = {"username": "b", "email": "same@example.com"}
    assert client.post("/auth/register", json=payload2).status_code == 400
