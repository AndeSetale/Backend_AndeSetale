from django.urls import path

from .views import DashboardStatsView, AgentDashboardView

urlpatterns = [
    # Dashboard superviseur/admin existant
    path("stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    # Dashboard personnel de l'agent connecté
    path("agent/", AgentDashboardView.as_view(), name="dashboard-agent",),
]
