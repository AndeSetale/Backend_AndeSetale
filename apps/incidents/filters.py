"""
Filtres avancés DjangoFilter pour l'API des signalements.
"""

from django_filters import rest_framework as filters

from .models import Incident


class IncidentFilter(filters.FilterSet):
    """
    Filtre personnalisé pour les signalements :
    - statut (ex: NOUVEAU, EN_COURS, RESOLU)
    - type (ex: DECHETS, CANAUX, VOIRIE)
    - niveau_urgence (ex: CRITIQUE, ELEVE, MODERE, ROUTINE)
    - citoyen (ID du citoyen ayant signalé)
    - quartier (recherche insensible à la casse)
    - date_debut / date_fin (filtrage temporel)
    """

    statut = filters.CharFilter(field_name="statut", lookup_expr="exact")
    type = filters.CharFilter(field_name="type", lookup_expr="exact")
    niveau_urgence = filters.CharFilter(field_name="niveau_urgence", lookup_expr="exact")
    
    # Filtre par citoyen (signale_par)
    citoyen = filters.NumberFilter(field_name="signale_par_id")
    signale_par = filters.NumberFilter(field_name="signale_par_id")
    
    # Filtres texte et dates
    quartier = filters.CharFilter(field_name="quartier", lookup_expr="icontains")
    date_debut = filters.DateTimeFilter(field_name="date_creation", lookup_expr="gte")
    date_fin = filters.DateTimeFilter(field_name="date_creation", lookup_expr="lte")

    class Meta:
        model = Incident
        fields = ["statut", "type", "niveau_urgence", "citoyen", "signale_par", "quartier"]