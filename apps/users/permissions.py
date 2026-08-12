"""
Permissions DRF par rôle pour Andë Sétal.

Hiérarchie des rôles :
  CITOYEN  — peut signaler des incidents et consulter ses propres données
  AGENT    — peut gérer les interventions qui lui sont assignées
  ADMIN    — accès complet (superviseur)
"""

from rest_framework.permissions import BasePermission

from .models import Utilisateur


class IsCitoyen(BasePermission):
    """Autorise uniquement les citoyens authentifiés."""

    message = "Accès réservé aux citoyens."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == Utilisateur.Role.CITOYEN
        )


class IsAgent(BasePermission):
    """Autorise uniquement les agents authentifiés."""

    message = "Accès réservé aux agents."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == Utilisateur.Role.AGENT
        )


class IsAdmin(BasePermission):
    """Autorise uniquement les administrateurs authentifiés."""

    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == Utilisateur.Role.ADMIN
        )


class IsAgentOrAdmin(BasePermission):
    """Autorise les agents ET les administrateurs."""

    message = "Accès réservé aux agents et administrateurs."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (Utilisateur.Role.AGENT, Utilisateur.Role.ADMIN)
        )


class IsCitoyenOrAdmin(BasePermission):
    """Autorise les citoyens ET les administrateurs."""

    message = "Accès réservé aux citoyens et administrateurs."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (Utilisateur.Role.CITOYEN, Utilisateur.Role.ADMIN)
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Permission au niveau objet.
    Autorise uniquement le propriétaire de l'objet ou un administrateur.
    L'objet doit avoir un attribut `signale_par` ou `utilisateur`.
    """

    message = "Vous n'avez pas accès à cette ressource."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == Utilisateur.Role.ADMIN:
            return True
        # Support des deux conventions de nommage
        owner = getattr(obj, "signale_par", None) or getattr(obj, "utilisateur", None)
        return owner == request.user
