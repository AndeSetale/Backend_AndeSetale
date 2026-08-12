from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path("auth/", include("apps.users.urls")),
    path("incidents/", include("apps.incidents.urls")),
] + router.urls
