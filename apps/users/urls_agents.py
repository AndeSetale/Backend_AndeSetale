from django.urls import path

from .views import AgentDetailView, AgentListCreateView, AgentMeView

urlpatterns = [
    path("", AgentListCreateView.as_view(), name="agents-list-create"),
    path("me/", AgentMeView.as_view(), name="agent-me"),
    path("<int:pk>/", AgentDetailView.as_view(), name="agent-detail"),
]
