from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import Agent, Utilisateur


class AgentSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de lecture d'un agent.

    Transforme un objet Agent en représentation JSON destinée au frontend.

    Les informations personnelles sont récupérées depuis le compte
    Utilisateur associé. Le champ `nom_complet` est construit à partir
    de `first_name` et `last_name`.

    Ce sérialiseur est utilisé pour :
    - GET /api/agents/
    - GET /api/agents/<id>/
    - la réponse après création ou modification d'un agent.
    """

    nom_complet = serializers.SerializerMethodField()

    email = serializers.EmailField(
        source="utilisateur.email",
        read_only=True,
    )

    telephone = serializers.CharField(
        source="utilisateur.telephone",
        read_only=True,
    )

    quartier = serializers.CharField(
        source="utilisateur.quartier",
        read_only=True,
    )

    class Meta:
        model = Agent
        fields = [
            "id",
            "nom_complet",
            "email",
            "telephone",
            "quartier",
            "matricule",
            "departement",
            "specialisation",
            "disponible",
            "score_satisfaction",
            "taux_completion",
            "ponctualite",
            "taches_resolues_semaine",
            "objectif_hebdo",
        ]

        read_only_fields = [
            "id",
            "nom_complet",
            "email",
            "telephone",
            "quartier",
        ]

    def get_nom_complet(self, obj):
        return obj.utilisateur.get_full_name().strip()


class AgentCreateSerializer(serializers.Serializer):
    """
    Sérialiseur de création d'un agent.

    Valide les données reçues par l'API puis crée de manière atomique :

    1. le compte Utilisateur ;
    2. le profil Agent associé.

    Le compte créé reçoit automatiquement le rôle AGENT.

    Les données suivantes sont contrôlées avant création :
    - unicité de l'email ;
    - unicité du téléphone ;
    - unicité du matricule ;
    - validité du mot de passe ;
    - présence d'un nom complet.
    """

    nom_complet = serializers.CharField(max_length=150)

    email = serializers.EmailField()

    telephone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    quartier = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
    )

    matricule = serializers.CharField(max_length=50)

    departement = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    specialisation = serializers.ChoiceField(
        choices=Agent.TypeIncident.choices,
        required=False,
        allow_null=True,
    )

    disponible = serializers.BooleanField(default=True)

    score_satisfaction = serializers.FloatField(
        required=False,
        default=0.0,
        min_value=0.0,
    )

    taux_completion = serializers.FloatField(
        required=False,
        default=0.0,
        min_value=0.0,
        max_value=100.0,
    )

    ponctualite = serializers.FloatField(
        required=False,
        default=0.0,
        min_value=0.0,
        max_value=100.0,
    )

    taches_resolues_semaine = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
    )

    objectif_hebdo = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
    )

    def validate_matricule(self, value):
        if Agent.objects.filter(matricule=value).exists():
            raise serializers.ValidationError(
                "Ce matricule est déjà utilisé."
            )
        return value

    def validate_email(self, value):
        if Utilisateur.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Cette adresse email est déjà utilisée."
            )
        return value

    def validate_telephone(self, value):
        if value and Utilisateur.objects.filter(
            telephone=value
        ).exists():
            raise serializers.ValidationError(
                "Ce numéro de téléphone est déjà utilisé."
            )
        return value

    def validate_nom_complet(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Le nom complet est obligatoire."
            )

        return value

    @staticmethod
    def _split_nom_complet(nom_complet):
        parts = nom_complet.split(" ", 1)

        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        return first_name, last_name

    @staticmethod
    def _generer_username(email):
        import re

        base = email.split("@")[0]
        base = re.sub(r"[^a-zA-Z0-9_]", "", base) or "agent"
        base = base.lower()[:25]

        username = base
        suffix = 0

        while Utilisateur.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base}{suffix}"

        return username

    @transaction.atomic
    def create(self, validated_data):
        """
        Crée le compte utilisateur et le profil Agent associés.

        La transaction garantit que les deux objets sont créés ensemble :
        si la création du profil Agent échoue, le compte Utilisateur
        nouvellement créé est également annulé.
        """
        nom_complet = validated_data.pop("nom_complet")
        email = validated_data.pop("email")
        telephone = validated_data.pop("telephone", None)
        quartier = validated_data.pop("quartier", "")
        password = validated_data.pop("password")

        first_name, last_name = self._split_nom_complet(
            nom_complet
        )

        user = Utilisateur(
            username=self._generer_username(email),
            first_name=first_name,
            last_name=last_name,
            email=email,
            telephone=telephone or None,
            quartier=quartier,
            role=Utilisateur.Role.AGENT,
        )

        user.set_password(password)
        user.save()

        agent = Agent.objects.create(
            utilisateur=user,
            **validated_data,
        )

        return agent



class AgentUpdateSerializer(serializers.Serializer):
    """
    Sérialiseur de modification partielle d'un agent.

    Tous les champs sont facultatifs afin de permettre l'utilisation
    de la méthode HTTP PATCH.

    Les informations personnelles (`nom_complet`, `email`,
    `telephone`) concernent le compte Utilisateur associé.

    Les autres champs concernent directement le profil Agent.
    """

    nom_complet = serializers.CharField(
        max_length=150,
        required=False,
    )

    email = serializers.EmailField(
        required=False,
    )

    telephone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    matricule = serializers.CharField(
        max_length=50,
        required=False,
    )

    departement = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    specialisation = serializers.ChoiceField(
        choices=Agent.TypeIncident.choices,
        required=False,
        allow_null=True,
    )

    disponible = serializers.BooleanField(
        required=False,
    )

    score_satisfaction = serializers.FloatField(
        required=False,
        min_value=0.0,
    )

    taux_completion = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=100.0,
    )

    ponctualite = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=100.0,
    )

    taches_resolues_semaine = serializers.IntegerField(
        required=False,
        min_value=0,
    )

    objectif_hebdo = serializers.IntegerField(
        required=False,
        min_value=0,
    )