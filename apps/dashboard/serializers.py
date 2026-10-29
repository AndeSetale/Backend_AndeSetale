from rest_framework import serializers

# ==========================================================
# DASHBOARD ADMIN / SUPERVISEUR
# ==========================================================

class SignalementsStatsSerializer(serializers.Serializer):
    """
    Compteurs globaux des signalements.
    """

    total = serializers.IntegerField()
    en_cours = serializers.IntegerField()
    resolus = serializers.IntegerField()
    urgents = serializers.IntegerField()


class IncidentParStatutSerializer(serializers.Serializer):
    """
    Nombre d'incidents pour chaque statut.
    """

    statut = serializers.CharField()
    count = serializers.IntegerField()


class DashboardStatsSerializer(serializers.Serializer):
    """
    Réponse de GET /api/dashboard/stats/.

    Utilisé pour documenter et valider la structure
    de la réponse du dashboard administrateur.
    """

    signalements = SignalementsStatsSerializer()
    incidents_par_statut = IncidentParStatutSerializer(
        many=True
    )
    agents_disponibles = serializers.IntegerField()


# ==========================================================
# DASHBOARD AGENT
# ==========================================================

class AgentDashboardInfoSerializer(serializers.Serializer):
    """
    Informations de base de l'agent connecté.
    """

    id = serializers.IntegerField()

    nom_complet = serializers.CharField()

    matricule = serializers.CharField()

    # Peut être null si aucune spécialisation
    # n'est définie pour l'agent.
    specialisation = serializers.CharField(
        allow_null=True,
    )


class AgentDashboardStatsSerializer(serializers.Serializer):
    """
    Statistiques personnelles affichées sur le
    dashboard de l'agent.
    """

    # Nombre d'interventions terminées depuis
    # le début de la semaine actuelle.
    taches_resolues_semaine = serializers.IntegerField()

    # Nombre d'interventions actuellement EN_COURS.
    interventions_en_cours = serializers.IntegerField()

    # Taux de complétion enregistré sur le profil Agent.
    taux_completion = serializers.FloatField()

    # Taux de ponctualité enregistré sur le profil Agent.
    ponctualite = serializers.FloatField()


class AgentDashboardInterventionSerializer(serializers.Serializer):
    """
    Représentation simplifiée d'une intervention pour le dashboard agent.

    Cette structure correspond exactement aux données envoyées
    par AgentDashboardView.
    """

    id = serializers.IntegerField()
    numero_suivi = serializers.CharField()

    statut = serializers.CharField()

    date_debut = serializers.DateTimeField(
        allow_null=True
    )

    date_fin = serializers.DateTimeField(
        allow_null=True
    )

    # ----------------------------------------------------------
    # Informations provenant de l'incident associé
    # ----------------------------------------------------------

    incident_id = serializers.IntegerField()

    reference = serializers.CharField()

    type = serializers.CharField()

    description = serializers.CharField()

    niveau_urgence = serializers.CharField()

    quartier = serializers.CharField(
        allow_null=True,
        allow_blank=True,
    )

    adresse = serializers.CharField(
        allow_null=True,
        allow_blank=True,
    )




class AgentDashboardSerializer(serializers.Serializer):
    """
    Réponse complète de :

    GET /api/dashboard/agent/

    Structure envoyée au frontend :

    {
        "agent": {...},
        "statistiques": {...},
        "interventions_prioritaires": [...],
        "interventions_recentes": [...]
    }
    """

    agent = AgentDashboardInfoSerializer()

    statistiques = AgentDashboardStatsSerializer()

    interventions_prioritaires = (
        AgentDashboardInterventionSerializer(
            many=True
        )
    )

    interventions_recentes = (
        AgentDashboardInterventionSerializer(
            many=True
        )
    )
