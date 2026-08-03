from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import FormView, ListView, TemplateView
from apps.tenants.models import ServiceArea

from .forms import IssueReportForm, PublicTrackingForm
from .models import Issue
from .services import submit_issue


class IssueReportView(LoginRequiredMixin, FormView):
    template_name = "issues/report_form.html"
    form_class = IssueReportForm
    login_url = "login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        areas = ServiceArea.objects.active()
        context["service_area_bounds"] = {
            str(area.pk): list(area.boundary.extent) for area in areas if area.boundary
        }
        context.update(
            {
                "eyebrow": "Citizen reporting",
                "form_title": "Report an infrastructure issue",
                "form_intro": (
                    "Tell the responsible public team what needs attention. "
                    "It takes a few minutes."
                ),
            }
        )
        return context

    def form_valid(self, form):
        issue, token = submit_issue(form, request=self.request)
        return redirect("issues:submitted", reference=issue.reference, token=token)


class IssueSubmittedView(TemplateView):
    template_name = "issues/submitted.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["issue"] = get_object_or_404(Issue, reference=kwargs["reference"])
        if not context["issue"].check_tracking_token(kwargs["token"]):
            raise Http404
        context["tracking_url"] = reverse(
            "issues:track",
            kwargs={"reference": kwargs["reference"], "token": kwargs["token"]},
        )
        context["verification_code"] = kwargs["token"]
        return context


class PublicTrackingLookupView(FormView):
    template_name = "issues/track_lookup.html"
    form_class = PublicTrackingForm

    def form_valid(self, form):
        issue = Issue.objects.filter(reference=form.cleaned_data["reference"]).first()
        if issue is None or not issue.check_tracking_token(
            form.cleaned_data["verification_code"]
        ):
            form.add_error(
                None,
                "We could not verify that reference and code. Check both and try again.",
            )
            return self.form_invalid(form)
        return redirect(
            "issues:track",
            reference=issue.reference,
            token=form.cleaned_data["verification_code"],
        )


class PublicIssueTrackingView(TemplateView):
    template_name = "issues/track_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        issue = (
            Issue.objects.select_related("service_area")
            .prefetch_related("status_events")
            .filter(reference=kwargs["reference"].upper())
            .first()
        )
        owns_issue = (
            self.request.user.is_authenticated
            and issue
            and issue.reporter_id == self.request.user.id
        )
        if issue is None or (not owns_issue and not issue.check_tracking_token(kwargs["token"])):
            raise Http404
        context["issue"] = issue
        context["events"] = issue.status_events.all()
        return context


class MyIssueListView(LoginRequiredMixin, ListView):
    template_name = "issues/my_reports.html"
    context_object_name = "issues"
    login_url = "login"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return redirect("issues:reports")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Issue.objects.filter(reporter=self.request.user).select_related("service_area", "tenant").order_by("-created_at")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(reference__icontains=query) | queryset.filter(description__icontains=query)
        if category := self.request.GET.get("category"):
            queryset = queryset.filter(category=category)
        if status := self.request.GET.get("status"):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Issue.Category.choices
        context["statuses"] = Issue.Status.choices
        context["total_reports"] = Issue.objects.filter(reporter=self.request.user).count()
        context["open_reports"] = Issue.objects.filter(reporter=self.request.user).exclude(
            status__in=(Issue.Status.CLOSED, Issue.Status.REJECTED, Issue.Status.DUPLICATE)
        ).count()
        return context


class IssueOperationsListView(LoginRequiredMixin, ListView):
    template_name = "issues/reports.html"
    context_object_name = "issues"
    paginate_by = 10
    def get_queryset(self):
        queryset = Issue.objects.select_related("service_area", "tenant").order_by("-created_at")
        tenant = getattr(self.request, "tenant", None)
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(reference__icontains=query) | queryset.filter(description__icontains=query)
        if category := self.request.GET.get("category"):
            queryset = queryset.filter(category=category)
        if status := self.request.GET.get("status"):
            queryset = queryset.filter(status=status)
        if area := self.request.GET.get("area"):
            queryset = queryset.filter(service_area_id=area)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Issue.Category.choices
        context["statuses"] = Issue.Status.choices
        context["service_areas"] = self.get_queryset().model.service_area.field.related_model.objects.filter(tenant=self.request.tenant, is_active=True) if getattr(self.request, "tenant", None) else []
        return context
