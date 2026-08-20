from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .otp_utils import can_resend_otp, create_and_send_otp
from .serializers import (
    AgentCreateSerializer,
    AgentSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    ResendOtpSerializer,
    UtilisateurSerializer,
    VerifyEmailSerializer,
)
from .models import Agent


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
    description="Retourne ou met à jour le profil de l'utilisateur authentifié.",
    tags=["Auth"],
)
class MeView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/auth/me/ — Profil de l'utilisateur connecté.
    PATCH /api/auth/me/ — Mise à jour partielle (first_name, last_name, telephone, quartier).
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = UtilisateurSerializer
    http_method_names = ["get", "patch", "head", "options"]

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



class IsAdmin(BasePermission):
    """Autorise uniquement les administrateurs."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )



@extend_schema(
    responses=AgentSerializer,
    description="Liste des agents.",
    tags=["Agents"],
)
class AgentListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAdmin,)

    def get_queryset(self):
        return Agent.objects.select_related("utilisateur").all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AgentCreateSerializer
        return AgentSerializer


@extend_schema(
    responses=AgentSerializer,
    description="Détail, modification ou suppression d'un agent.",
    tags=["Agents"],
)
class AgentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAdmin,)
    queryset = Agent.objects.select_related("utilisateur")
    serializer_class = AgentSerializer