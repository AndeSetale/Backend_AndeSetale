import io

import pytest
from PIL import Image
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.incidents.models import Incident, Preuve


def create_test_image(name="test.jpg", image_format="JPEG"):
    """Crée une vraie image en mémoire pour tester les uploads."""
    image = Image.new("RGB", (100, 100), "white")
    image_io = io.BytesIO()
    image.save(image_io, format=image_format)
    image_io.seek(0)
    image_io.name = name
    return image_io


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

    def test_liste_incidents_authentifie(
        self, user_citoyen, user_agent
    ):
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
        assert len(response.data) == 2

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

        response = self.client.post(
            "/api/incidents/",
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["type"] == "DECHETS"
        assert response.data["description"] == "Dépôt sauvage de déchets"

        incident = Incident.objects.get(
            description="Dépôt sauvage de déchets"
        )

        assert incident.signale_par == user_citoyen

    def test_creation_incident_sans_authentification(self):
        data = {
            "type": "DECHETS",
            "description": "Incident non authentifié",
        }

        response = self.client.post(
            "/api/incidents/",
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_creation_incident_description_obligatoire(self, user_citoyen):
        self.client.force_authenticate(user=user_citoyen)

        data = {
            "type": "DECHETS",
        }

        response = self.client.post(
            "/api/incidents/",
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_creation_incident_type_invalide(self, user_citoyen):
        self.client.force_authenticate(user=user_citoyen)

        data = {
            "type": "TYPE_INEXISTANT",
            "description": "Incident test",
        }

        response = self.client.post(
            "/api/incidents/",
            data,
            format="json",
        )

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
            {
                "incident_id": incident.id,
                "type": "PHOTO_AVANT",
                "image": image,
            },
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
            {
                "incident_id": incident.id,
                "type": "PHOTO_AVANT",
                "image": image,
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_201_CREATED

        assert Preuve.objects.filter(
            incident=incident
        ).count() == 1

        preuve = Preuve.objects.get(incident=incident)

        assert preuve.type == "PHOTO_AVANT"
        assert preuve.image

    def test_upload_preuve_incident_inexistant(self, user_citoyen):
        self.client.force_authenticate(user=user_citoyen)

        image = create_test_image()

        response = self.client.post(
            "/api/incidents/preuves/upload/",
            {
                "incident_id": 999999,
                "type": "PHOTO_AVANT",
                "image": image,
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_upload_preuve_sans_image(self, user_citoyen):
        incident = Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Incident sans photo",
            signale_par=user_citoyen,
        )

        self.client.force_authenticate(user=user_citoyen)

        response = self.client.post(
            "/api/incidents/preuves/upload/",
            {
                "incident_id": incident.id,
                "type": "PHOTO_AVANT",
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST