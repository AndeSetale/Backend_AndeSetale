from django.urls import path

from .views import IncidentListView, PreuveUploadView

urlpatterns = [
    path("", IncidentListView.as_view(), name="incident-list"),
    path("preuves/upload/", PreuveUploadView.as_view(), name="preuve-upload"),
]
