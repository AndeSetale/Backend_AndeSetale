from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import Utilisateur

from .models import Incident


class SignalementAPITests(APITestCase):
    def setUp(self):
        # Création des utilisateurs de test
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

        # Signalement de test
        self.incident1 = Incident.objects.create(
            reference="SIG-20260813-0001",
            type=Incident.TypeIncident.DECHETS,
            description="Dépôt sauvage d'ordures",
            statut=Incident.StatutIncident.NOUVEAU,
            niveau_urgence=Incident.NiveauUrgence.ELEVE,
            quartier="Plateau",
            signale_par=self.citoyen1,
        )
        self.incident2 = Incident.objects.create(
            reference="SIG-20260813-0002",
            type=Incident.TypeIncident.VOIRIE,
            description="Nid de poule géant",
            statut=Incident.StatutIncident.EN_COURS,
            niveau_urgence=Incident.NiveauUrgence.MODERE,
            quartier="Médina",
            signale_par=self.citoyen2,
        )

        self.list_url = "/api/signalements/"
        self.detail_url = f"/api/signalements/{self.incident1.id}/"

    def test_creation_signalement_citoyen(self):
        """Tester la création d'un signalement par un citoyen connecté."""
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
        self.assertTrue(response.data["reference"].startswith("SIG-"))

    def test_liste_signalements_filtree_pour_citoyen(self):
        """Un citoyen ne voit que ses propres signalements par défaut."""
        self.client.force_authenticate(user=self.citoyen1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # pagination active -> "results"
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.incident1.id)

    def test_liste_signalements_admin_voit_tout(self):
        """Un admin voit tous les signalements."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filtrage_par_statut(self):
        """Tester le filtre par statut ?statut=EN_COURS."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.list_url}?statut=EN_COURS")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.incident2.id)

    def test_detail_signalement(self):
        """Tester l'obtention du détail d'un signalement."""
        self.client.force_authenticate(user=self.citoyen1)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["reference"], "SIG-20260813-0001")
        self.assertEqual(response.data["signale_par_details"]["username"], "citoyen1")

