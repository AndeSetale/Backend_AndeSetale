from django.urls import path

from .agent_views import AgentDetailView, AgentListCreateView


urlpatterns = [
    path("", AgentListCreateView.as_view(), name="agents-list-create"),
    path("<int:pk>/", AgentDetailView.as_view(), name="agent-detail"),
]