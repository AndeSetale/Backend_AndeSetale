"""
Vues API ViewSet pour les signalements.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.users.models import Utilisateur
from apps.users.permissions import IsOwnerOrAdmin

from .filters import IncidentFilter
from .models import Incident
from .serializers import IncidentSerializer


class IncidentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des signalements (Incidents).

    Endpoints générés :
      GET    /api/signalements/          : Liste paginée & filtrée des signalements
      POST   /api/signalements/          : Création d'un signalement par un citoyen
      GET    /api/signalements/{id}/     : Détail d'un signalement
      PUT    /api/signalements/{id}/     : Modification complète (Admin / Propriétaire)
      PATCH  /api/signalements/{id}/     : Modification partielle (Statut, Commentaires)
      DELETE /api/signalements/{id}/     : Suppression d'un signalement
    """

    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = IncidentFilter

    # Champs configurés pour la recherche globale (?search=...)
    search_fields = ["reference", "description", "quartier", "adresse"]

    # Champs autorisés pour le tri (?ordering=-date_creation)
    ordering_fields = ["date_creation", "niveau_urgence", "statut"]
    ordering = ["-date_creation"]

    def get_queryset(self):
        """
        Règle métier d'accès aux données :
        - Les citoyens ne voient que LEURS propres signalements (sauf si un filtre spécifique est appliqué par un admin/agent).
        - Les administrateurs et agents de terrain voient TOUS les signalements.
        - Optimisation de requêtes SQL avec `select_related` et `prefetch_related`.
        """
        user = self.request.user
        queryset = Incident.objects.select_related(
            "signale_par", "assigne_a", "analyse_ia"
        ).prefetch_related("preuves")

        # Si l'utilisateur est un citoyen simple, limiter à ses propres signalements
        if user.is_authenticated and user.role == Utilisateur.Role.CITOYEN:
            return queryset.filter(signale_par=user)

        return queryset

    def perform_create(self, serializer):
        """
        Assigne automatiquement l'utilisateur connecté comme auteur du signalement.
        """
        serializer.save(signale_par=self.request.user)

    def get_permissions(self):
        """
        Permissions dynamiques selon l'action effectuée.
        - Création : réservée aux citoyens ou admins authentifiés.
        - Modification / Suppression : réservée au propriétaire du signalement ou admin.
        """
        if self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()