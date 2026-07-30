from django.urls import path
from .views import AccountSettingsView, ProfileView
urlpatterns = [path("", ProfileView.as_view(), name="profile"), path("settings/", AccountSettingsView.as_view(), name="settings")]
