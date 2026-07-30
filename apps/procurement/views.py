from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from .forms import TenderForm, BidForm, AwardForm
from .models import Tender, Bid, Award, ProcurementAuditEvent
from apps.contractors.access import can_submit_bids

class TenderListView(ListView):
    model = Tender
    template_name = "procurement/tenders.html"
    context_object_name = "tenders"
    def get_queryset(self): return Tender.objects.filter(published=True).order_by("deadline")

class TenderCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = TenderForm
    template_name = "procurement/tender_form.html"
    success_url = reverse_lazy("procurement:tenders")
    def test_func(self): return self.request.user.is_staff
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        tenant = getattr(self.request, "tenant", None)
        if tenant:
            form.fields["department"].queryset = form.fields["department"].queryset.filter(tenant=tenant)
            form.fields["service_area"].queryset = form.fields["service_area"].queryset.filter(tenant=tenant, is_active=True)
        return form
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        ProcurementAuditEvent.objects.create(tender=self.object, actor=self.request.user, action="published" if self.object.published else "draft_created", note="Tender created")
        return response

class BidCreateView(LoginRequiredMixin, CreateView):
    form_class = BidForm
    template_name = "procurement/bid_form.html"
    success_url = reverse_lazy("procurement:tenders")
    def dispatch(self, request, *args, **kwargs):
        self.tender = get_object_or_404(Tender, pk=kwargs["pk"], published=True)
        already_bid = Bid.objects.filter(tender=self.tender, contractor=request.user).exists()
        if not can_submit_bids(request.user) or not self.tender.open_for_bids or already_bid:
            messages.error(request, "You are not eligible to bid on this tender.")
            return redirect("procurement:tenders")
        return super().dispatch(request, *args, **kwargs)
    def form_valid(self, form):
        form.instance.tender = self.tender; form.instance.contractor = self.request.user
        response = super().form_valid(form); return redirect("procurement:tenders")

class AwardCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = AwardForm
    template_name = "procurement/award_form.html"
    success_url = reverse_lazy("procurement:tenders")
    def test_func(self): return self.request.user.is_staff
    def dispatch(self, request, *args, **kwargs):
        self.tender = get_object_or_404(Tender, pk=kwargs["pk"])
        if hasattr(self.tender, "award"):
            return redirect("procurement:tenders")
        return super().dispatch(request, *args, **kwargs)
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["winning_bid"].queryset = Bid.objects.filter(tender=self.tender).select_related("contractor")
        return form
    def form_valid(self, form):
        form.instance.tender = self.tender
        form.instance.awarded_by = self.request.user
        self.tender.published = False
        self.tender.save(update_fields=("published",))
        response = super().form_valid(form)
        ProcurementAuditEvent.objects.create(tender=self.tender, actor=self.request.user, action="award_finalized", note=form.instance.decision_note)
        send_mail("Tender award notification", f"Your bid for {self.tender.reference} was selected.", None, [form.instance.winning_bid.contractor.email], fail_silently=True)
        return response

class TenderAuditView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "procurement/audit.html"
    context_object_name = "events"
    def test_func(self): return self.request.user.is_staff
    def get_queryset(self):
        tender = get_object_or_404(Tender, pk=self.kwargs["pk"])
        return tender.audit_events.select_related("actor")

class AuditActivityView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "procurement/audit_activity.html"
    context_object_name = "events"
    def test_func(self): return self.request.user.is_staff
    def get_queryset(self): return ProcurementAuditEvent.objects.select_related("actor", "tender")
