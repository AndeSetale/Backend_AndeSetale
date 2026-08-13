"""
Tests BE-005 — Permissions DRF par rôle.
Vérifie que chaque rôle accède uniquement à ce qu'il a le droit de faire.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from apps.users.models import Utilisateur
from apps.users.permissions import (
    IsAdmin,
    IsAgent,
    IsAgentOrAdmin,
    IsCitoyen,
    IsCitoyenOrAdmin,
    IsOwnerOrAdmin,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def citoyen(db):
    return User.objects.create_user(
        username="citoyen1",
        password="pass1234!",
        role=Utilisateur.Role.CITOYEN,
    )


@pytest.fixture
def agent(db):
    return User.objects.create_user(
        username="agent1",
        password="pass1234!",
        role=Utilisateur.Role.AGENT,
    )


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        username="admin1",
        password="pass1234!",
        role=Utilisateur.Role.ADMIN,
    )


@pytest.fixture
def anonymous_request(factory):
    """Requête sans authentification."""
    request = factory.get("/")
    from django.contrib.auth.models import AnonymousUser
    request.user = AnonymousUser()
    return request


def make_request(factory, user):
    request = factory.get("/")
    request.user = user
    return request


# ---------------------------------------------------------------------------
# Tests IsCitoyen
# ---------------------------------------------------------------------------

class TestIsCitoyen:
    def test_citoyen_autorise(self, factory, citoyen):
        perm = IsCitoyen()
        assert perm.has_permission(make_request(factory, citoyen), None) is True

    def test_agent_refuse(self, factory, agent):
        perm = IsCitoyen()
        assert perm.has_permission(make_request(factory, agent), None) is False

    def test_admin_refuse(self, factory, admin):
        perm = IsCitoyen()
        assert perm.has_permission(make_request(factory, admin), None) is False

    def test_anonyme_refuse(self, anonymous_request):
        perm = IsCitoyen()
        assert perm.has_permission(anonymous_request, None) is False


# ---------------------------------------------------------------------------
# Tests IsAgent
# ---------------------------------------------------------------------------

class TestIsAgent:
    def test_agent_autorise(self, factory, agent):
        perm = IsAgent()
        assert perm.has_permission(make_request(factory, agent), None) is True

    def test_citoyen_refuse(self, factory, citoyen):
        perm = IsAgent()
        assert perm.has_permission(make_request(factory, citoyen), None) is False

    def test_admin_refuse(self, factory, admin):
        perm = IsAgent()
        assert perm.has_permission(make_request(factory, admin), None) is False


# ---------------------------------------------------------------------------
# Tests IsAdmin
# ---------------------------------------------------------------------------

class TestIsAdmin:
    def test_admin_autorise(self, factory, admin):
        perm = IsAdmin()
        assert perm.has_permission(make_request(factory, admin), None) is True

    def test_citoyen_refuse(self, factory, citoyen):
        perm = IsAdmin()
        assert perm.has_permission(make_request(factory, citoyen), None) is False

    def test_agent_refuse(self, factory, agent):
        perm = IsAdmin()
        assert perm.has_permission(make_request(factory, agent), None) is False


# ---------------------------------------------------------------------------
# Tests IsAgentOrAdmin
# ---------------------------------------------------------------------------

class TestIsAgentOrAdmin:
    def test_agent_autorise(self, factory, agent):
        perm = IsAgentOrAdmin()
        assert perm.has_permission(make_request(factory, agent), None) is True

    def test_admin_autorise(self, factory, admin):
        perm = IsAgentOrAdmin()
        assert perm.has_permission(make_request(factory, admin), None) is True

    def test_citoyen_refuse(self, factory, citoyen):
        perm = IsAgentOrAdmin()
        assert perm.has_permission(make_request(factory, citoyen), None) is False


# ---------------------------------------------------------------------------
# Tests IsCitoyenOrAdmin
# ---------------------------------------------------------------------------

class TestIsCitoyenOrAdmin:
    def test_citoyen_autorise(self, factory, citoyen):
        perm = IsCitoyenOrAdmin()
        assert perm.has_permission(make_request(factory, citoyen), None) is True

    def test_admin_autorise(self, factory, admin):
        perm = IsCitoyenOrAdmin()
        assert perm.has_permission(make_request(factory, admin), None) is True

    def test_agent_refuse(self, factory, agent):
        perm = IsCitoyenOrAdmin()
        assert perm.has_permission(make_request(factory, agent), None) is False


# ---------------------------------------------------------------------------
# Tests IsOwnerOrAdmin (niveau objet)
# ---------------------------------------------------------------------------

class FakeIncident:
    """Objet simulant un incident avec signale_par."""
    def __init__(self, owner):
        self.signale_par = owner


class TestIsOwnerOrAdmin:
    def test_proprietaire_autorise(self, factory, citoyen):
        perm = IsOwnerOrAdmin()
        obj = FakeIncident(owner=citoyen)
        assert perm.has_object_permission(make_request(factory, citoyen), None, obj) is True

    def test_admin_autorise_sur_tout(self, factory, admin, citoyen):
        perm = IsOwnerOrAdmin()
        obj = FakeIncident(owner=citoyen)  # appartient au citoyen
        assert perm.has_object_permission(make_request(factory, admin), None, obj) is True

    def test_autre_citoyen_refuse(self, factory, citoyen, agent):
        perm = IsOwnerOrAdmin()
        obj = FakeIncident(owner=agent)    # appartient à l'agent
        assert perm.has_object_permission(make_request(factory, citoyen), None, obj) is False


# ---------------------------------------------------------------------------
# Tests d'intégration via API (critères d'acceptation BE-005)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPermissionsAPI:
    """
    Simule de vrais appels HTTP pour vérifier que les permissions
    sont correctement appliquées sur les endpoints.
    """

    def setup_method(self):
        self.client = APIClient()

    def _get_token(self, username, password):
        resp = self.client.post(
            "/api/auth/login/",
            {"username": username, "password": password},
            format="json",
        )
        return resp.data.get("access")

    def test_endpoint_me_refuse_sans_token(self):
        """Un anonyme ne peut pas accéder à /me/."""
        resp = self.client.get("/api/auth/me/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_citoyen_peut_acceder_me(self, citoyen):
        token = self._get_token("citoyen1", "pass1234!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get("/api/auth/me/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["role"] == "citoyen"

    def test_agent_peut_acceder_me(self, agent):
        token = self._get_token("agent1", "pass1234!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get("/api/auth/me/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["role"] == "agent"

    def test_token_invalide_refuse(self):
        """Un token falsifié retourne 401."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token.faux.invalide")
        resp = self.client.get("/api/auth/me/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
