"""
Routage des URLs pour l'application Incidents.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IncidentViewSet

router = DefaultRouter()
# Enregistrement du ViewSet sur l'endpoint 'signalements'
router.register(r"", IncidentViewSet, basename="signalement")

urlpatterns = [
    path("", include(router.urls)),
]