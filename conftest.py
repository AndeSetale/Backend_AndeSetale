import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user_citoyen(db):
    User = get_user_model()

    return User.objects.create_user(
        username="citoyen_test",
        password="Test1234!",
        role="citoyen",
    )


@pytest.fixture
def user_agent(db):
    User = get_user_model()

    return User.objects.create_user(
        username="agent_test",
        password="Test1234!",
        role="agent",
    )


@pytest.fixture
def user_admin(db):
    User = get_user_model()

    return User.objects.create_user(
        username="admin_test",
        password="Test1234!",
        role="admin",
    )