"""
Serializers REST Framework pour le module des incidents / signalements.
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

from apps.users.models import Utilisateur
from apps.incidents.geo import point_dans_plateau

from .models import AnalyseIA, Incident, Preuve


# ---------------------------------------------------------------------------
# Constantes de validation
# ---------------------------------------------------------------------------

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _validate_image(value):
    """Validation partagée : taille ≤ 5 MB et format JPEG/PNG/WebP."""
    if value.size > MAX_IMAGE_SIZE_BYTES:
        raise serializers.ValidationError(
            f"L'image dépasse la taille maximale autorisée de 5 MB "
            f"(taille reçue : {value.size / 1024 / 1024:.1f} MB)."
        )
    content_type = getattr(value, "content_type", None)
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise serializers.ValidationError(
            f"Format non supporté : {content_type}. "
            f"Formats acceptés : JPEG, PNG, WebP."
        )
    return value


# ---------------------------------------------------------------------------
# Utilisateur simplifié — lecture imbriquée
# ---------------------------------------------------------------------------

class UtilisateurSimplifieSerializer(serializers.ModelSerializer):
    """Serializer ultra-léger pour afficher l'auteur et l'agent assigné."""

    nom_complet = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "nom_complet",
            "email",
            "role",
            "telephone",
        ]

    def get_nom_complet(self, obj):
        return obj.get_full_name() or obj.username


# ---------------------------------------------------------------------------
# Preuve — lecture
# ---------------------------------------------------------------------------

class PreuveSerializer(serializers.ModelSerializer):
    """Serializer pour les preuves/photos associées à un incident."""

    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Preuve
        fields = ["id", "type", "type_display", "url", "date_ajout"]


# ---------------------------------------------------------------------------
# Preuve — upload standalone (photo avant/après par un agent)
# ---------------------------------------------------------------------------

class PreuveUploadSerializer(serializers.Serializer):
    """
    Validation du téléversement d'une preuve photo.
    Usage : POST /api/incidents/preuves/upload/
    """

    incident_id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=Preuve.TypePreuve.choices)
    image = extend_schema_field(OpenApiTypes.BINARY)(
        serializers.ImageField(
            required=True,
            allow_empty_file=False,
            use_url=False,
        )
    )

    def validate_image(self, value):
        return _validate_image(value)

    def validate_incident_id(self, value):
        if not Incident.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                f"Aucun incident trouvé avec l'id {value}."
            )
        return value


# ---------------------------------------------------------------------------
# AnalyseIA — lecture simplifiée (imbriquée dans IncidentSerializer)
# ---------------------------------------------------------------------------

class AnalyseIASimplifieeSerializer(serializers.ModelSerializer):
    """Serializer pour afficher l'analyse IA attachée à l'incident."""

    class Meta:
        model = AnalyseIA
        fields = [
            "id",
            "type_detecte",
            "score_confiance",
            "niveau_urgence_detecte",
            "description_generee",
            "recommandations",
            "date_analyse",
        ]
        read_only_fields = ["id", "date_analyse"]

    def validate_score_confiance(self, value):
        if not (0.0 <= value <= 1.0):
            raise serializers.ValidationError(
                "Le score de confiance doit être compris entre 0.0 et 1.0."
            )
        return value


# ---------------------------------------------------------------------------
# AnalyseIA — lecture + écriture (endpoint dédié pour le service IA)
# ---------------------------------------------------------------------------

class AnalyseIASerializer(serializers.ModelSerializer):
    """
    Lecture/écriture du résultat d'analyse IA pour un incident.

    Cet endpoint est réservé au service IA.
    Endpoint : POST /api/incidents/<id>/analyse/
    """

    class Meta:
        model = AnalyseIA
        fields = [
            "id",
            "type_detecte",
            "score_confiance",
            "niveau_urgence_detecte",
            "description_generee",
            "recommandations",
            "date_analyse",
        ]
        read_only_fields = ["id", "date_analyse"]

    def validate_score_confiance(self, value):
        if not (0.0 <= value <= 1.0):
            raise serializers.ValidationError(
                "Le score de confiance doit être compris entre 0.0 et 1.0."
            )
        return value


# ---------------------------------------------------------------------------
# Incident — création (avec photo initiale optionnelle inline)
# ---------------------------------------------------------------------------

class IncidentCreateSerializer(serializers.ModelSerializer):
    """
    Création d'un incident via multipart/form-data.

    Le champ `image` est optionnel. Si fourni, une Preuve de type
    PHOTO_INITIALE est créée automatiquement après la sauvegarde.
    """

    type = serializers.ChoiceField(
        choices=Incident.TypeIncident.choices,
        required=False,
        default=Incident.TypeIncident.DECHETS,
        help_text="Type d'incident (qualifié automatiquement par l'IA si non renseigné).",
    )
    image = extend_schema_field(OpenApiTypes.BINARY)(
        serializers.ImageField(
            required=False,
            allow_empty_file=False,
            write_only=True,
            use_url=False,
            help_text="Photo initiale (optionnelle). Max 5 MB. Formats : JPEG, PNG, WebP.",
        )
    )

    class Meta:
        model = Incident
        fields = [
            "type",
            "description",
            "niveau_urgence",
            "quartier",
            "adresse",
            "latitude",
            "longitude",
            "date_estimation_heures",
            "commentaire",
            "image",
        ]

    def validate(self, attrs):
        lat = attrs.get("latitude")
        lng = attrs.get("longitude")
        if lat is not None and lng is not None:
            if not point_dans_plateau(lat, lng):
                raise serializers.ValidationError(
                    "Ce signalement est en dehors du périmètre couvert (Dakar-Plateau)."
                )
        return attrs

    def validate_image(self, value):
        return _validate_image(value)

    def create(self, validated_data):
        image = validated_data.pop("image", None)
        incident = super().create(validated_data)
        if image is not None:
            Preuve.objects.create(
                incident=incident,
                type=Preuve.TypePreuve.PHOTO_INITIALE,
                image=image,
            )
        return incident


# ---------------------------------------------------------------------------
# Incident — lecture complète
# ---------------------------------------------------------------------------

class IncidentSerializer(serializers.ModelSerializer):
    """
    Serializer principal pour la lecture complète d'un incident.
    """

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    niveau_urgence_display = serializers.CharField(
        source="get_niveau_urgence_display", read_only=True
    )

    signale_par_details = UtilisateurSimplifieSerializer(
        source="signale_par", read_only=True
    )
    assigne_a_details = UtilisateurSimplifieSerializer(
        source="assigne_a", read_only=True
    )
    preuves = PreuveSerializer(many=True, read_only=True)
    analyse_ia = AnalyseIASimplifieeSerializer(read_only=True)

    class Meta:
        model = Incident
        fields = [
            "id",
            "reference",
            "type",
            "type_display",
            "description",
            "statut",
            "statut_display",
            "niveau_urgence",
            "niveau_urgence_display",
            "quartier",
            "adresse",
            "latitude",
            "longitude",
            "date_creation",
            "date_estimation_heures",
            "commentaire",
            "signale_par",
            "signale_par_details",
            "assigne_a",
            "assigne_a_details",
            "preuves",
            "analyse_ia",
        ]
        read_only_fields = ["id", "reference", "date_creation"]


# ---------------------------------------------------------------------------
# Incident — mise à jour partielle (statut, assignation, notes)
# ---------------------------------------------------------------------------

class IncidentUpdateSerializer(serializers.ModelSerializer):
    """Mise à jour partielle par un agent/admin."""

    class Meta:
        model = Incident
        fields = [
            "statut",
            "niveau_urgence",
            "assigne_a",
            "commentaire",
            "date_estimation_heures",
        ]
