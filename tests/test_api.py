import pytest
from fastapi.testclient import TestClient

from db import get_db
from main import app
from tests.conftest import TestingSessionLocal


# override DB connection
def override_get_db():
    try:
        db = TestingSessionLocal()
        db.begin()
        yield db
    finally:
        db.rollback()
        db.close()


app.dependency_overrides[get_db] = override_get_db
# Create a TestClient instance to make requests to your FastAPI app
client = TestClient(app)


def test_create_user():
    # Send a POST request to create a new user
    response = client.post("/users/", json={"name": "Test user 1", "balance": 200.0})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test user 1"
    assert data["balance"] == '200.00'


def test_get_users():
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1  # We only have one user in the test database


def test_transfer_money():
    client.post("/users/", json={"name": "Test user 2", "balance": 300.0})
    # Send a POST request to transfer money between users
    response = client.post("/transactions/transfer", json={"sender_id": 1, "receiver_id": 2, "amount": 50.0})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["type"] == "transfer"
    assert data["amount"] == '50.00'


def test_get_transactions_history():
    # Send a GET request to retrieve transaction history between two users
    response = client.get("/transactions/history/1/2")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1  # Including the transfer transaction from user with ID 1 to user with ID 2


def test_withdraw_money():
    # Send a POST request to withdraw money from a user
    response = client.post("/transactions/withdraw", json={"sender_id": 1, "amount": 50.0})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Withdrawal request submitted"


def test_get_all_transactions():
    # Send a GET request to retrieve all transactions
    response = client.get("/transactions/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1  # Including the transfer and withdrawal transactions


def test_get_transactions_for_user():
    # Send a GET request to retrieve transactions for a specific user
    response = client.get("/transactions/1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1  # Including the transfer and withdrawal transactions for user with ID 1
