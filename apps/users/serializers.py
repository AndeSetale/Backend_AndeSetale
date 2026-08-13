from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Administrateur, Agent, Citoyen, Utilisateur


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


class RegisterSerializer(serializers.ModelSerializer):
    """Inscription d'un nouvel utilisateur."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password2 = serializers.CharField(write_only=True, required=True, label="Confirmation mot de passe")

    class Meta:
        model = Utilisateur
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password2",
            "role",
            "telephone",
            "quartier",
        )

    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un compte avec cet email existe déjà.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        role = validated_data.get("role", Utilisateur.Role.CITOYEN)

        user = Utilisateur(**validated_data)
        user.set_password(password)
        user.save()

        # Créer le profil étendu selon le rôle
        if role == Utilisateur.Role.CITOYEN:
            Citoyen.objects.create(utilisateur=user)
        elif role == Utilisateur.Role.AGENT:
            # Le matricule sera assigné plus tard par un admin
            Agent.objects.create(utilisateur=user, matricule=f"AGT-{user.id:05d}")
        elif role == Utilisateur.Role.ADMIN:
            Administrateur.objects.create(utilisateur=user)

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT enrichi avec les infos utilisateur dans la réponse."""

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        return data
