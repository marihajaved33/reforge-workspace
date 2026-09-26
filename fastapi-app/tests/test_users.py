def test_users_endpoint(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
