from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView
from apps.issues.models import Issue
from apps.procurement.models import Tender, Bid
from apps.contractors.models import ContractorApplication


class HomeView(TemplateView):
    template_name = "home.html"


class WorkspaceView(LoginRequiredMixin, TemplateView):
    """Authenticated starting point until role-specific modules are delivered."""

    template_name = "workspace/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["available_memberships"] = (
            self.request.user.tenant_memberships.active().select_related("tenant")
        )
        tenant = self.request.tenant
        context["open_reports_count"] = Issue.objects.filter(tenant=tenant).exclude(status=Issue.Status.CLOSED).count() if tenant else 0
        context["active_tenders_count"] = Tender.objects.filter(published=True).count()
        context["pending_bids_count"] = Bid.objects.filter(tender__published=True).count()
        context["active_contractors_count"] = ContractorApplication.objects.filter(status=ContractorApplication.Status.APPROVED).count()
        return context


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
