from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView, ListView

from .forms import ContractorApplicationForm, ContractorReviewForm
from .models import ContractorApplication


class ContractorApplyView(LoginRequiredMixin, CreateView):
    form_class = ContractorApplicationForm
    template_name = "contractors/apply.html"
    success_url = reverse_lazy("contractors:mine")
    def form_valid(self, form):
        form.instance.applicant = self.request.user
        return super().form_valid(form)

class MyContractorApplicationsView(LoginRequiredMixin, ListView):
    model = ContractorApplication
    template_name = "contractors/mine.html"
    context_object_name = "applications"
    def get_queryset(self):
        return ContractorApplication.objects.filter(applicant=self.request.user)


class ContractorReviewListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "contractors/review_list.html"
    context_object_name = "applications"
    def test_func(self): return self.request.user.is_staff
    def get_queryset(self): return ContractorApplication.objects.exclude(status=ContractorApplication.Status.APPROVED)


class ContractorReviewView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_staff
    def post(self, request, pk, action):
        application = get_object_or_404(ContractorApplication, pk=pk)
        form = ContractorReviewForm(request.POST)
        if form.is_valid() and action in {"approve", "reject", "info"}:
            application.reviewed_by = request.user
            application.review_reason = form.cleaned_data["reason"]
            application.status = {"approve": "approved", "reject": "rejected", "info": "info_requested"}[action]
            application.save(update_fields=("status", "review_reason", "reviewed_by", "updated_at"))
            messages.success(request, "Contractor application updated.")
        return redirect("contractors:review")
