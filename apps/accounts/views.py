import hashlib
import secrets
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Count, Q, QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from .forms import (
    CitizenRegistrationForm,
    InvitationSetPasswordForm,
    SeparationOfDutiesPolicyForm,
    SignupOTPForm,
    TenantRoleForm,
)
from .models import SeparationOfDutiesPolicy, SignupOTP, StaffInvitation, TenantRole
from .services import InvitationError, accept_staff_invitation


class PlatformStaffRequiredMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self) -> bool:
        return self.request.user.is_authenticated and self.request.user.is_staff


class CitizenRegistrationView(CreateView):
    form_class = CitizenRegistrationForm
    template_name = "registration/signup.html"
    def form_valid(self, form):
        super().form_valid(form)
        code = f"{secrets.randbelow(1000000):06d}"
        SignupOTP.objects.create(
            user=self.object,
            code_hash=hashlib.sha256(code.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        send_mail(
            "CivicFlow verification code",
            f"Your verification code is {code}.",
            None,
            [self.object.email],
        )
        return redirect("signup-verify", user_id=self.object.pk)


class SignupVerifyView(View):
    template_name = "registration/signup_verify.html"

    def get(self, request, user_id):
        return render(request, self.template_name, {"form": SignupOTPForm()})

    def post(self, request, user_id):
        form = SignupOTPForm(request.POST)
        user = get_object_or_404(get_user_model(), pk=user_id, is_active=False)
        otp = SignupOTP.objects.filter(user=user).order_by("-created_at").first()
        if form.is_valid() and otp and otp.verify_code(form.cleaned_data["code"]):
            user.is_active = True
            user.email_verified = True
            user.save(update_fields=("is_active", "email_verified"))
            return redirect("login")
        form.add_error("code", "The code is invalid, expired, or locked.")
        return render(request, self.template_name, {"form": form})


class TenantRoleListView(PlatformStaffRequiredMixin, ListView):
    model = TenantRole
    template_name = "accounts/role_list.html"
    context_object_name = "roles"

    def get_queryset(self) -> QuerySet[TenantRole]:
        return TenantRole.objects.select_related("tenant").annotate(
            member_count=Count("membership_assignments", distinct=True),
            permission_count=Count("grants", distinct=True),
            sensitive_permission_count=Count(
                "grants",
                filter=Q(grants__permission__is_sensitive=True),
                distinct=True,
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["separation_policies"] = SeparationOfDutiesPolicy.objects.select_related(
            "tenant",
            "initiator_permission",
            "approver_permission",
        )
        return context


class RoleFormMixin(PlatformStaffRequiredMixin):
    model = TenantRole
    form_class = TenantRoleForm
    template_name = "accounts/role_form.html"
    success_url = reverse_lazy("accounts:role-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class TenantRoleCreateView(RoleFormMixin, CreateView):
    success_message = "Role created."


class TenantRoleUpdateView(RoleFormMixin, UpdateView):
    success_message = "Role updated."


class SeparationPolicyFormMixin(PlatformStaffRequiredMixin):
    model = SeparationOfDutiesPolicy
    form_class = SeparationOfDutiesPolicyForm
    template_name = "accounts/separation_policy_form.html"
    success_url = reverse_lazy("accounts:role-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class SeparationPolicyCreateView(SeparationPolicyFormMixin, CreateView):
    success_message = "Separation-of-duties policy created."


class SeparationPolicyUpdateView(SeparationPolicyFormMixin, UpdateView):
    success_message = "Separation-of-duties policy updated."


class StaffInvitationAcceptView(View):
    template_name = "accounts/invitation_accept.html"

    def get(self, request, public_id, uidb64, token):
        invitation = self._invitation(public_id, uidb64)
        if not self._is_valid(invitation, token):
            return render(request, self.template_name, {"invalid": True}, status=400)
        form = (
            InvitationSetPasswordForm(invitation.membership.user)
            if not invitation.membership.user.has_usable_password()
            else None
        )
        return render(
            request,
            self.template_name,
            {"invitation": invitation, "form": form},
        )

    def post(self, request, public_id, uidb64, token):
        invitation = self._invitation(public_id, uidb64)
        if not self._is_valid(invitation, token):
            return render(request, self.template_name, {"invalid": True}, status=400)

        user = invitation.membership.user
        form = (
            InvitationSetPasswordForm(user, request.POST)
            if not user.has_usable_password()
            else None
        )
        if form is not None and not form.is_valid():
            return render(
                request,
                self.template_name,
                {"invitation": invitation, "form": form},
            )

        try:
            accept_staff_invitation(
                invitation,
                token=token,
                raw_password=form.cleaned_data["new_password1"] if form else None,
            )
        except InvitationError:
            return render(request, self.template_name, {"invalid": True}, status=400)

        messages.success(request, "Your CivicFlow membership is now active.")
        return redirect(f"{reverse('login')}?next={reverse('workspace')}")

    @staticmethod
    def _invitation(public_id, uidb64) -> StaffInvitation:
        invitation = get_object_or_404(
            StaffInvitation.objects.select_related("membership__user", "membership__tenant"),
            public_id=public_id,
        )
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
        except (ValueError, TypeError, UnicodeDecodeError) as exc:
            raise Http404 from exc
        if str(invitation.membership.user_id) != user_id:
            raise Http404
        return invitation

    @staticmethod
    def _is_valid(invitation: StaffInvitation, token: str) -> bool:
        return (
            invitation.is_pending
            and invitation.membership.status == invitation.membership.Status.INVITED
            and default_token_generator.check_token(invitation.membership.user, token)
        )
