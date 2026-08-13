from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UtilisateurSerializer,
)


@extend_schema(
    request=RegisterSerializer,
    responses={201: UtilisateurSerializer},
    description="Inscription d'un nouvel utilisateur. Crée automatiquement le profil selon le rôle choisi.",
    tags=["Auth"],
)
class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — Inscription avec création du profil selon le rôle."""

    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Inscription réussie.",
                "user": UtilisateurSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    request=CustomTokenObtainPairSerializer,
    description="Connexion — retourne access token, refresh token et infos utilisateur.",
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
