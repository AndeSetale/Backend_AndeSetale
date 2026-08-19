import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.incidents.models import Incident
from apps.users.models import Agent


@pytest.mark.django_db
class TestDashboardStatsAPI:

    def setup_method(self):
        self.client = APIClient()

    # ==========================================================
    # AUTHENTIFICATION
    # ==========================================================

    def test_dashboard_refuse_sans_authentification(self):
        response = self.client.get("/api/dashboard/stats/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_dashboard_accessible_utilisateur_authentifie(self, user_citoyen):
        self.client.force_authenticate(user=user_citoyen)

        response = self.client.get("/api/dashboard/stats/")

        assert response.status_code == status.HTTP_200_OK

    # ==========================================================
    # DASHBOARD VIDE
    # ==========================================================

    def test_dashboard_sans_donnees(self, user_citoyen):
        self.client.force_authenticate(user=user_citoyen)

        response = self.client.get("/api/dashboard/stats/")

        assert response.status_code == status.HTTP_200_OK

        signalements = response.data["signalements"]

        assert signalements["total"] == 0
        assert signalements["en_cours"] == 0
        assert signalements["resolus"] == 0
        assert signalements["urgents"] == 0

        assert response.data["incidents_par_statut"] == []
        assert response.data["agents_disponibles"] == 0

    # ==========================================================
    # TOTAL INCIDENTS
    # ==========================================================

    def test_total_incidents(self, user_citoyen):
        Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Déchets dans la rue",
            signale_par=user_citoyen,
        )

        Incident.objects.create(
            type=Incident.TypeIncident.VOIRIE,
            description="Nid de poule",
            signale_par=user_citoyen,
        )

        self.client.force_authenticate(user=user_citoyen)

        response = self.client.get("/api/dashboard/stats/")

        assert response.data["signalements"]["total"] == 2

    # ==========================================================
    # INCIDENTS EN COURS
    # ==========================================================

    def test_compte_incidents_en_cours(self, user_citoyen):
        Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Incident en cours",
            statut=Incident.StatutIncident.EN_COURS,
            signale_par=user_citoyen,
        )

        Incident.objects.create(
            type=Incident.TypeIncident.VOIRIE,
            description="Incident nouveau",
            statut=Incident.StatutIncident.NOUVEAU,
            signale_par=user_citoyen,
        )

        self.client.force_authenticate(user=user_citoyen)

        response = self.client.get("/api/dashboard/stats/")

        assert response.data["signalements"]["en_cours"] == 1

    # ==========================================================
    # INCIDENTS RÉSOLUS
    # ==========================================================

    def test_compte_incidents_resolus(self, user_citoyen):
        Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Incident résolu",
            statut=Incident.StatutIncident.RESOLU,
            signale_par=user_citoyen,
        )

        Incident.objects.create(
            type=Incident.TypeIncident.VOIRIE,
            description="Incident nouveau",
            statut=Incident.StatutIncident.NOUVEAU,
            signale_par=user_citoyen,
        )

        self.client.force_authenticate(user=user_citoyen)

        response = self.client.get("/api/dashboard/stats/")

        assert response.data["signalements"]["resolus"] == 1

    # ==========================================================
    # INCIDENTS URGENTS
    # ==========================================================

    def test_compte_incidents_urgents(self, user_citoyen):
        Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Urgence critique",
            niveau_urgence=Incident.NiveauUrgence.CRITIQUE,
            signale_par=user_citoyen,
        )

        Incident.objects.create(
            type=Incident.TypeIncident.VOIRIE,
            description="Urgence élevée",
            niveau_urgence=Incident.NiveauUrgence.ELEVE,
            signale_par=user_citoyen,
        )

        Incident.objects.create(
            type=Incident.TypeIncident.ARBRE,
            description="Incident modéré",
            niveau_urgence=Incident.NiveauUrgence.MODERE,
            signale_par=user_citoyen,
        )

        Incident.objects.create(
            type=Incident.TypeIncident.CANAUX,
            description="Incident routine",
            niveau_urgence=Incident.NiveauUrgence.ROUTINE,
            signale_par=user_citoyen,
        )

        self.client.force_authenticate(user=user_citoyen)

        response = self.client.get("/api/dashboard/stats/")

        assert response.data["signalements"]["urgents"] == 2

    # ==========================================================
    # RÉPARTITION PAR STATUT
    # ==========================================================

    def test_repartition_incidents_par_statut(self, user_citoyen):
        Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Nouveau 1",
            statut=Incident.StatutIncident.NOUVEAU,
            signale_par=user_citoyen,
        )

        Incident.objects.create(
            type=Incident.TypeIncident.DECHETS,
            description="Nouveau 2",
            statut=Incident.StatutIncident.NOUVEAU,
            signale_par=user_citoyen,
        )

        Incident.objects.create(
            type=Incident.TypeIncident.VOIRIE,
            description="En cours",
            statut=Incident.StatutIncident.EN_COURS,
            signale_par=user_citoyen,
        )

        Incident.objects.create(
            type=Incident.TypeIncident.ARBRE,
            description="Résolu",
            statut=Incident.StatutIncident.RESOLU,
            signale_par=user_citoyen,
        )

        self.client.force_authenticate(user=user_citoyen)

        response = self.client.get("/api/dashboard/stats/")

        repartition = {
            item["statut"]: item["count"]
            for item in response.data["incidents_par_statut"]
        }

        assert repartition["NOUVEAU"] == 2
        assert repartition["EN_COURS"] == 1
        assert repartition["RESOLU"] == 1

    # ==========================================================
    # AGENTS DISPONIBLES
    # ==========================================================

    def test_compte_agents_disponibles(
        self,
        user_citoyen,
        user_agent,
    ):
        Agent.objects.create(
            utilisateur=user_agent,
            matricule="AG-001",
            disponible=True,
        )

        self.client.force_authenticate(user=user_citoyen)

        response = self.client.get("/api/dashboard/stats/")

        assert response.data["agents_disponibles"] == 1

    # ==========================================================
    # AGENTS INDISPONIBLES
    # ==========================================================

    def test_agents_indisponibles_non_comptes(
        self,
        user_citoyen,
        user_agent,
    ):
        Agent.objects.create(
            utilisateur=user_agent,
            matricule="AG-001",
            disponible=False,
        )

        self.client.force_authenticate(user=user_citoyen)

        response = self.client.get("/api/dashboard/stats/")

        assert response.data["agents_disponibles"] == 0

    # ==========================================================
    # STRUCTURE DE LA RÉPONSE
    # ==========================================================

    def test_structure_reponse_dashboard(self, user_citoyen):
        self.client.force_authenticate(user=user_citoyen)

        response = self.client.get("/api/dashboard/stats/")

        assert response.status_code == status.HTTP_200_OK

        assert "signalements" in response.data
        assert "incidents_par_statut" in response.data
        assert "agents_disponibles" in response.data

        assert "total" in response.data["signalements"]
        assert "en_cours" in response.data["signalements"]
        assert "resolus" in response.data["signalements"]
        assert "urgents" in response.data["signalements"]