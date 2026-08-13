from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path("auth/", include("apps.users.urls")),
    # Inclusion des URLs des signalements -> /api/signalements/
    path("signalements/", include("apps.incidents.urls")),
] + router.urls