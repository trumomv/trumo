from decimal import Decimal

import pytest
from services.user_service import UserService


@pytest.mark.usefixtures("create_user")
def test_create_user(create_user):
    user = create_user("John Doe", 100.0)
    assert user.name == "John Doe"
    assert user.balance == Decimal('100.0')


@pytest.mark.usefixtures("session")
@pytest.mark.usefixtures("create_user")
def test_fetch_user(session, create_user):
    user = create_user("Alice", 200.0)

    fetched_user = UserService.fetch(session, user.id)

    assert fetched_user.id == user.id
    assert fetched_user.name == user.name
    assert fetched_user.balance == user.balance


@pytest.mark.usefixtures("session")
def test_get_users(session):
    users_data = [
        {"name": "John Doe", "balance": 100.0},
        {"name": "Alice", "balance": 200.0}
    ]

    users = UserService.get_users(session)

    assert len(users) == len(users_data)
    assert all(user.name in [user_data["name"] for user_data in users_data] for user in users)
    assert all(user.balance in [user_data["balance"] for user_data in users_data] for user in users)
