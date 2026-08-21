from django.urls import path

from .views import DashboardStatsView, AgentDashboardView, IncidentsCarte

urlpatterns = [
    # Dashboard superviseur/admin existant
    path("stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    # Dashboard personnel de l'agent connecté
    path("agent/", AgentDashboardView.as_view(), name="dashboard-agent"),
    # Incidents géolocalisés pour la carte admin
    path("incidents-carte/", IncidentsCarte.as_view(), name="dashboard-incidents-carte"),
]

