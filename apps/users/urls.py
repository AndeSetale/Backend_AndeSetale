from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AgentDetailView,
    AgentListCreateView,
    LoginView,
    MeView,
    RegisterView,
    ResendOtpView,
    VerifyEmailView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path("resend-otp/", ResendOtpView.as_view(), name="auth-resend-otp"),

    path("agents/", AgentListCreateView.as_view(), name="agents-list-create"),
    path("agents/<int:pk>/", AgentDetailView.as_view(), name="agent-detail"),
]

