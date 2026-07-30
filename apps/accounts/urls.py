from django.urls import path

from .views import (
    SeparationPolicyCreateView,
    SeparationPolicyUpdateView,
    TenantRoleCreateView,
    TenantRoleListView,
    TenantRoleUpdateView,
)

app_name = "accounts"

urlpatterns = [
    path("roles/", TenantRoleListView.as_view(), name="role-list"),
    path("roles/add/", TenantRoleCreateView.as_view(), name="role-add"),
    path("roles/<int:pk>/edit/", TenantRoleUpdateView.as_view(), name="role-edit"),
    path("policies/add/", SeparationPolicyCreateView.as_view(), name="policy-add"),
    path(
        "policies/<int:pk>/edit/",
        SeparationPolicyUpdateView.as_view(),
        name="policy-edit",
    ),
]
