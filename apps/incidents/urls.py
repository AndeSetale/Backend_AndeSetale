from django.urls import path

from .views import PreuveDestroyView, PreuveListCreateView

urlpatterns = [
    path(
        "<int:incident_id>/preuves/",
        PreuveListCreateView.as_view(),
        name="incident-preuves-list-create",
    ),
    path(
        "<int:incident_id>/preuves/<int:preuve_id>/",
        PreuveDestroyView.as_view(),
        name="incident-preuve-destroy",
    ),
]
