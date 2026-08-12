from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import generics, parsers, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Incident, Preuve
from .serializers import PreuveListSerializer, PreuveUploadSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Lister les preuves d'un incident",
        description="Retourne toutes les photos attachées à l'incident.",
        responses={200: PreuveListSerializer(many=True)},
        tags=["Incidents - Preuves"],
    ),
    post=extend_schema(
        summary="Uploader une photo de preuve",
        description=(
            "Upload d'une photo via multipart/form-data. "
            "Formats acceptés : JPEG, PNG, WebP. Taille max : 5 MB."
        ),
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["PHOTO_INITIALE", "PHOTO_AVANT", "PHOTO_APRES"],
                    },
                    "image": {"type": "string", "format": "binary"},
                },
                "required": ["type", "image"],
            }
        },
        responses={
            201: PreuveUploadSerializer,
            400: OpenApiResponse(description="Validation échouée (taille/format)"),
            404: OpenApiResponse(description="Incident non trouvé"),
        },
        tags=["Incidents - Preuves"],
    ),
)
class PreuveListCreateView(generics.GenericAPIView):
    """
    GET  /api/incidents/{incident_id}/preuves/   — Lister les photos d'un incident
    POST /api/incidents/{incident_id}/preuves/   — Uploader une photo (multipart/form-data)
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def _get_incident(self, incident_id):
        try:
            return Incident.objects.get(pk=incident_id)
        except Incident.DoesNotExist:
            raise NotFound(f"Incident #{incident_id} introuvable.")

    def get(self, request, incident_id):
        incident = self._get_incident(incident_id)
        preuves = incident.preuves.all()
        serializer = PreuveListSerializer(
            preuves, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request, incident_id):
        incident = self._get_incident(incident_id)
        serializer = PreuveUploadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(incident=incident)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Supprimer une preuve",
    description="Supprime une photo de preuve et le fichier associé.",
    responses={
        204: OpenApiResponse(description="Preuve supprimée"),
        404: OpenApiResponse(description="Preuve ou incident introuvable"),
    },
    tags=["Incidents - Preuves"],
)
class PreuveDestroyView(generics.GenericAPIView):
    """DELETE /api/incidents/{incident_id}/preuves/{preuve_id}/"""

    permission_classes = [IsAuthenticated]

    def delete(self, request, incident_id, preuve_id):
        try:
            preuve = Preuve.objects.get(pk=preuve_id, incident_id=incident_id)
        except Preuve.DoesNotExist:
            raise NotFound("Preuve introuvable.")

        # Supprimer le fichier physique avant de supprimer l'objet
        if preuve.image:
            preuve.image.delete(save=False)
        preuve.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
