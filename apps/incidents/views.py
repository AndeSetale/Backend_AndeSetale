from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.users.permissions import IsAgentOrAdmin
from .models import Incident, Preuve, AnalyseIA
from .ai_service import déclencher_analyse_ia
from .serializers import (
    IncidentSerializer,
    IncidentCreateSerializer,
    PreuveSerializer,
    PreuveUploadSerializer,
    IncidentUpdateSerializer,
    AnalyseIASerializer,
)
from drf_spectacular.utils import extend_schema

# Classe pour lister et creer des incidents.
class IncidentListView(generics.ListCreateAPIView):
    """
    GET  /api/incidents/  — liste tous les incidents (authentifié)
    POST /api/incidents/  — crée un incident (accessible SANS authentification)
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Incident.objects.prefetch_related("preuves").order_by("-date_creation")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["statut", "type", "niveau_urgence", "quartier"]
    search_fields = ["description", "reference", "adresse"]
    ordering_fields = ["date_creation", "niveau_urgence"]

    def get_serializer_class(self):
        return IncidentCreateSerializer if self.request.method == "POST" else IncidentSerializer

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "POST" else [IsAuthenticated()]

    def perform_create(self, serializer):
        signale_par = self.request.user if self.request.user.is_authenticated else None
        serializer.save(signale_par=signale_par)

    @extend_schema(
        request={
            "multipart/form-data": IncidentCreateSerializer,
        },
        responses={201: IncidentSerializer},
        description="Crée un incident avec photo initiale optionnelle et géolocalisation. Déclenche l'analyse IA."
    )
    def create(self, request, *args, **kwargs):
        # On garde le comportement standard de CreateModelMixin, mais on
        # sérialise la RÉPONSE avec IncidentSerializer (lecture complète :
        # id, reference, preuves, analyse_ia...) plutôt qu'avec le serializer
        # de création (write-only, qui n'expose pas ces champs).
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Déclenchement automatique de l'analyse IA si une photo initiale est jointe
        incident = serializer.instance
        preuve_initiale = incident.preuves.filter(type=Preuve.TypePreuve.PHOTO_INITIALE).first()
        if preuve_initiale and preuve_initiale.image:
            déclencher_analyse_ia(incident, preuve_initiale.image)
            incident.refresh_from_db()

        output = IncidentSerializer(incident, context={"request": request})
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)


class MesIncidentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        incidents = (
            Incident.objects.filter(signale_par=request.user)
            .prefetch_related("preuves")
            .order_by("-date_creation")
        )
        serializer = IncidentSerializer(
            incidents, many=True, context={"request": request}
        )
        return Response(serializer.data)


class PreuveUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=PreuveUploadSerializer,
        responses={201: PreuveSerializer},
        description="Téléverse une preuve photo pour un incident existant."
    )
    def post(self, request):
        serializer = PreuveUploadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        incident = Incident.objects.get(pk=serializer.validated_data["incident_id"])
        preuve = Preuve.objects.create(
            incident=incident,
            type=serializer.validated_data["type"],
            image=serializer.validated_data["image"],
        )

        # Déclenchement automatique de l'analyse IA si l'incident n'en a pas encore
        if not hasattr(incident, "analyse_ia"):
            déclencher_analyse_ia(incident, preuve.image)

        output = PreuveSerializer(preuve, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class IncidentDetailView(APIView):
    """
    GET   /api/incidents/<id>/  — détail d'un incident (authentifié)
    PATCH /api/incidents/<id>/  — mise à jour par un agent/admin
    """

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAgentOrAdmin()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        incident = get_object_or_404(
            Incident.objects.prefetch_related("preuves"), pk=pk
        )
        serializer = IncidentSerializer(incident, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, pk):
        incident = get_object_or_404(Incident, pk=pk)
        serializer = IncidentUpdateSerializer(
            incident, data=request.data, partial=True
            )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            IncidentSerializer(incident, context={"request": request}).data 
        )

class AnalyseIAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        incident = get_object_or_404(Incident, pk=pk)
        serializer = AnalyseIASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        analyse, _ = AnalyseIA.objects.update_or_create(
            incident=incident, defaults=serializer.validated_data
        )
        return Response(
            AnalyseIASerializer(analyse).data, status=status.HTTP_201_CREATED
        )
