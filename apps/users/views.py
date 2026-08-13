from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .otp_utils import can_resend_otp, create_and_send_otp
from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    ResendOtpSerializer,
    UtilisateurSerializer,
    VerifyEmailSerializer,
)


@extend_schema(
    request=RegisterSerializer,
    responses={201: UtilisateurSerializer},
    description=(
        "Inscription d'un citoyen. Contrat : nom_complet, email_ou_telephone, "
        "quartier, password, accepte_conditions, recevoir_alertes. "
        "Envoie automatiquement un code OTP par email si un email est fourni."
    ),
    tags=["Auth"],
)
class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — Inscription citoyen conforme à la maquette."""

    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.email:
            create_and_send_otp(user)

        return Response(
            {
                "message": "Inscription réussie. Vérifiez votre email pour activer votre compte.",
                "user": UtilisateurSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    request=CustomTokenObtainPairSerializer,
    description="Connexion via `identifiant` (email ou téléphone) + password.",
    tags=["Auth"],
)
class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — Retourne access + refresh token JWT."""

    permission_classes = (AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    responses={200: UtilisateurSerializer},
    description="Retourne le profil complet de l'utilisateur authentifié.",
    tags=["Auth"],
)
class MeView(generics.RetrieveAPIView):
    """GET /api/auth/me/ — Profil de l'utilisateur connecté."""

    permission_classes = (IsAuthenticated,)
    serializer_class = UtilisateurSerializer

    def get_object(self):
        return self.request.user


@extend_schema(
    request=VerifyEmailSerializer,
    description="Vérifie le code OTP reçu par email et active email_verifie.",
    tags=["Auth"],
)
class VerifyEmailView(APIView):
    """POST /api/auth/verify-email/ — { email, code } → email vérifié."""

    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Email vérifié avec succès.", "email_verifie": True},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    request=ResendOtpSerializer,
    description="Redemande un nouveau code OTP (cooldown 60s, validité 10 min).",
    tags=["Auth"],
)
class ResendOtpView(APIView):
    """POST /api/auth/resend-otp/ — { email } → nouveau code envoyé."""

    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from .models import Utilisateur  # import local pour éviter tout cycle
        user = Utilisateur.objects.get(email__iexact=serializer.validated_data["email"])

        autorise, secondes_restantes = can_resend_otp(user)
        if not autorise:
            return Response(
                {
                    "detail": "Veuillez patienter avant de redemander un code.",
                    "retry_after": secondes_restantes,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        create_and_send_otp(user)
        return Response(
            {"detail": "Nouveau code envoyé.", "expires_in": 600},
            status=status.HTTP_200_OK,
        )
