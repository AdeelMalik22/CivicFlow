from django.urls import path

from .views import (
    ServiceAreaCreateView,
    ServiceAreaListView,
    ServiceAreaUpdateView,
    TenantCreateView,
    TenantListView,
    TenantMembershipCreateView,
    TenantMembershipListView,
    TenantMembershipUpdateView,
    TenantSwitchView,
    TenantUpdateView,
)

app_name = "tenants"

urlpatterns = [
    path("select/<uuid:public_id>/", TenantSwitchView.as_view(), name="select"),
    path("", TenantListView.as_view(), name="list"),
    path("add/", TenantCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", TenantUpdateView.as_view(), name="edit"),
    path("service-areas/", ServiceAreaListView.as_view(), name="service-area-list"),
    path("service-areas/add/", ServiceAreaCreateView.as_view(), name="service-area-add"),
    path("service-areas/<int:pk>/edit/", ServiceAreaUpdateView.as_view(), name="service-area-edit"),
    path("memberships/", TenantMembershipListView.as_view(), name="membership-list"),
    path("memberships/add/", TenantMembershipCreateView.as_view(), name="membership-add"),
    path(
        "memberships/<int:pk>/edit/",
        TenantMembershipUpdateView.as_view(),
        name="membership-edit",
    ),
]
