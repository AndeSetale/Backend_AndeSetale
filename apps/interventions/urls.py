from django.urls import path

from .views import InterventionDetailView, InterventionListView

urlpatterns = [
    path("", InterventionListView.as_view(), name="intervention-list"),
    path("<int:pk>/", InterventionDetailView.as_view(), name="intervention-detail"),
]
