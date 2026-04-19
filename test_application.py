import pytest
import os
import json

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from application import app, db, Blacklist

#comentario de prueba
@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_health(client):
    """Prueba el endpoint de salud de la API"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

def test_login_success(client):
    """Prueba el inicio de sesión con credenciales válidas"""
    response = client.post("/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.get_json()

def test_login_failure(client):
    """Prueba el inicio de sesión con credenciales inválidas"""
    response = client.post("/login", json={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401

def test_add_blacklist_success(client):
    """Prueba agregar un correo a la lista negra exitosamente"""
    # Login to get token
    login_resp = client.post("/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.get_json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "email": "test@example.com",
        "app_uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "blocked_reason": "Testing purpose"
    }
    response = client.post("/blacklists", json=data, headers=headers)
    assert response.status_code == 201
    assert response.get_json()["email"] == "test@example.com"

def test_add_blacklist_duplicate_error(client):
    """Prueba que no se permita agregar un correo duplicado (Error 409)"""
    login_resp = client.post("/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "email": "duplicate@example.com",
        "app_uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "blocked_reason": "Reason 1"
    }
    # First insertion
    client.post("/blacklists", json=data, headers=headers)
    
    # Second insertion of same email
    response = client.post("/blacklists", json=data, headers=headers)
    assert response.status_code == 409
    assert "El email ya se encuentra en la lista negra" in response.get_json()["mensaje"]

def test_add_blacklist_invalid_data(client):
    """Prueba la validación de esquema con datos inválidos"""
    login_resp = client.post("/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "email": "not-an-email",
        "app_uuid": "not-a-uuid"
    }
    response = client.post("/blacklists", json=data, headers=headers)
    assert response.status_code == 400
    assert "Error de validación" in response.get_json()["mensaje"]

def test_check_blacklist_exists(client):
    """Prueba verificar un correo que SÍ está en la lista negra"""
    login_resp = client.post("/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    email = "blacklisted@example.com"
    client.post("/blacklists", json={
        "email": email,
        "app_uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "blocked_reason": "Reported for spam"
    }, headers=headers)
    
    response = client.get(f"/blacklists/{email}", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["is_blacklisted"] is True
    assert response.get_json()["blocked_reason"] == "Reported for spam"

def test_check_blacklist_not_exists(client):
    """Prueba verificar un correo que NO está en la lista negra"""
    login_resp = client.post("/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/blacklists/clean-email@example.com", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["is_blacklisted"] is False

def test_unauthorized_access(client):
    """Prueba que los endpoints protegidos devuelvan 401 sin token"""
    response_post = client.post("/blacklists", json={})
    response_get = client.get("/blacklists/any@example.com")
    
    assert response_post.status_code == 401
    assert response_get.status_code == 401
