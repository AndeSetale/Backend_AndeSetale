from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, UtilisateurSerializer


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Inscription d'un nouvel utilisateur avec création du profil selon son rôle.
    """

    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "Inscription réussie.",
                    "user": UtilisateurSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Retourne access + refresh token JWT enrichis des infos utilisateur.
    """

    permission_classes = (AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    """
    GET /api/auth/me/
    Retourne le profil de l'utilisateur connecté.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = UtilisateurSerializer(request.user)
        return Response(serializer.data)
