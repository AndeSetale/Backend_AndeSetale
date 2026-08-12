from rest_framework import serializers


class SignalementsStatsSerializer(serializers.Serializer):
    """Compteurs globaux des signalements."""

    total = serializers.IntegerField()
    en_cours = serializers.IntegerField()
    resolus = serializers.IntegerField()
    urgents = serializers.IntegerField()


class IncidentParStatutSerializer(serializers.Serializer):
    """Ligne de la répartition des incidents par statut."""

    statut = serializers.CharField()
    count = serializers.IntegerField()


class DashboardStatsSerializer(serializers.Serializer):
    """
    Réponse complète de GET /api/dashboard/stats/.

    Utilisé uniquement pour la documentation OpenAPI (drf-spectacular).
    La vue construit le dict manuellement pour éviter un aller-retour DB
    inutile via .to_representation().
    """

    signalements = SignalementsStatsSerializer()
    incidents_par_statut = IncidentParStatutSerializer(many=True)
    agents_disponibles = serializers.IntegerField()
