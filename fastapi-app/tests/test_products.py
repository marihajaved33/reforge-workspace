def test_products_empty(client):
    response = client.get("/products")
    assert response.status_code == 200
    assert response.json() == []


def test_add_product(client):
    response = client.post("/products", json={"name": "Keyboard", "price": 25.0})
    assert response.status_code == 201
    assert response.json()["name"] == "Keyboard"
