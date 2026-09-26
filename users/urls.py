from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    AccountView,
    EmailVerificationView,
    ProfileUpdateView,
    RegisterView,
    ResendVerificationView,
    ResumeVerificationView,
    UserLoginView,
)

app_name = "users"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("account/", AccountView.as_view(), name="account"),
    path("settings/", ProfileUpdateView.as_view(), name="profile_settings"),
    path("verify-email/", EmailVerificationView.as_view(), name="verify_email"),
    path(
        "verify-email/resend/",
        ResendVerificationView.as_view(),
        name="resend_verification",
    ),
    path(
        "verify-email/resume/",
        ResumeVerificationView.as_view(),
        name="resume_verification",
    ),
]
