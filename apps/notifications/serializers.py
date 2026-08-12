from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Lecture d'une notification."""

    class Meta:
        model = Notification
        fields = ["id", "type", "contenu", "lu", "date_envoi"]
        read_only_fields = ["id", "date_envoi"]


class NotificationMarkReadSerializer(serializers.Serializer):
    """Marquer une liste de notifications comme lues."""

    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="Liste des IDs de notifications à marquer comme lues.",
    )
