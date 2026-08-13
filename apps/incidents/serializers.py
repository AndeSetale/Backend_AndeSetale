"""
Serializers REST Framework pour le module des incidents / signalements.
"""

import uuid

from django.utils import timezone
from rest_framework import serializers

from apps.users.models import Utilisateur

from .models import AnalyseIA, Incident, Preuve


class UtilisateurSimplifieSerializer(serializers.ModelSerializer):
    """Serializer ultra-léger pour afficher l'auteur et l'agent assigné."""

    nom_complet = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = ["id", "username", "first_name", "last_name", "nom_complet", "email", "role", "telephone"]

    def get_nom_complet(self, obj):
        return obj.get_full_name() or obj.username


class PreuveSerializer(serializers.ModelSerializer):
    """Serializer pour les preuves/photos associées à un incident."""

    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Preuve
        fields = ["id", "type", "type_display", "url", "date_ajout"]


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


class IncidentSerializer(serializers.ModelSerializer):
    """
    Serializer principal pour le CRUD complet des signalements d'incidents.
    """

    # Libellés lisibles pour les Enums/Choices
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    niveau_urgence_display = serializers.CharField(source="get_niveau_urgence_display", read_only=True)

    # Détails imbriqués en lecture seule
    signale_par_details = UtilisateurSimplifieSerializer(source="signale_par", read_only=True)
    assigne_a_details = UtilisateurSimplifieSerializer(source="assigne_a", read_only=True)
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
        read_only_fields = [
            "id",
            "reference",
            "date_creation",
            "signale_par",
            "assigne_a",
        ]

    def create(self, validated_data):
        """
        Génération automatique de la référence si elle n'est pas fournie.
        Format : SIG-YYYYMMDD-XXXX (ex: SIG-20260812-A1B2)
        """
        if "reference" not in validated_data or not validated_data["reference"]:
            today_str = timezone.now().strftime("%Y%m%d")
            short_hash = uuid.uuid4().hex[:4].upper()
            validated_data["reference"] = f"SIG-{today_str}-{short_hash}"

        return super().create(validated_data)