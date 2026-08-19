from rest_framework import serializers

from .models import Intervention, Rapport
# serializers sert à générer les APIs REST

class RapportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rapport
        fields = [
            "id",
            "intervention",
            "photo_avant",
            "photo_apres",
            "date_envoi",
            "statut",
        ]
        read_only_fields = ["id", "date_envoi"]

class InterventionSerializer(serializers.ModelSerializer):
    """Lecture complète d'une intervention avec son rapport s'il existe."""

    rapport = RapportSerializer(read_only=True)

    class Meta:
        model = Intervention
        fields = [
            "id",
            "numero_suivi",
            "incident",
            "agent",
            "statut",
            "date_debut",
            "date_fin",
            "rapport",
        ]
        read_only_fields = ["id", "numero_suivi"]


class InterventionCreateSerializer(serializers.ModelSerializer):
    """
    Création d'une intervention (assignation d'un agent à un incident).
    Le numéro de suivi est généré automatiquement si non fourni.
    """

    class Meta:
        model = Intervention
        fields = ["incident", "agent", "statut", "date_debut", "date_fin", "numero_suivi"]
        extra_kwargs = {
            "numero_suivi": {"required": False},
        }

    def validate_numero_suivi(self, value):
        if value and Intervention.objects.filter(numero_suivi=value).exists():
            raise serializers.ValidationError(
                f"Le numéro de suivi '{value}' est déjà utilisé."
            )
        return value


class InterventionUpdateSerializer(serializers.ModelSerializer):
    """Mise à jour partielle d'une intervention (statut, dates)."""

    class Meta:
        model = Intervention
        fields = ["agent", "statut", "date_debut", "date_fin"]
