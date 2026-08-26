import re

from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Agent, Administrateur, Citoyen, OTP, Utilisateur

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UtilisateurSerializer(serializers.ModelSerializer):
    """Sérialisation publique d'un utilisateur (lecture)."""

    class Meta:
        model = Utilisateur
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "telephone",
            "quartier",
            "photo_profil",
            "email_verifie",
            "date_joined",
        )
        read_only_fields = ("id", "email_verifie", "date_joined")


# ---------------------------------------------------------------------------
# Inscription — contrat exact attendu par la maquette Angular
# ---------------------------------------------------------------------------

class RegisterSerializer(serializers.Serializer):
    """
    Inscription d'un nouvel utilisateur — CONTRAT MAQUETTE :
    nom_complet, email_ou_telephone, quartier, password,
    accepte_conditions, recevoir_alertes.

    Le rôle est TOUJOURS "citoyen" à l'inscription publique (un agent/admin
    est créé par un administrateur, jamais par auto-inscription).
    """

    nom_complet = serializers.CharField(max_length=150)
    email_ou_telephone = serializers.CharField(max_length=150)
    quartier = serializers.CharField(max_length=100, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    accepte_conditions = serializers.BooleanField()
    recevoir_alertes = serializers.BooleanField(required=False, default=True)

    def validate_accepte_conditions(self, value):
        if not value:
            raise serializers.ValidationError(
                "Vous devez accepter les conditions d'utilisation."
            )
        return value

    def validate_email_ou_telephone(self, value):
        is_email = bool(EMAIL_REGEX.match(value))
        if is_email:
            if Utilisateur.objects.filter(email__iexact=value).exists():
                raise serializers.ValidationError(
                    "Cette adresse email est déjà utilisée."
                )
        else:
            if Utilisateur.objects.filter(telephone=value).exists():
                raise serializers.ValidationError(
                    "Ce numéro de téléphone est déjà utilisé."
                )
        return value

    @staticmethod
    def _generer_username(base):
        """Génère un username unique à partir d'un email ou téléphone."""
        base = re.sub(r"[^a-zA-Z0-9_]", "", base.split("@")[0]) or "user"
        base = base.lower()[:25]
        username = base
        suffix = 0
        while Utilisateur.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base}{suffix}"
        return username

    def create(self, validated_data):
        nom_complet = validated_data["nom_complet"].strip()
        identifiant = validated_data["email_ou_telephone"].strip()
        is_email = bool(EMAIL_REGEX.match(identifiant))

        parts = nom_complet.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        user = Utilisateur(
            username=self._generer_username(identifiant),
            first_name=first_name,
            last_name=last_name,
            email=identifiant if is_email else "",
            telephone=None if is_email else identifiant,
            quartier=validated_data.get("quartier", ""),
            role=Utilisateur.Role.CITOYEN,
        )
        user.set_password(validated_data["password"])
        user.save()

        Citoyen.objects.create(utilisateur=user)

        # TODO (recevoir_alertes) : stocker la préférence quand le modèle
        # de préférences de notification existera côté app `notifications`.

        return user


# ---------------------------------------------------------------------------
# Connexion — email OU téléphone dans un champ unique `identifiant`
# ---------------------------------------------------------------------------

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    JWT — connexion avec un identifiant unique.

    L'utilisateur peut se connecter avec :
    - son email ;
    - son numéro de téléphone ;
    - son username.

    Le champ envoyé par le frontend reste toujours :
        {
            "identifiant": "...",
            "password": "..."
        }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # SimpleJWT attend normalement "username".
        # On le remplace uniquement dans le formulaire exposé
        # au frontend par notre champ "identifiant".
        #
        # IMPORTANT :
        # self.username_field reste "username" pour que
        # SimpleJWT puisse ensuite appeler authenticate().
        self.fields.pop(self.username_field, None)
        self.fields["identifiant"] = serializers.CharField()

    def validate(self, attrs):
        # ------------------------------------------------------
        # 1. RÉCUPÉRATION DE L'IDENTIFIANT
        # ------------------------------------------------------

        identifiant = attrs.pop("identifiant", "").strip()

        if not identifiant:
            raise serializers.ValidationError(
                {"detail": "L'identifiant est obligatoire."}
            )

        # ------------------------------------------------------
        # 2. RECHERCHE DE L'UTILISATEUR
        # ------------------------------------------------------

        # Si l'identifiant ressemble à un email,
        # on recherche par email.
        if EMAIL_REGEX.match(identifiant):
            lookup = {"email__iexact": identifiant}

        # Si c'est un numéro de téléphone,
        # on recherche par téléphone.
        elif identifiant.startswith("+") or identifiant.isdigit():
            lookup = {"telephone": identifiant}

        # Sinon, on considère que c'est le username.
        # Exemple : "agent001"
        else:
            lookup = {"username": identifiant}

        try:
            user = Utilisateur.objects.get(**lookup)
        except Utilisateur.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Identifiants invalides."}
            )

        # ------------------------------------------------------
        # 3. VÉRIFICATION DU MOT DE PASSE
        # ------------------------------------------------------

        password = attrs.get("password")

        if not user.check_password(password):
            raise serializers.ValidationError(
                {"detail": "Identifiants invalides."}
            )

        # ------------------------------------------------------
        # 4. PRÉPARATION POUR SIMPLEJWT
        # ------------------------------------------------------

        # SimpleJWT utilise toujours la clé "username"
        # pour appeler authenticate().
        #
        # On lui transmet donc le vrai username du compte.
        attrs[self.username_field] = user.get_username()

        # La validation standard de SimpleJWT génère
        # les tokens access + refresh.
        data = super().validate(attrs)

        # ------------------------------------------------------
        # 5. INFORMATIONS UTILISATEUR DANS LA RÉPONSE
        # ------------------------------------------------------

        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": self.user.role,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }

        return data


# ---------------------------------------------------------------------------
# OTP — vérification email + renvoi de code
# ---------------------------------------------------------------------------

class VerifyEmailSerializer(serializers.Serializer):
    """POST /api/auth/verify-email/ — email + code → email_verifie = True."""

    email = serializers.EmailField()
    code = serializers.CharField(max_length=10)

    def validate(self, attrs):
        try:
            user = Utilisateur.objects.get(email__iexact=attrs["email"])
        except Utilisateur.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Aucun compte associé à cet email."}
            )

        otp = (
            OTP.objects.filter(utilisateur=user, code=attrs["code"], verifie=False)
            .order_by("-id")
            .first()
        )
        if otp is None or otp.date_expiration < timezone.now():
            raise serializers.ValidationError(
                {"detail": "Code invalide ou expiré."}
            )

        attrs["user"] = user
        attrs["otp"] = otp
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        otp = self.validated_data["otp"]
        otp.verifie = True
        otp.save(update_fields=["verifie"])
        user.email_verifie = True
        user.save(update_fields=["email_verifie"])
        return user


class ResendOtpSerializer(serializers.Serializer):
    """POST /api/auth/resend-otp/ — redemande un code OTP."""

    email = serializers.EmailField()

    def validate_email(self, value):
        if not Utilisateur.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Aucun compte associé à cet email."
            )
        return value


class AgentSerializer(serializers.ModelSerializer):
    """Lecture d'un agent avec les informations de son utilisateur."""

    nom_complet = serializers.SerializerMethodField()
    email = serializers.EmailField(source="utilisateur.email", read_only=True)
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
        fields = (
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
        )

    def get_nom_complet(self, obj):
        return obj.utilisateur.get_full_name()


class AgentCreateSerializer(serializers.Serializer):
    """Création d'un agent et de son utilisateur associé."""

    nom_complet = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    telephone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
    )
    quartier = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )
    
    departement = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    specialisation = serializers.ChoiceField(
        choices=Agent.TypeIncident.choices,
        required=False,
        allow_blank=True,
    )
    disponible = serializers.BooleanField(default=True)

    def validate_email(self, value):
        if Utilisateur.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Cette adresse email est déjà utilisée."
            )
        return value

    def create(self, validated_data):
        nom_complet = validated_data.pop("nom_complet").strip()
        password = validated_data.pop("password")

        parts = nom_complet.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        email = validated_data.pop("email")
        telephone = validated_data.pop("telephone", "")
        quartier = validated_data.pop("quartier", "")

        username = RegisterSerializer._generer_username(email)

        # Création de l'utilisateur
        user = Utilisateur(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            telephone=telephone,
            quartier=quartier,
            role=Utilisateur.Role.AGENT,
        )

        user.set_password(password)
        user.save()

        # Génération automatique de la matricule
        dernier_agent = Agent.objects.order_by("-id").first()

        if dernier_agent:
            dernier_numero = int(
                dernier_agent.matricule.replace("AG", "")
            )
            numero = dernier_numero + 1
        else:
            numero = 1

        matricule = f"AG{numero:03d}"

        # Création de l'agent
        return Agent.objects.create(
            utilisateur=user,
            matricule=matricule,
            **validated_data,
        )

