from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer, NotificationMarkReadSerializer


class NotificationListView(APIView):
    """
    GET /api/notifications/
    Liste les notifications de l'utilisateur connecté (les non-lues en premier).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mes notifications",
        description="Retourne les notifications de l'utilisateur connecté, non-lues en premier.",
        responses={200: NotificationSerializer(many=True)},
        tags=["Notifications"],
    )
    def get(self, request):
        notifications = (
            Notification.objects
            .filter(utilisateur=request.user)
            .order_by("lu", "-date_envoi")   # non-lues d'abord
        )
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class NotificationMarkReadView(APIView):
    """
    POST /api/notifications/mark-read/
    Marque une liste de notifications comme lues.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Marquer des notifications comme lues",
        request=NotificationMarkReadSerializer,
        responses={
            200: OpenApiResponse(description="Notifications mises à jour"),
            400: OpenApiResponse(description="Données invalides"),
        },
        tags=["Notifications"],
    )
    def post(self, request):
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids = serializer.validated_data["ids"]
        updated = (
            Notification.objects
            .filter(id__in=ids, utilisateur=request.user, lu=False)
            .update(lu=True)
        )
        return Response(
            {"marked_read": updated},
            status=status.HTTP_200_OK,
        )


class NotificationUnreadCountView(APIView):
    """
    GET /api/notifications/unread-count/
    Retourne le nombre de notifications non lues de l'utilisateur connecté.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Nombre de notifications non lues",
        responses={
            200: OpenApiResponse(description="Compteur retourné"),
        },
        tags=["Notifications"],
    )
    def get(self, request):
        count = Notification.objects.filter(
            utilisateur=request.user, lu=False
        ).count()
        return Response({"unread_count": count})
