import io

import pytest
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.incidents.models import Incident, Preuve
from apps.users.models import Utilisateur


def create_test_image(name="test.jpg", image_format="JPEG"):
    """Crée une vraie image en mémoire pour tester les uploads."""
    image = Image.new("RGB", (100, 100), "white")
    image_io = io.BytesIO()
    image.save(image_io, format=image_format)
    image_io.seek(0)
    image_io.name = name
    return image_io


# ---------------------------------------------------------------------------
# Tests pytest (fixtures conftest) — modèle + API incidents
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestIncidentModel:

    def test_reference_generee_automatiquement(self, user_citoyen):
        incident = Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Déchets dans la rue",
            signale_par=user_citoyen,
        )
        assert incident.reference.startswith("INC-")
        assert len(incident.reference) == 12

    def test_statut_par_defaut_nouveau(self, user_citoyen):
        incident = Incident.objects.create(
            type=Incident.TypeIncident.VOIRIE,
            description="Nid de poule",
            signale_par=user_citoyen,
        )
        assert incident.statut == Incident.StatutIncident.NOUVEAU

    def test_niveau_urgence_par_defaut_routine(self, user_citoyen):
        incident = Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Dépôt sauvage",
            signale_par=user_citoyen,
        )
        assert incident.niveau_urgence == Incident.NiveauUrgence.ROUTINE

    def test_reference_unique(self, user_citoyen):
        incident1 = Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Premier incident",
            signale_par=user_citoyen,
        )
        incident2 = Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Deuxième incident",
            signale_par=user_citoyen,
        )
        assert incident1.reference != incident2.reference


@pytest.mark.django_db
class TestIncidentAPI:

    def setup_method(self):
        self.client = APIClient()

    def test_liste_incidents_sans_authentification(self):
        response = self.client.get("/api/incidents/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_liste_incidents_authentifie(self, user_citoyen, user_agent):
        Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Déchets abandonnés",
            signale_par=user_citoyen,
        )
        Incident.objects.create(
            type=Incident.TypeIncident.VOIRIE,
            description="Route dégradée",
            signale_par=user_citoyen,
        )
        self.client.force_authenticate(user=user_citoyen)
        response = self.client.get("/api/incidents/")
        assert response.status_code == status.HTTP_200_OK
        results = (
            response.data["results"]
            if isinstance(response.data, dict) and "results" in response.data
            else response.data
        )
        assert len(results) == 2

    def test_creation_incident_authentifie(self, user_citoyen):
        self.client.force_authenticate(user=user_citoyen)
        data = {
            "type": "DECHETS",
            "description": "Dépôt sauvage de déchets",
            "niveau_urgence": "ELEVE",
            "quartier": "Yoff",
            "adresse": "Rue principale",
            "latitude": 14.75,
            "longitude": -17.45,
        }
        response = self.client.post("/api/incidents/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["type"] == "DECHETS"
        assert response.data["description"] == "Dépôt sauvage de déchets"
        incident = Incident.objects.get(description="Dépôt sauvage de déchets")
        assert incident.signale_par == user_citoyen

    def test_creation_incident_sans_authentification(self):
        data = {
            "type": "DECHETS",
            "description": "Incident non authentifié",
        }
        response = self.client.post("/api/incidents/", data, format="json")
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_401_UNAUTHORIZED,
        ]

    def test_creation_incident_description_obligatoire(self, user_citoyen):
        self.client.force_authenticate(user=user_citoyen)
        data = {"type": "DECHETS"}
        response = self.client.post("/api/incidents/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_creation_incident_type_invalide(self, user_citoyen):
        self.client.force_authenticate(user=user_citoyen)
        data = {"type": "TYPE_INEXISTANT", "description": "Incident test"}
        response = self.client.post("/api/incidents/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPreuveUploadAPI:

    def setup_method(self):
        self.client = APIClient()

    def test_upload_preuve_sans_authentification(self, user_citoyen):
        incident = Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Incident test",
            signale_par=user_citoyen,
        )
        image = create_test_image()
        response = self.client.post(
            "/api/incidents/preuves/upload/",
            {"incident_id": incident.id, "type": "PHOTO_AVANT", "image": image},
            format="multipart",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_preuve_authentifie(self, user_citoyen):
        incident = Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Incident avec photo",
            signale_par=user_citoyen,
        )
        self.client.force_authenticate(user=user_citoyen)
        image = create_test_image()
        response = self.client.post(
            "/api/incidents/preuves/upload/",
            {"incident_id": incident.id, "type": "PHOTO_AVANT", "image": image},
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Preuve.objects.filter(incident=incident).count() == 1
        preuve = Preuve.objects.get(incident=incident)
        assert preuve.type == "PHOTO_AVANT"
        assert preuve.image

    def test_upload_preuve_incident_inexistant(self, user_citoyen):
        self.client.force_authenticate(user=user_citoyen)
        image = create_test_image()
        response = self.client.post(
            "/api/incidents/preuves/upload/",
            {"incident_id": 999999, "type": "PHOTO_AVANT", "image": image},
            format="multipart",
        )
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_upload_preuve_sans_image(self, user_citoyen):
        incident = Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Incident sans photo",
            signale_par=user_citoyen,
        )
        self.client.force_authenticate(user=user_citoyen)
        response = self.client.post(
            "/api/incidents/preuves/upload/",
            {"incident_id": incident.id, "type": "PHOTO_AVANT"},
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Tests APITestCase (style BE-010) — CRUD incidents via /api/incidents/
# ---------------------------------------------------------------------------

class SignalementAPITests(APITestCase):
    def setUp(self):
        self.citoyen1 = Utilisateur.objects.create_user(
            username="citoyen1",
            email="citoyen1@example.com",
            password="Password123!",
            role=Utilisateur.Role.CITOYEN,
        )
        self.citoyen2 = Utilisateur.objects.create_user(
            username="citoyen2",
            email="citoyen2@example.com",
            password="Password123!",
            role=Utilisateur.Role.CITOYEN,
        )
        self.admin = Utilisateur.objects.create_user(
            username="admin_user",
            email="admin@example.com",
            password="Password123!",
            role=Utilisateur.Role.ADMIN,
        )

        self.incident1 = Incident.objects.create(
            reference="SIG-20260813-A001",
            type=Incident.TypeIncident.DECHETS,
            description="Dépôt sauvage d'ordures",
            statut=Incident.StatutIncident.NOUVEAU,
            niveau_urgence=Incident.NiveauUrgence.ELEVE,
            quartier="Plateau",
            signale_par=self.citoyen1,
        )
        self.incident2 = Incident.objects.create(
            reference="SIG-20260813-A002",
            type=Incident.TypeIncident.VOIRIE,
            description="Nid de poule géant",
            statut=Incident.StatutIncident.EN_COURS,
            niveau_urgence=Incident.NiveauUrgence.MODERE,
            quartier="Médina",
            signale_par=self.citoyen2,
        )

        self.list_url = "/api/incidents/"
        self.detail_url = f"/api/incidents/{self.incident1.id}/"

    def test_creation_signalement_citoyen(self):
        """Création d'un signalement par un citoyen connecté."""
        self.client.force_authenticate(user=self.citoyen1)
        payload = {
            "type": Incident.TypeIncident.CANAUX,
            "description": "Canal bouché après les pluies",
            "quartier": "Fann",
            "adresse": "Avenue Cheikh Anta Diop",
            "niveau_urgence": Incident.NiveauUrgence.CRITIQUE,
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["type"], Incident.TypeIncident.CANAUX)
        self.assertEqual(response.data["signale_par"], self.citoyen1.id)

    def test_liste_signalements_filtree_pour_citoyen(self):
        """Un citoyen ne voit que ses propres signalements."""
        self.client.force_authenticate(user=self.citoyen1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data["results"]
            if "results" in response.data
            else response.data
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.incident1.id)

    def test_liste_signalements_admin_voit_tout(self):
        """Un admin voit tous les signalements."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data["results"]
            if "results" in response.data
            else response.data
        )
        self.assertEqual(len(results), 2)

    def test_filtrage_par_statut(self):
        """Filtre ?statut=EN_COURS."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.list_url}?statut=EN_COURS")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data["results"]
            if "results" in response.data
            else response.data
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.incident2.id)

    def test_detail_signalement(self):
        """Détail d'un signalement avec données imbriquées."""
        self.client.force_authenticate(user=self.citoyen1)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["reference"], "SIG-20260813-A001")
        self.assertEqual(
            response.data["signale_par_details"]["username"], "citoyen1"
        )
