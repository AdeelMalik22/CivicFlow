from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "home.html"


class WorkspaceView(LoginRequiredMixin, TemplateView):
    """Authenticated starting point until role-specific modules are delivered."""

    template_name = "workspace/home.html"


@require_GET
@never_cache
def liveness(request):
    """Confirm that the Django process can serve requests."""
    return JsonResponse({"status": "ok", "service": "civicflow"})


@require_GET
@never_cache
def readiness(request):
    """Confirm that required synchronous dependencies are available."""
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except OperationalError:
        return JsonResponse(
            {"status": "unavailable", "checks": {"database": "failed"}},
            status=503,
        )

    return JsonResponse({"status": "ok", "checks": {"database": "ok"}})
