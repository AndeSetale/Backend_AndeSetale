from rest_framework import serializers

from .models import Incident, Preuve

# Taille max autorisée pour les uploads : 5 MB
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB en octets
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]


class PreuveUploadSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'upload d'une photo de preuve via multipart/form-data.

    Valide :
    - Format : JPEG, PNG, WebP uniquement
    - Taille : < 5 MB
    """

    class Meta:
        model = Preuve
        fields = ["id", "type", "image", "date_ajout", "url"]
        read_only_fields = ["id", "date_ajout", "url"]

    def validate_image(self, image):
        # Validation taille
        if image.size > MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f"La taille de l'image dépasse la limite autorisée de 5 MB "
                f"(reçu : {image.size / (1024 * 1024):.1f} MB)."
            )
        # Validation format MIME
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise serializers.ValidationError(
                f"Format non supporté : {image.content_type}. "
                f"Formats acceptés : JPEG, PNG, WebP."
            )
        return image

    def to_representation(self, instance):
        """Inclure l'URL absolue dans la réponse."""
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and instance.image:
            data["url"] = request.build_absolute_uri(instance.image.url)
        return data


class PreuveListSerializer(serializers.ModelSerializer):
    """Serializer lecture seule pour lister les preuves d'un incident."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = Preuve
        fields = ["id", "type", "url", "date_ajout"]

    def get_url(self, obj):
        request = self.context.get("request")
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


class IncidentSerializer(serializers.ModelSerializer):
    """Serializer de base pour un incident (sans les preuves)."""

    class Meta:
        model = Incident
        fields = [
            "id",
            "reference",
            "type",
            "description",
            "statut",
            "niveau_urgence",
            "quartier",
            "adresse",
            "latitude",
            "longitude",
            "date_creation",
            "date_estimation_heures",
            "commentaire",
            "signale_par",
            "assigne_a",
        ]
        read_only_fields = ["id", "reference", "date_creation"]
