from django.urls import path

from .views import ServiceAreaListView, TenantListView, TenantMembershipListView

app_name = "tenants"

urlpatterns = [
    path("", TenantListView.as_view(), name="list"),
    path("service-areas/", ServiceAreaListView.as_view(), name="service-area-list"),
    path("memberships/", TenantMembershipListView.as_view(), name="membership-list"),
]
