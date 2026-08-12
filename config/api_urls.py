from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path("auth/", include("apps.users.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("incidents/", include("apps.incidents.urls")),
    path("interventions/", include("apps.interventions.urls")),
    path("notifications/", include("apps.notifications.urls")),
] + router.urls