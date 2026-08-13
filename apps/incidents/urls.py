from django.urls import path

from .views import IncidentListView, MesIncidentsView, PreuveUploadView

urlpatterns = [
    path("", IncidentListView.as_view(), name="incident-list"),
    path("my/", MesIncidentsView.as_view(), name="incident-my"),
    path("preuves/upload/", PreuveUploadView.as_view(), name="preuve-upload"),
]
