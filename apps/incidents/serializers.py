from rest_framework import serializers

from .models import Incident, Preuve, AnalyseIA


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
# Preuve — lecture
# ---------------------------------------------------------------------------

class PreuveSerializer(serializers.ModelSerializer):
    """Lecture d'une preuve (URL publique de l'image)."""

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Preuve
        fields = ["id", "type", "image_url", "date_ajout"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# ---------------------------------------------------------------------------
# Preuve — upload multipart
# ---------------------------------------------------------------------------

class PreuveUploadSerializer(serializers.Serializer):
    """
    Upload multipart d'une photo de preuve pour un incident existant.

    Règle image :
    - Requis à l'upload (required=True par défaut sur ImageField)
    - Non stocké en base si non fourni (blank=True, null=True sur le modèle)
    """

    incident_id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=Preuve.TypePreuve.choices)
    # L'image est OBLIGATOIRE lors d'un upload — c'est l'objet même de cet endpoint.
    image = serializers.ImageField(
        required=True,
        allow_empty_file=False,
        use_url=False,  # on construit l'URL manuellement dans PreuveSerializer
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
# AnalyseIA — lecture + écriture (géré par le service IA du coéquipier)
# ---------------------------------------------------------------------------

class AnalyseIASerializer(serializers.ModelSerializer):
    """
    Lecture/écriture du résultat d'analyse IA pour un incident.

    Cet endpoint est réservé au service IA (coéquipier).
    Le backend expose uniquement le contrat de données — la logique
    d'inférence reste côté service IA.

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

    Le champ `image` est optionnel à la création (le citoyen peut ne pas
    avoir de photo immédiatement). Une image peut être ajoutée plus tard
    via POST /api/incidents/preuves/upload/.

    Si `image` est fourni, une Preuve de type PHOTO_INITIALE est créée
    automatiquement après la sauvegarde de l'incident.
    """

    # Champ transient : présent à l'écriture, absent de la réponse.
    # required=False → l'image est optionnelle à la création.
    image = serializers.ImageField(
        required=False,
        allow_empty_file=False,
        write_only=True,
        use_url=False,
        help_text="Photo initiale (optionnelle). Max 5 MB. Formats : JPEG, PNG, WebP.",
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
            # champ transient — write only
            "image",
        ]

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
    """Lecture complète d'un incident avec ses preuves et son analyse IA."""

    preuves = PreuveSerializer(many=True, read_only=True)
    # Null si l'analyse IA n'a pas encore été effectuée
    analyse_ia = AnalyseIASerializer(read_only=True)

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
            "preuves",
            "analyse_ia",   # null tant que le service IA n'a pas posté
        ]
        read_only_fields = ["id", "reference", "date_creation"]


# ---------------------------------------------------------------------------
# Incident — mise à jour par un agent/admin (statut, assignation, priorité)
# ---------------------------------------------------------------------------

class IncidentUpdateSerializer(serializers.ModelSerializer):
    """Mise à jour partielle par un agent/admin (statut, assignation, notes)."""

    class Meta:
        model = Incident
        fields = [
            "statut",
            "niveau_urgence",
            "assigne_a",
            "commentaire",
            "date_estimation_heures",
        ]
