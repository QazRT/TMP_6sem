from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

uniq = __import__("random").randint(0, 100000)

def test_create_user():
    response = client.post("/users/", json={"name": "John Doe", "email": f"john{uniq}@example.com"})
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"
    assert response.json()["email"] == f"john{uniq}@example.com"

def test_read_users():
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
