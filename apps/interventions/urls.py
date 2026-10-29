from django.urls import path

from .views import InterventionDetailView, InterventionListView,MesInterventionsView,RapportView

urlpatterns = [
    path("", InterventionListView.as_view(), name="intervention-list"),
    path(
    "my/",
    MesInterventionsView.as_view(),
    name="mes-interventions"
),
path(
    "<int:intervention_id>/rapport/",
    RapportView.as_view(),
    name="intervention-rapport",
),
    path("<int:pk>/", InterventionDetailView.as_view(), name="intervention-detail"),
    
]
