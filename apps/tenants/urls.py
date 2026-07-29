from django.urls import path

from .views import TenantListView

app_name = "tenants"

urlpatterns = [
    path("", TenantListView.as_view(), name="list"),
]
