"""
Tests du workflow complet : signalement → assignation → intervention → rapport → résolution.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO
from rest_framework import status
from rest_framework.test import APIClient

from apps.incidents.models import Incident
from apps.interventions.models import Intervention
from apps.notifications.models import Notification
from apps.users.models import Agent


def image_test(nom="photo.jpg"):
    contenu = BytesIO()
    Image.new("RGB", (20, 20), (0, 120, 60)).save(contenu, "JPEG")
    return SimpleUploadedFile(nom, contenu.getvalue(), content_type="image/jpeg")


@pytest.fixture
def agent_profil(user_agent):
    return Agent.objects.create(utilisateur=user_agent, matricule="AG-001")


@pytest.fixture
def incident(user_citoyen):
    return Incident.objects.create(
        type=Incident.TypeIncident.DECHETS,
        description="Dépôt sauvage",
        niveau_urgence=Incident.NiveauUrgence.ELEVE,
        signale_par=user_citoyen,
    )


@pytest.mark.django_db
class TestWorkflowIntervention:

    def setup_method(self):
        self.client = APIClient()

    def assigner(self, admin, incident, agent_user):
        self.client.force_authenticate(user=admin)
        return self.client.patch(
            f"/api/incidents/{incident.id}/", {"assigne_a": agent_user.id}, format="json"
        )

    def test_assignation_cree_intervention_et_notifie(self, user_admin, user_agent, agent_profil, incident):
        response = self.assigner(user_admin, incident, user_agent)

        assert response.status_code == status.HTTP_200_OK
        incident.refresh_from_db()
        assert incident.statut == Incident.StatutIncident.EN_COURS
        intervention = Intervention.objects.get(incident=incident)
        assert intervention.agent == user_agent
        assert intervention.statut == Intervention.Statut.EN_ATTENTE
        assert Notification.objects.filter(utilisateur=user_agent).exists()
        assert Notification.objects.filter(utilisateur=incident.signale_par).exists()

    def test_assignation_refuse_un_non_agent(self, user_admin, user_citoyen, incident):
        response = self.assigner(user_admin, incident, user_citoyen)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reassignation_reutilise_l_intervention(self, user_admin, user_agent, agent_profil, incident):
        from django.contrib.auth import get_user_model

        autre = get_user_model().objects.create_user(username="agent2", password="x", role="agent")
        Agent.objects.create(utilisateur=autre, matricule="AG-002")
        self.assigner(user_admin, incident, user_agent)
        self.assigner(user_admin, incident, autre)

        assert Intervention.objects.filter(incident=incident).count() == 1
        assert Intervention.objects.get(incident=incident).agent == autre

    def test_agent_voit_l_incident_dans_ses_interventions(self, user_admin, user_agent, agent_profil, incident):
        self.assigner(user_admin, incident, user_agent)
        self.client.force_authenticate(user=user_agent)

        response = self.client.get("/api/interventions/my/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["incident_details"]["description"] == "Dépôt sauvage"

    def test_rapport_termine_intervention_et_resout_incident(self, user_admin, user_agent, agent_profil, incident):
        self.assigner(user_admin, incident, user_agent)
        intervention = Intervention.objects.get(incident=incident)
        self.client.force_authenticate(user=user_agent)
        self.client.patch(f"/api/interventions/{intervention.id}/", {"statut": "EN_COURS"}, format="json")

        response = self.client.post(
            f"/api/interventions/{intervention.id}/rapport/",
            {"photo_avant": image_test("avant.jpg"), "photo_apres": image_test("apres.jpg")},
            format="multipart",
        )

        assert response.status_code == status.HTTP_201_CREATED
        intervention.refresh_from_db()
        incident.refresh_from_db()
        assert intervention.statut == Intervention.Statut.TERMINEE
        assert intervention.date_fin is not None
        assert incident.statut == Incident.StatutIncident.RESOLU
        assert incident.date_resolution is not None

    def test_stats_agent_calculees(self, user_admin, user_agent, agent_profil, incident):
        self.assigner(user_admin, incident, user_agent)
        intervention = Intervention.objects.get(incident=incident)
        self.client.force_authenticate(user=user_agent)
        self.client.patch(f"/api/interventions/{intervention.id}/", {"statut": "EN_COURS"}, format="json")
        self.client.patch(f"/api/interventions/{intervention.id}/", {"statut": "TERMINEE"}, format="json")

        self.client.force_authenticate(user=user_admin)
        response = self.client.get(f"/api/agents/{agent_profil.id}/")

        assert response.data["utilisateur_id"] == user_agent.id
        assert response.data["interventions_terminees"] == 1
        assert response.data["taux_completion"] == 100
        assert response.data["ponctualite"] == 100
        assert len(response.data["activite_semaine"]) == 7

    def test_agent_change_sa_disponibilite(self, user_agent, agent_profil):
        self.client.force_authenticate(user=user_agent)

        response = self.client.patch("/api/agents/me/", {"disponible": False}, format="json")

        assert response.status_code == status.HTTP_200_OK
        agent_profil.refresh_from_db()
        assert agent_profil.disponible is False

    def test_utilisateur_ne_peut_pas_changer_son_role(self, user_citoyen):
        self.client.force_authenticate(user=user_citoyen)

        self.client.patch("/api/auth/me/", {"role": "admin", "quartier": "Plateau"}, format="json")

        user_citoyen.refresh_from_db()
        assert user_citoyen.role == "citoyen"
        assert user_citoyen.quartier == "Plateau"

    def test_dashboard_stats_completes(self, user_admin, incident):
        self.client.force_authenticate(user=user_admin)

        response = self.client.get("/api/dashboard/stats/")

        assert response.data["repartition_par_type"][0]["type"] == "DECHETS"
        assert len(response.data["evolution_30_jours"]) == 30
        assert response.data["evolution_30_jours"][-1]["nouveaux"] == 1
