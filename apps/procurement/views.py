from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import TenderForm, BidForm
from .models import Tender, Bid
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
    def form_valid(self, form): form.instance.created_by = self.request.user; return super().form_valid(form)

class BidCreateView(LoginRequiredMixin, CreateView):
    form_class = BidForm
    template_name = "procurement/bid_form.html"
    def dispatch(self, request, *args, **kwargs):
        self.tender = get_object_or_404(Tender, pk=kwargs["pk"], published=True)
        if not can_submit_bids(request.user) or not self.tender.open_for_bids:
            messages.error(request, "You are not eligible to bid on this tender.")
            return redirect("procurement:tenders")
        return super().dispatch(request, *args, **kwargs)
    def form_valid(self, form):
        form.instance.tender = self.tender; form.instance.contractor = self.request.user
        response = super().form_valid(form); return redirect("procurement:tenders")
