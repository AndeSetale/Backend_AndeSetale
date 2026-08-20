from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.users.permissions import IsAgentOrAdmin

from .models import Intervention,Rapport
from .serializers import (
    InterventionSerializer,
    InterventionCreateSerializer,
    InterventionUpdateSerializer,
    RapportSerializer,
)
from apps.users.permissions import IsAgent, IsAgentOrAdmin

class InterventionListView(APIView):
    """
    GET  /api/interventions/
        - Agent : liste uniquement ses interventions.
        - Admin : liste toutes les interventions.

    POST /api/interventions/
        - Agent : interdit.
        - Admin : crée une intervention et assigne un agent.
    """

    permission_classes = [IsAgentOrAdmin]

    # ==========================================================
    # LISTE DES INTERVENTIONS
    # ==========================================================

    @extend_schema(
        summary="Liste des interventions",
        description=(
            "Retourne les interventions accessibles à l'utilisateur. "
            "Un agent ne voit que ses propres interventions. "
            "Un administrateur peut voir toutes les interventions."
        ),
        responses={
            200: InterventionSerializer(many=True),
        },
        tags=["Interventions"],
    )
    def get(self, request):

        interventions = (
            Intervention.objects
            .select_related("incident", "agent", "rapport")
        )

        # L'administrateur peut voir toutes les interventions.
        # Un agent ne voit que les interventions qui lui sont assignées.
        if request.user.role != request.user.Role.ADMIN:
            interventions = interventions.filter(
                agent=request.user
            )

        interventions = interventions.order_by("-date_debut")

        serializer = InterventionSerializer(
            interventions,
            many=True
        )

        return Response(serializer.data)


        

    # ==========================================================
    # CRÉATION D'UNE INTERVENTION
    # ==========================================================

    @extend_schema(
        summary="Créer une intervention",
        description=(
            "Crée une intervention et l'assigne à un agent. "
            "Cette opération est réservée aux administrateurs."
        ),
        request=InterventionCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="Intervention créée",
                response=InterventionSerializer,
            ),
            400: OpenApiResponse(
                description="Données invalides"
            ),
            403: OpenApiResponse(
                description="Accès réservé aux administrateurs"
            ),
        },
        tags=["Interventions"],
    )
    def post(self, request):

        # ------------------------------------------------------
        # SÉCURITÉ AGENT
        # ------------------------------------------------------
        # Les agents ne créent pas eux-mêmes des interventions.
        # L'assignation est faite par l'administrateur.
        if request.user.role == "agent":
            return Response(
                {
                    "detail": (
                        "Un agent ne peut pas créer une intervention. "
                        "Les interventions sont assignées par un "
                        "administrateur."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = InterventionCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        intervention = serializer.save()

        output = InterventionSerializer(
            intervention
        )

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )


# ==============================================================
# MES INTERVENTIONS — AGENT
# ==============================================================

class MesInterventionsView(APIView):
    """
    GET /api/interventions/my/

    Retourne uniquement les interventions assignées
    à l'agent actuellement connecté.

    Cet endpoint est volontairement réservé aux agents.
    """

    permission_classes = [IsAgent]

    @extend_schema(
        summary="Mes interventions",
        description=(
            "Retourne uniquement les interventions assignées "
            "à l'agent connecté."
        ),
        responses={
            200: InterventionSerializer(many=True),
        },
        tags=["Interventions"],
    )
    def get(self, request):

        interventions = (
            Intervention.objects
            .filter(agent=request.user)
            .select_related(
                "incident",
                "agent",
                "rapport",
            )
            .order_by(
                "-date_debut",
                "-id",
            )
        )

        serializer = InterventionSerializer(
            interventions,
            many=True,
        )

        return Response(
            serializer.data
        )



class InterventionDetailView(APIView):
    """
    GET   /api/interventions/<id>/  — détail
    PATCH /api/interventions/<id>/  — mise à jour partielle

    ADMIN :
        Peut consulter et modifier toutes les interventions.

    AGENT :
        Peut consulter et modifier uniquement les interventions
        qui lui sont assignées.
    """

    permission_classes = [IsAgentOrAdmin]

    @extend_schema(
        summary="Détail d'une intervention",
        responses={
            200: InterventionSerializer,
            404: OpenApiResponse(
                description="Intervention introuvable ou non accessible",
            ),
        },
        tags=["Interventions"],
    )
    def get(self, request, pk):

        # ------------------------------------------------------
        # ADMIN : accès à toutes les interventions
        # ------------------------------------------------------
        if request.user.role == request.user.Role.ADMIN:
            intervention = get_object_or_404(
                Intervention.objects.select_related(
                    "incident",
                    "agent",
                    "rapport",
                ),
                pk=pk,
            )

        # ------------------------------------------------------
        # AGENT : uniquement ses interventions
        # ------------------------------------------------------
        else:
            intervention = get_object_or_404(
                Intervention.objects.select_related(
                    "incident",
                    "agent",
                    "rapport",
                ),
                pk=pk,
                agent=request.user,
            )

        serializer = InterventionSerializer(intervention)

        return Response(serializer.data)

    @extend_schema(
        summary="Mettre à jour une intervention",
        request=InterventionUpdateSerializer,
        responses={
            200: InterventionSerializer,
            400: OpenApiResponse(
                description="Données invalides ou transition impossible",
            ),
            404: OpenApiResponse(
                description="Intervention introuvable ou non accessible",
            ),
        },
        tags=["Interventions"],
    )
    def patch(self, request, pk):

        # ------------------------------------------------------
        # Récupération sécurisée de l'intervention
        # ------------------------------------------------------

        if request.user.role == request.user.Role.ADMIN:
            intervention = get_object_or_404(
                Intervention,
                pk=pk,
            )
        else:
            intervention = get_object_or_404(
                Intervention,
                pk=pk,
                agent=request.user,
            )

        # Copie des données reçues afin de pouvoir
        # ajouter automatiquement les dates.
        data = request.data.copy()

        nouveau_statut = data.get("statut")

        # ------------------------------------------------------
        # Contrôle du workflow Agent
        # ------------------------------------------------------

        if nouveau_statut:

            transitions_autorisees = {
                Intervention.Statut.EN_ATTENTE: [
                    Intervention.Statut.EN_COURS,
                ],
                Intervention.Statut.EN_COURS: [
                    Intervention.Statut.TERMINEE,
                ],
                Intervention.Statut.TERMINEE: [],
            }

            # L'admin n'est pas soumis aux transitions
            # opérationnelles de l'agent.
            if request.user.role != request.user.Role.ADMIN:

                if nouveau_statut not in transitions_autorisees.get(
                    intervention.statut,
                    [],
                ):
                    return Response(
                        {
                            "detail": (
                                f"Transition impossible : "
                                f"{intervention.statut} → "
                                f"{nouveau_statut}."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # --------------------------------------------------
            # Début de l'intervention
            # --------------------------------------------------

            if (
                nouveau_statut == Intervention.Statut.EN_COURS
                and intervention.date_debut is None
            ):
                data["date_debut"] = timezone.now()

            # --------------------------------------------------
            # Fin de l'intervention
            # --------------------------------------------------

            if (
                nouveau_statut == Intervention.Statut.TERMINEE
                and intervention.date_fin is None
            ):
                data["date_fin"] = timezone.now()

        # ------------------------------------------------------
        # Mise à jour
        # ------------------------------------------------------

        serializer = InterventionUpdateSerializer(
            intervention,
            data=data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        intervention = serializer.save()

        # ------------------------------------------------------
        # Réponse
        # ------------------------------------------------------

        output = InterventionSerializer(intervention)

        return Response(output.data)





class RapportView(APIView):
    """
    Gestion du rapport de clôture d'une intervention.

    ADMIN :
        peut consulter, créer et modifier les rapports de toutes
        les interventions.

    AGENT :
        peut uniquement consulter, créer et modifier le rapport
        de l'intervention qui lui est assignée.
    """

    permission_classes = [IsAgentOrAdmin]

    def get_intervention(self, request, intervention_id):
        """
        Retourne l'intervention si elle est accessible par l'utilisateur.

        ADMIN → toutes les interventions.
        AGENT → uniquement ses interventions.
        """

        queryset = Intervention.objects.select_related(
            "incident",
            "agent",
        )

        if request.user.role != request.user.Role.ADMIN:
            queryset = queryset.filter(
                agent=request.user
            )

        return get_object_or_404(
            queryset,
            pk=intervention_id,
        )

    @extend_schema(
        summary="Consulter le rapport de clôture",
        responses={
            200: RapportSerializer,
            404: OpenApiResponse(
                description="Rapport introuvable ou intervention non accessible"
            ),
        },
        tags=["Interventions"],
    )
    def get(self, request, intervention_id):

        intervention = self.get_intervention(
            request,
            intervention_id,
        )

        rapport = get_object_or_404(
            Rapport,
            intervention=intervention,
        )

        serializer = RapportSerializer(rapport)

        return Response(serializer.data)

    @extend_schema(
        summary="Créer un rapport de clôture",
        request=RapportSerializer,
        responses={
            201: RapportSerializer,
            400: OpenApiResponse(
                description="Données invalides"
            ),
            404: OpenApiResponse(
                description="Intervention non accessible"
            ),
        },
        tags=["Interventions"],
    )
    def post(self, request, intervention_id):

        intervention = self.get_intervention(
            request,
            intervention_id,
        )

        # Une intervention ne peut avoir qu'un seul rapport.
        if Rapport.objects.filter(
            intervention=intervention
        ).exists():
            return Response(
                {
                    "detail": "Un rapport existe déjà pour cette intervention."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RapportSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        rapport = serializer.save(
            intervention=intervention
        )

        return Response(
            RapportSerializer(rapport).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Modifier le rapport de clôture",
        request=RapportSerializer,
        responses={
            200: RapportSerializer,
            400: OpenApiResponse(
                description="Données invalides"
            ),
            404: OpenApiResponse(
                description="Rapport introuvable ou intervention non accessible"
            ),
        },
        tags=["Interventions"],
    )
    def patch(self, request, intervention_id):

        intervention = self.get_intervention(
            request,
            intervention_id,
        )

        rapport = get_object_or_404(
            Rapport,
            intervention=intervention,
        )

        serializer = RapportSerializer(
            rapport,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(serializer.data)

