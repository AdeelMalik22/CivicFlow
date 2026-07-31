from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, DetailView, ListView, TemplateView
from apps.issues.models import Issue
from apps.procurement.models import Tender, Bid
from apps.contractors.models import ContractorApplication
from .forms import ProjectForm
from .models import Project


class HomeView(TemplateView):
    template_name = "home.html"

class HowItWorksView(TemplateView):
    template_name = "how_it_works.html"

class AccountabilityView(TemplateView):
    template_name = "accountability.html"

class ProjectsView(LoginRequiredMixin, ListView):
    template_name = "workspace/projects.html"
    context_object_name = "projects"
    paginate_by = 10

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if tenant is None and self.request.user.is_superuser:
            return Project.objects.all()
        if tenant is None:
            membership = self.request.user.tenant_memberships.active().select_related("tenant").first()
            tenant = membership.tenant if membership else None
        return Project.objects.filter(tenant=tenant).select_related("tenant", "created_by").order_by("-created_at") if tenant else Project.objects.none()


class ProjectCreateView(LoginRequiredMixin, CreateView):
    form_class = ProjectForm
    template_name = "workspace/project_form.html"
    success_url = "/workspace/projects/"

    def form_valid(self, form):
        tenant = getattr(self.request, "tenant", None)
        if tenant is None:
            membership = self.request.user.tenant_memberships.active().select_related("tenant").first()
            tenant = membership.tenant if membership else None
        if tenant is None:
            form.add_error(None, "Select an active organization before creating a project.")
            return self.form_invalid(form)
        form.instance.tenant = tenant
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "workspace/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if tenant is None and self.request.user.is_superuser:
            return Project.objects.select_related("tenant", "created_by")
        if tenant is None:
            membership = self.request.user.tenant_memberships.active().select_related("tenant").first()
            tenant = membership.tenant if membership else None
        return Project.objects.filter(tenant=tenant).select_related("tenant", "created_by") if tenant else Project.objects.none()


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
        context["recent_reports"] = Issue.objects.filter(tenant=tenant).order_by("-created_at")[:3] if tenant else Issue.objects.none()
        context["recent_tenders"] = Tender.objects.order_by("-created_at")[:3]
        context["recent_contractors"] = ContractorApplication.objects.order_by("-created_at")[:3]
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
