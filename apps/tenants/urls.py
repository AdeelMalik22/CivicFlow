from django.urls import path

from .views import ServiceAreaListView, TenantListView

app_name = "tenants"

urlpatterns = [
    path("", TenantListView.as_view(), name="list"),
    path("service-areas/", ServiceAreaListView.as_view(), name="service-area-list"),
]
