from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_user():
    response = client.post("/users/", json={"name": "John Doe", "email": "john@example.com"})
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"
    assert response.json()["email"] == "john@example.com"

def test_read_users():
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
