from rest_framework import serializers

from .models import Intervention, Rapport
from apps.users.models import Agent

# On réutilise le serializer Incident déjà existant.
# Cela permet de récupérer les informations complètes de l'incident
# dans la réponse d'une intervention.
from apps.incidents.serializers import IncidentSerializer


class RapportSerializer(serializers.ModelSerializer):
    """
    Sérialiseur des rapports de clôture.

    L'intervention est déterminée par l'URL :
    /api/interventions/<id>/rapport/

    Le frontend n'a donc pas besoin de l'envoyer dans le POST.
    """

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

        read_only_fields = [
            "id",
            "intervention",
            "date_envoi",
        ]


class InterventionSerializer(serializers.ModelSerializer):
    """
    Lecture complète d'une intervention.

    L'incident est volontairement imbriqué dans la réponse
    afin que le frontend de l'agent puisse afficher directement :

    - la référence de l'incident
    - le type
    - la description
    - le niveau d'urgence
    - l'adresse
    - les preuves/photos
    - les autres informations de l'incident

    Le frontend n'a donc pas besoin de faire une deuxième
    requête vers /api/incidents/<id>/.
    """

    incident = IncidentSerializer(read_only=True)

    # ----------------------------------------------------------
    # RAPPORT
    # ----------------------------------------------------------
    #
    # Le rapport est imbriqué lorsqu'il existe.
    # Si aucun rapport n'existe encore, la valeur sera null.
    rapport = RapportSerializer(read_only=True)

    class Meta:
        model = Intervention
        fields = [
            "id",
            "numero_suivi",
            "incident",
            "agent",
            "agent_nom",
            "statut",
            "date_debut",
            "date_fin",
            "rapport",
        ]
        read_only_fields = ["id", "numero_suivi", "agent_nom",]
        
    agent_nom = serializers.SerializerMethodField()   
    def get_agent_nom(self, obj):
        if not obj.agent:
            return None

        return (
            obj.agent.get_full_name()
            or obj.agent.username
        )


class InterventionCreateSerializer(serializers.ModelSerializer):
    """
    Création d'une intervention.

    Une intervention peut être créée par un administrateur.
    L'agent fourni doit obligatoirement correspondre à un profil Agent.
    """

    class Meta:
        model = Intervention
        fields = [
            "incident",
            "agent",
            "statut",
            "date_debut",
            "date_fin",
            "numero_suivi",
        ]
        extra_kwargs = {
            "numero_suivi": {"required": False},
        }

    def validate_agent(self, value):
        """
        Vérifie que le compte utilisateur sélectionné possède
        bien un profil Agent.
        """

        if not hasattr(value, "profil_agent"):
            raise serializers.ValidationError(
                "L'utilisateur sélectionné n'est pas un agent."
            )

        return value

    def validate_numero_suivi(self, value):
        if value and Intervention.objects.filter(
            numero_suivi=value
        ).exists():
            raise serializers.ValidationError(
                f"Le numéro de suivi '{value}' est déjà utilisé."
            )

        return value


class InterventionUpdateSerializer(serializers.ModelSerializer):
    """
    Mise à jour d'une intervention.

    Le champ `agent` n'est volontairement pas modifiable ici.

    L'assignation d'un agent relève du superviseur/admin.
    Un agent peut uniquement modifier les informations
    opérationnelles de son intervention.
    """

    class Meta:
        model = Intervention
        fields = [
            "statut",
            "date_debut",
            "date_fin",
        ]
