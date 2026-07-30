"""
URL configuration for civicflow project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.common.views import HomeView, WorkspaceView, liveness, readiness

admin.site.site_header = "CivicFlow administration"
admin.site.site_title = "CivicFlow admin"
admin.site.index_title = "Platform configuration"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("workspace/", WorkspaceView.as_view(), name="workspace"),
    path(
        "workspace/organizations/",
        include("apps.tenants.urls"),
    ),
    path("workspace/access/", include("apps.accounts.urls")),
    path("workspace/administration/", include("apps.tenants.admin_urls")),
    path("", include("apps.issues.urls")),
    path("contractors/", include("apps.contractors.urls")),
    path("procurement/", include("apps.procurement.urls")),
    path(
        "sign-in/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("sign-up/", include("apps.accounts.signup_urls")),
    path("signup/", include("apps.accounts.signup_urls")),
    path(
        "sign-out/",
        auth_views.LogoutView.as_view(next_page="home"),
        name="logout",
    ),
    path("admin/", admin.site.urls),
    path("health/live/", liveness, name="health-live"),
    path("health/ready/", readiness, name="health-ready"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]
