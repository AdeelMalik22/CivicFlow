from django import forms
from django.contrib.auth.forms import SetPasswordForm

from .models import (
    AccessPermission,
    RolePermission,
    SeparationOfDutiesPolicy,
    TenantRole,
)


class TenantRoleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=AccessPermission.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select only the capabilities this role requires.",
    )

    class Meta:
        model = TenantRole
        fields = (
            "tenant",
            "name",
            "code",
            "description",
            "requires_mfa",
            "is_active",
            "permissions",
        )
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Government Officer"}),
            "code": forms.TextInput(attrs={"placeholder": "officer", "spellcheck": "false"}),
            "description": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Describe this role's responsibility."}
            ),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["permissions"].queryset = AccessPermission.objects.order_by("name")
        if self.instance.pk:
            self.fields["permissions"].initial = self.instance.permissions.all()

    def save(self, commit: bool = True) -> TenantRole:
        role = super().save(commit=commit)
        if commit:
            selected = self.cleaned_data["permissions"]
            RolePermission.objects.filter(role=role).exclude(permission__in=selected).delete()
            for permission in selected:
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=permission,
                    defaults={"scope": permission.default_scope},
                )
        return role


class SeparationOfDutiesPolicyForm(forms.ModelForm):
    class Meta:
        model = SeparationOfDutiesPolicy
        fields = (
            "tenant",
            "name",
            "initiator_permission",
            "approver_permission",
            "is_active",
        )
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Payment maker-checker"}),
        }
        help_texts = {
            "initiator_permission": "The capability used to begin the controlled workflow.",
            "approver_permission": "The capability that cannot approve the same user's work.",
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        queryset = AccessPermission.objects.order_by("name")
        self.fields["initiator_permission"].queryset = queryset
        self.fields["approver_permission"].queryset = queryset.filter(is_sensitive=True)


class InvitationSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Create password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    new_password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
