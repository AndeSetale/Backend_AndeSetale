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

class InterventionListView(APIView):
    """
    GET  /api/interventions/  — liste toutes les interventions
    POST /api/interventions/  — crée une intervention
    """

    permission_classes = [IsAgentOrAdmin]

    @extend_schema(
        summary="Liste des interventions",
        responses={200: InterventionSerializer(many=True)},
        tags=["Interventions"],
    )
    def get(self, request):
        interventions = (
            Intervention.objects
            .select_related("incident", "agent", "rapport")
            .order_by("-date_debut")
        )
        serializer = InterventionSerializer(interventions, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Créer une intervention",
        request=InterventionCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="Intervention créée",
                response=InterventionSerializer,
            ),
            400: OpenApiResponse(description="Données invalides"),
        },
        tags=["Interventions"],
    )
    def post(self, request):
        serializer = InterventionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        intervention = serializer.save()
        output = InterventionSerializer(intervention)
        return Response(output.data, status=status.HTTP_201_CREATED)


class InterventionDetailView(APIView):
    """
    GET   /api/interventions/<id>/  — détail
    PATCH /api/interventions/<id>/  — mise à jour partielle (statut, agent, dates)
    """

    permission_classes = [IsAgentOrAdmin]

    @extend_schema(
        summary="Détail d'une intervention",
        responses={
            200: InterventionSerializer,
            404: OpenApiResponse(description="Intervention introuvable"),
        },
        tags=["Interventions"],
    )
    def get(self, request, pk):
        intervention = get_object_or_404(
            Intervention.objects.select_related("incident", "agent", "rapport"),
            pk=pk,
        )
        serializer = InterventionSerializer(intervention)
        return Response(serializer.data)

    @extend_schema(
        summary="Mettre à jour une intervention",
        request=InterventionUpdateSerializer,
        responses={
            200: InterventionSerializer,
            400: OpenApiResponse(description="Données invalides"),
            404: OpenApiResponse(description="Intervention introuvable"),
        },
        tags=["Interventions"],
    )
    def patch(self, request, pk):
        intervention = get_object_or_404(Intervention, pk=pk)
        serializer = InterventionUpdateSerializer(
            intervention, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        intervention = serializer.save()
        output = InterventionSerializer(intervention)
        return Response(output.data)



class RapportView(APIView):
    permission_classes = [IsAgentOrAdmin]

    @extend_schema(
        summary="Consulter le rapport de clôture",
        responses={
            200: RapportSerializer,
            404: OpenApiResponse(
                description="Rapport introuvable"
            ),
        },
        tags=["Interventions"],
    )
    def get(self, request, intervention_id):
        intervention = get_object_or_404(
            Intervention,
            pk=intervention_id
        )

        rapport = get_object_or_404(
            Rapport,
            intervention=intervention
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
        },
        tags=["Interventions"],
    )
    def post(self, request, intervention_id):
        intervention = get_object_or_404(
            Intervention,
            pk=intervention_id
        )

        serializer = RapportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rapport = serializer.save(
            intervention=intervention
        )

        return Response(
            RapportSerializer(rapport).data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Modifier le rapport de clôture",
        request=RapportSerializer,
        responses={
            200: RapportSerializer,
            404: OpenApiResponse(
                description="Rapport introuvable"
            ),
        },
        tags=["Interventions"],
    )
    def patch(self, request, intervention_id):
        intervention = get_object_or_404(
            Intervention,
            pk=intervention_id
        )

        rapport = get_object_or_404(
            Rapport,
            intervention=intervention
        )

        serializer = RapportSerializer(
            rapport,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

class MesInterventionsView(APIView):
    """
    GET /api/interventions/my/
    Retourne les interventions assignées à l'agent connecté.
    """

    permission_classes = [IsAgentOrAdmin]

    @extend_schema(
        summary="Mes interventions",
        description="Retourne les interventions assignées à l'agent connecté.",
        responses={200: InterventionSerializer(many=True)},
        tags=["Interventions"],
    )
    def get(self, request):
        interventions = (
            Intervention.objects
            .filter(agent=request.user)
            .select_related("incident", "agent", "rapport")
            .order_by("-date_debut")
        )

        serializer = InterventionSerializer(
            interventions,
            many=True
        )

        return Response(serializer.data)