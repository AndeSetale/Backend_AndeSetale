from django.db.models import Count

from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.incidents.models import Incident
from apps.users.models import Agent
from .serializers import DashboardStatsSerializer


class DashboardStatsView(APIView):
    """
    GET /api/dashboard/stats/

    Retourne les statistiques globales pour le dashboard superviseur :
    - Compteurs totaux (signalements total, en cours, résolus, urgents)
    - Répartition des incidents par statut
    - Nombre d'agents disponibles
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Statistiques du dashboard superviseur",
        description=(
            "Retourne les compteurs clés et la répartition des incidents par statut. "
            "Accessible uniquement aux utilisateurs authentifiés. "
            "Temps de réponse cible < 500 ms."
        ),
        responses={
            200: OpenApiResponse(
                description="Statistiques retournées avec succès",
                response=DashboardStatsSerializer,
            ),
        },
        tags=["Dashboard"],
    )
    def get(self, request):
        # --- Compteurs signalements (3 requêtes agrégées) ---
        total = Incident.objects.count()
        en_cours = Incident.objects.filter(
            statut=Incident.StatutIncident.EN_COURS
        ).count()
        resolus = Incident.objects.filter(
            statut=Incident.StatutIncident.RESOLU
        ).count()
        urgents = Incident.objects.filter(
            niveau_urgence__in=[
                Incident.NiveauUrgence.CRITIQUE,
                Incident.NiveauUrgence.ELEVE,
            ]
        ).count()

        # --- Incidents par statut (1 requête groupée) ---
        par_statut = (
            Incident.objects.values("statut")
            .annotate(count=Count("id"))
            .order_by("statut")
        )
        incidents_par_statut = [
            {"statut": row["statut"], "count": row["count"]}
            for row in par_statut
        ]

        # --- Agents disponibles ---
        agents_disponibles = Agent.objects.filter(disponible=True).count()

        data = {
            "signalements": {
                "total": total,
                "en_cours": en_cours,
                "resolus": resolus,
                "urgents": urgents,
            },
            "incidents_par_statut": incidents_par_statut,
            "agents_disponibles": agents_disponibles,
        }

        return Response(data)
