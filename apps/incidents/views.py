from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Incident, Preuve
from .serializers import (
    IncidentSerializer,
    IncidentCreateSerializer,
    PreuveSerializer,
    PreuveUploadSerializer,
)


class IncidentListView(APIView):
    """
    GET  /api/incidents/  — liste tous les incidents (authentifié)
    POST /api/incidents/  — crée un incident (accessible SANS authentification)
    """

    # La création doit être ouverte au public (signalement citoyen sans compte).
    # La lecture de la liste complète reste réservée aux utilisateurs connectés.
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Liste des incidents",
        responses={200: IncidentSerializer(many=True)},
        tags=["Incidents"],
    )
    def get(self, request):
        incidents = (
            Incident.objects.prefetch_related("preuves").order_by("-date_creation")
        )
        serializer = IncidentSerializer(
            incidents, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Créer un incident (avec ou sans compte)",
        description=(
            "Crée un nouvel incident. Accessible sans authentification : "
            "si l'utilisateur est connecté, `signale_par` est rempli automatiquement, "
            "sinon `signale_par` reste `null`. "
            "Le champ `image` est optionnel : si fourni (multipart/form-data), "
            "une Preuve PHOTO_INITIALE est créée automatiquement. "
            "Taille max image : 5 MB. Formats : JPEG, PNG, WebP."
        ),
        request=IncidentCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="Incident créé avec succès",
                response=IncidentSerializer,
            ),
            400: OpenApiResponse(description="Données invalides"),
        },
        tags=["Incidents"],
    )
    def post(self, request):
        serializer = IncidentCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        # signale_par = utilisateur connecté, ou None si signalement anonyme
        signale_par = request.user if request.user.is_authenticated else None
        incident = serializer.save(signale_par=signale_par)

        output = IncidentSerializer(incident, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class MesIncidentsView(APIView):
    """
    GET /api/incidents/my/ — liste uniquement les incidents du citoyen connecté.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mes signalements",
        description="Retourne uniquement les incidents signalés par l'utilisateur connecté.",
        responses={200: IncidentSerializer(many=True)},
        tags=["Incidents"],
    )
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
    """
    POST /api/incidents/preuves/upload/

    Upload d'une photo de preuve pour un incident existant.
    Corps multipart/form-data :
      - incident_id  (integer)
      - type         (PHOTO_INITIALE | PHOTO_AVANT | PHOTO_APRES)
      - image        (fichier requis, < 5 MB, JPEG/PNG/WebP)
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Upload d'une photo de preuve",
        description=(
            "Upload multipart d'une image attachée à un incident existant. "
            "L'image est OBLIGATOIRE sur cet endpoint. "
            "Taille max : 5 MB. Formats acceptés : JPEG, PNG, WebP."
        ),
        request=PreuveUploadSerializer,
        responses={
            201: OpenApiResponse(
                description="Preuve créée avec succès",
                response=PreuveSerializer,
            ),
            400: OpenApiResponse(description="Données invalides"),
            404: OpenApiResponse(description="Incident introuvable"),
        },
        tags=["Incidents"],
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

        output = PreuveSerializer(preuve, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)
