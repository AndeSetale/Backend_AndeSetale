from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from drf_spectacular.utils import extend_schema, OpenApiResponse

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.incidents.models import Incident
from apps.interventions.models import Intervention
from apps.interventions.stats import stats_agent

from apps.users.models import Agent

from .models import EvenementSetSetal
from apps.users.permissions import IsAdmin, IsAgent, IsAgentOrAdmin

from .serializers import (
    DashboardStatsSerializer,
    AgentDashboardSerializer,
    AgentDashboardInterventionSerializer
)


# ==============================================================
# DASHBOARD ADMIN / SUPERVISEUR
# ==============================================================

class DashboardStatsView(APIView):
    """
    GET /api/dashboard/stats/

    Retourne les statistiques globales du système.

    Cet endpoint est actuellement accessible à tout utilisateur
    authentifié. Il pourra être restreint à IsAdmin si nécessaire
    pour le dashboard administrateur.
    """

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Statistiques du dashboard superviseur",
        description=(
            "Retourne les compteurs clés et la répartition "
            "des incidents par statut."
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

        # ------------------------------------------------------
        # COMPTEURS DES INCIDENTS
        # ------------------------------------------------------

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

        # ------------------------------------------------------
        # RÉPARTITION DES INCIDENTS PAR STATUT
        # ------------------------------------------------------

        par_statut = (
            Incident.objects
            .values("statut")
            .annotate(count=Count("id"))
            .order_by("statut")
        )

        incidents_par_statut = [
            {
                "statut": row["statut"],
                "count": row["count"],
            }
            for row in par_statut
        ]

        # ------------------------------------------------------
        # AGENTS DISPONIBLES
        # ------------------------------------------------------

        agents_disponibles = Agent.objects.filter(
            disponible=True
        ).count()

        # ------------------------------------------------------
        # RÉPONSE
        # ------------------------------------------------------

        # ------------------------------------------------------
        # RÉPARTITION PAR TYPE (donut)
        # ------------------------------------------------------

        labels_type = dict(Incident.TypeIncident.choices)
        repartition_par_type = [
            {
                "type": row["type"],
                "label": labels_type.get(row["type"], row["type"]),
                "count": row["count"],
            }
            for row in Incident.objects.values("type")
            .annotate(count=Count("id"))
            .order_by("-count")
        ]

        # ------------------------------------------------------
        # ÉVOLUTION SUR 30 JOURS (nouveaux vs résolus par jour)
        # ------------------------------------------------------

        aujourd_hui = timezone.localdate()
        depuis = aujourd_hui - timedelta(days=29)

        def par_jour(queryset, champ):
            return {
                row["jour"]: row["total"]
                for row in queryset.filter(**{f"{champ}__date__gte": depuis})
                .annotate(jour=TruncDate(champ))
                .values("jour")
                .annotate(total=Count("id"))
            }

        nouveaux = par_jour(Incident.objects.all(), "date_creation")
        resolus_jour = par_jour(
            Incident.objects.filter(date_resolution__isnull=False), "date_resolution"
        )
        evolution_30_jours = [
            {
                "date": jour.isoformat(),
                "nouveaux": nouveaux.get(jour, 0),
                "resolus": resolus_jour.get(jour, 0),
            }
            for jour in (depuis + timedelta(days=n) for n in range(30))
        ]

        # ------------------------------------------------------
        # PERFORMANCE DES AGENTS (classés par interventions terminées)
        # ------------------------------------------------------

        performance_agents = []
        for agent in Agent.objects.select_related("utilisateur"):
            stats = stats_agent(agent.utilisateur)
            performance_agents.append({
                "id": agent.id,
                "nom_complet": agent.utilisateur.get_full_name() or agent.utilisateur.username,
                "resolus": stats["interventions_terminees"],
                "taux_completion": stats["taux_completion"],
            })
        performance_agents.sort(key=lambda a: a["resolus"], reverse=True)

        data = {
            "signalements": {
                "total": total,
                "en_cours": en_cours,
                "resolus": resolus,
                "urgents": urgents,
            },
            "incidents_par_statut": incidents_par_statut,
            "agents_disponibles": agents_disponibles,
            "repartition_par_type": repartition_par_type,
            "evolution_30_jours": evolution_30_jours,
            "performance_agents": performance_agents[:5],
        }

        return Response(data)


# ==============================================================
# DASHBOARD AGENT
# ==============================================================

class AgentDashboardView(APIView):
    """
    GET /api/dashboard/agent/

    Retourne les informations nécessaires au dashboard
    de l'agent connecté :

    - informations personnelles de l'agent ;
    - statistiques personnelles ;
    - interventions prioritaires ;
    - interventions récentes.

    Un agent ne peut voir que ses propres interventions.
    """

    permission_classes = [IsAgent]

    @extend_schema(
        summary="Dashboard de l'agent",
        description=(
            "Retourne les informations et statistiques de l'agent "
            "connecté ainsi que ses interventions prioritaires "
            "et récentes."
        ),
        responses={
            200: AgentDashboardSerializer,
        },
        tags=["Dashboard"],
    )
    def get(self, request):

        # ======================================================
        # PROFIL AGENT
        # ======================================================

        # request.user est le compte Utilisateur.
        # On récupère le profil Agent correspondant.
        agent = (
            Agent.objects
            .select_related("utilisateur")
            .get(utilisateur=request.user)
        )

        # ======================================================
        # INTERVENTIONS DE L'AGENT CONNECTÉ
        # ======================================================

        # IMPORTANT :
        # On filtre directement avec request.user.
        # L'agent ne peut donc jamais récupérer les interventions
        # d'un autre agent via cet endpoint.
        interventions = (
            Intervention.objects
            .filter(agent=request.user)
            .select_related(
                "incident",
                "agent",
                "rapport",
            )
        )

        # ======================================================
        # STATISTIQUES DE LA SEMAINE
        # ======================================================

        # Date du jour dans le fuseau horaire Django.
        today = timezone.localdate()

        # Lundi de la semaine actuelle.
        debut_semaine = today - timedelta(
            days=today.weekday()
        )

        # ------------------------------------------------------
        # TÂCHES TERMINÉES CETTE SEMAINE
        # ------------------------------------------------------

        taches_resolues_semaine = stats["taches_resolues_semaine"]

        # ------------------------------------------------------
        # INTERVENTIONS ACTUELLEMENT EN COURS
        # ------------------------------------------------------

        interventions_en_cours = interventions.filter(
            statut=Intervention.Statut.EN_COURS,
        ).count()

        # ------------------------------------------------------
        # INDICATEURS DE PERFORMANCE
        # ------------------------------------------------------

        # Ces deux valeurs existent déjà dans le modèle Agent.
        stats = stats_agent(request.user)
        taux_completion = stats["taux_completion"]
        ponctualite = stats["ponctualite"]

        # ======================================================
        # INTERVENTIONS PRIORITAIRES
        # ======================================================

        # Une intervention prioritaire doit :
        # - appartenir à l'agent connecté ;
        # - concerner un incident critique ou élevé ;
        # - ne pas être déjà terminée.
        interventions_prioritaires = (
            interventions
            .filter(
                statut__in=[
                    Intervention.Statut.EN_ATTENTE,
                    Intervention.Statut.EN_COURS,
                ],
                incident__niveau_urgence__in=[
                    Incident.NiveauUrgence.CRITIQUE,
                    Incident.NiveauUrgence.ELEVE,
                ],
            )
            .select_related("incident")
            .order_by(
                "-incident__niveau_urgence",
                "-incident__date_creation",
            )[:5]
        )

        # ======================================================
        # INTERVENTIONS RÉCENTES
        # ======================================================

        # Les 5 dernières interventions de l'agent.
        interventions_recentes = (
            interventions
            .select_related("incident")
            .order_by(
                "-date_debut",
                "-id",
            )[:5]
        )

        # ======================================================
        # SÉRIALISATION DASHBOARD
        # ======================================================

        prioritaires_data = [
        {
            "id": intervention.id,
            "numero_suivi": intervention.numero_suivi,
            "statut": intervention.statut,
            "date_debut": intervention.date_debut,
            "date_fin": intervention.date_fin,

            # Informations de l'incident
            "incident_id": intervention.incident.id,
            "reference": intervention.incident.reference,
            "type": intervention.incident.type,
            "description": intervention.incident.description,
            "niveau_urgence": intervention.incident.niveau_urgence,
            "quartier": intervention.incident.quartier,
            "adresse": intervention.incident.adresse,
        }
        for intervention in interventions_prioritaires
    ]


        recentes_data = [
        {
            "id": intervention.id,
            "numero_suivi": intervention.numero_suivi,
            "statut": intervention.statut,
            "date_debut": intervention.date_debut,
            "date_fin": intervention.date_fin,

            # Informations de l'incident
            "incident_id": intervention.incident.id,
            "reference": intervention.incident.reference,
            "type": intervention.incident.type,
            "description": intervention.incident.description,
            "niveau_urgence": intervention.incident.niveau_urgence,
            "quartier": intervention.incident.quartier,
            "adresse": intervention.incident.adresse,
        }
        for intervention in interventions_recentes
    ]



        # ======================================================
        # CONSTRUCTION DU DASHBOARD
        # ======================================================

        data = {
            "agent": {
                "id": agent.id,
                "nom_complet": (
                    agent.utilisateur
                    .get_full_name()
                    .strip()
                ),
                "matricule": agent.matricule,
                "specialisation": (
                    agent.get_specialisation_display()
                    if agent.specialisation
                    else None
                ),
            },

            "statistiques": {
                "taches_resolues_semaine": (
                    taches_resolues_semaine
                ),
                "interventions_en_cours": (
                    interventions_en_cours
                ),
                "taux_completion": taux_completion,
                "ponctualite": ponctualite,
            },

            "interventions_prioritaires": (
                prioritaires_data
            ),

            "interventions_recentes": (
                recentes_data
            ),
        }

        # Le serializer vérifie que la structure finale
        # correspond bien au contrat prévu pour le frontend.
        serializer = AgentDashboardSerializer(data)

        return Response(serializer.data)


# ==============================================================
# CARTE INCIDENTS — ADMIN / AGENT
# ==============================================================

class IncidentsCarte(APIView):
    """
    GET /api/dashboard/incidents-carte/

    Retourne tous les incidents avec leurs coordonnées GPS
    pour affichage sous forme de points sur la carte admin.

    Accessible aux administrateurs et aux agents.
    """

    permission_classes = [IsAgentOrAdmin]

    @extend_schema(
        summary="Incidents pour la carte",
        description=(
            "Retourne la liste de tous les incidents avec leur position GPS, "
            "type, statut et niveau d'urgence. "
            "Utilisé pour afficher les marqueurs sur la carte du dashboard admin."
        ),
        responses={
            200: OpenApiResponse(description="Liste des incidents géolocalisés"),
        },
        tags=["Dashboard"],
    )
    def get(self, request):
        incidents = Incident.objects.only(
            "id",
            "reference",
            "type",
            "statut",
            "niveau_urgence",
            "quartier",
            "adresse",
            "latitude",
            "longitude",
            "description",
            "date_creation",
        ).order_by("-date_creation")

        data = [
            {
                "id": inc.id,
                "reference": inc.reference,
                "type": inc.type,
                "statut": inc.statut,
                "niveau_urgence": inc.niveau_urgence,
                "quartier": inc.quartier,
                "adresse": inc.adresse,
                "latitude": inc.latitude,
                "longitude": inc.longitude,
                "description": inc.description,
                "date_creation": inc.date_creation,
            }
            for inc in incidents
            if inc.latitude is not None and inc.longitude is not None
        ]

        return Response(data)


# ==============================================================
# PROCHAIN ÉVÉNEMENT SET-SETAL — ACCUEIL CITOYEN (PUBLIC)
# ==============================================================

class ProchainEvenementView(APIView):
    """
    GET /api/dashboard/evenements/prochain/

    Retourne le prochain événement Set-Setal à venir, ou null s'il n'y en a pas.
    Les événements sont créés par l'administrateur (admin Django).
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Prochain événement Set-Setal",
        responses={200: OpenApiResponse(description="Événement ou null")},
        tags=["Dashboard"],
    )
    def get(self, request):
        evenement = EvenementSetSetal.objects.filter(date__gte=timezone.now()).first()
        if evenement is None:
            return Response(None)
        return Response({
            "id": evenement.id,
            "titre": evenement.titre,
            "lieu": evenement.lieu,
            "date": evenement.date,
            "description": evenement.description,
        })
