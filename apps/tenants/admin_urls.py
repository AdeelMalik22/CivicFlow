from django.urls import path

from .admin_views import (
    DepartmentCreateView,
    DepartmentUpdateView,
    TenantAdministrationDashboardView,
    TenantMembershipActivateView,
    TenantMembershipCreateView,
    TenantMembershipResendView,
    TenantMembershipSuspendView,
    TenantMembershipUpdateView,
    TenantRoleCreateView,
    TenantRoleUpdateView,
    TenantServiceAreaCreateView,
    TenantServiceAreaUpdateView,
    TenantSettingsUpdateView,
)

app_name = "tenant-admin"

urlpatterns = [
    path("", TenantAdministrationDashboardView.as_view(), name="dashboard"),
    path("settings/", TenantSettingsUpdateView.as_view(), name="settings"),
    path("departments/add/", DepartmentCreateView.as_view(), name="department-add"),
    path(
        "departments/<int:pk>/edit/",
        DepartmentUpdateView.as_view(),
        name="department-edit",
    ),
    path("service-areas/add/", TenantServiceAreaCreateView.as_view(), name="service-area-add"),
    path(
        "service-areas/<int:pk>/edit/",
        TenantServiceAreaUpdateView.as_view(),
        name="service-area-edit",
    ),
    path("members/add/", TenantMembershipCreateView.as_view(), name="membership-add"),
    path(
        "members/<int:pk>/edit/",
        TenantMembershipUpdateView.as_view(),
        name="membership-edit",
    ),
    path(
        "members/<int:pk>/suspend/",
        TenantMembershipSuspendView.as_view(),
        name="membership-suspend",
    ),
    path(
        "members/<int:pk>/activate/",
        TenantMembershipActivateView.as_view(),
        name="membership-activate",
    ),
    path(
        "members/<int:pk>/resend/",
        TenantMembershipResendView.as_view(),
        name="membership-resend",
    ),
    path("roles/add/", TenantRoleCreateView.as_view(), name="role-add"),
    path("roles/<int:pk>/edit/", TenantRoleUpdateView.as_view(), name="role-edit"),
]
