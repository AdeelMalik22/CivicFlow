from django.urls import path

from .views import CitizenRegistrationView

urlpatterns = [path("", CitizenRegistrationView.as_view(), name="signup")]
