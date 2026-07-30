from django.urls import path

from .views import CitizenRegistrationView, SignupVerifyView

urlpatterns = [
    path("", CitizenRegistrationView.as_view(), name="signup"),
    path("verify/<int:user_id>/", SignupVerifyView.as_view(), name="signup-verify"),
]
