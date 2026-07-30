from django import forms
from django.contrib.auth import get_user_model
from django.contrib.gis.forms import OSMWidget

from apps.accounts.models import MembershipRole, TenantRole

from .models import Department, ServiceArea, Tenant, TenantMembership

User = get_user_model()


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ("name", "slug", "status", "timezone", "default_language", "contact_email")
        widgets = {
            "name": forms.TextInput(
                attrs={"autocomplete": "organization", "placeholder": "City Services Authority"}
            ),
            "slug": forms.TextInput(
                attrs={"placeholder": "city-services-authority", "spellcheck": "false"}
            ),
            "timezone": forms.TextInput(
                attrs={"placeholder": "Asia/Karachi", "spellcheck": "false"}
            ),
            "default_language": forms.TextInput(attrs={"placeholder": "en", "spellcheck": "false"}),
            "contact_email": forms.EmailInput(
                attrs={"autocomplete": "email", "placeholder": "contact@example.gov"}
            ),
        }
        help_texts = {
            "name": "The official public name of the government organization.",
            "default_language": "BCP 47 language code used for tenant defaults, such as en.",
            "contact_email": "Operational contact address; it is not displayed publicly.",
        }


class TenantSettingsForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ("name", "timezone", "default_language", "contact_email")
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "organization"}),
            "timezone": forms.TextInput(attrs={"placeholder": "Asia/Karachi"}),
            "default_language": forms.TextInput(attrs={"placeholder": "en"}),
            "contact_email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ("name", "code", "description", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Roads and maintenance"}),
            "code": forms.TextInput(attrs={"placeholder": "ROADS", "spellcheck": "false"}),
            "description": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Describe this department's responsibility."}
            ),
        }


class ServiceAreaForm(forms.ModelForm):
    class Meta:
        model = ServiceArea
        fields = ("tenant", "name", "code", "description", "boundary", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Central district"}),
            "code": forms.TextInput(attrs={"placeholder": "CENTRAL-01", "spellcheck": "false"}),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Describe the coverage and any routing notes.",
                }
            ),
            "boundary": OSMWidget(
                attrs={
                    "map_width": 800,
                    "map_height": 460,
                    "default_lon": 67.0011,
                    "default_lat": 24.8607,
                    "default_zoom": 10,
                }
            ),
        }
        help_texts = {
            "tenant": "The organization that owns and uses this boundary.",
            "boundary": "Use the map tools to draw one or more supported polygons.",
            "is_active": "Only active boundaries are considered when routing reports.",
        }


class TenantMembershipForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        queryset=TenantRole.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Assign one or more tenant-scoped roles.",
    )
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={"autocomplete": "email", "placeholder": "officer@example.gov"}
        ),
        help_text="We will connect an existing account or prepare a new invited account.",
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": "Aisha"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "family-name", "placeholder": "Khan"}),
    )

    class Meta:
        model = TenantMembership
        fields = ("tenant", "department")
        help_texts = {
            "tenant": "The organization this account may access.",
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        tenant_field = self.fields["tenant"]
        tenant_field.queryset = Tenant.objects.order_by("name")
        self.no_organizations = not tenant_field.queryset.exists()
        tenant_field.empty_label = (
            "Select an organization"
            if not self.no_organizations
            else "No organizations available — create one first"
        )
        if self.no_organizations:
            tenant_field.disabled = True

        if self.instance.pk:
            tenant_field.disabled = True
            self.fields["email"].initial = self.instance.user.email
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].disabled = True

        department_field = self.fields["department"]
        department_field.queryset = Department.objects.filter(is_active=True).order_by("name")
        department_field.empty_label = "Select a department"
        if tenant_id := (self.instance.tenant_id if self.instance.pk else self.data.get("tenant")):
            department_field.queryset = department_field.queryset.filter(tenant_id=tenant_id)
        if self.instance.pk:
            department_field.initial = self.instance.department_id
            department_field.disabled = True

        tenant_id = self.instance.tenant_id if self.instance.pk else self.data.get("tenant")
        if tenant_id:
            self.fields["roles"].queryset = TenantRole.objects.filter(
                tenant_id=tenant_id,
                is_active=True,
            )
        if self.instance.pk:
            self.fields["roles"].initial = TenantRole.objects.filter(
                membership_assignments__membership=self.instance
            )

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()
        if self.instance.pk:
            return self.instance.user.email
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        tenant = cleaned_data.get("tenant")
        department = cleaned_data.get("department")
        if department and tenant and department.tenant_id != tenant.id:
            self.add_error("department", "Select a department in the selected organization.")
        if not self.instance.pk and email and tenant:
            existing_user = User.objects.filter(email__iexact=email).first()
            if existing_user and TenantMembership.objects.filter(
                tenant=tenant,
                user=existing_user,
            ).exists():
                self.add_error(
                    "email",
                    "This account already has a membership in the selected organization.",
                )
        return cleaned_data

    def save(self, commit: bool = True) -> TenantMembership:
        membership = super().save(commit=False)
        if not membership.user_id:
            user, created = User.objects.get_or_create(
                email__iexact=self.cleaned_data["email"],
                defaults={
                    "email": self.cleaned_data["email"],
                    "first_name": self.cleaned_data.get("first_name", "").strip(),
                    "last_name": self.cleaned_data.get("last_name", "").strip(),
                },
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=("password",))
            membership.user = user
        else:
            user = membership.user
            user.first_name = self.cleaned_data.get("first_name", "").strip()
            user.last_name = self.cleaned_data.get("last_name", "").strip()
            if commit:
                user.save(update_fields=("first_name", "last_name"))

        if commit:
            membership.save()
            selected_roles = self.cleaned_data["roles"]
            MembershipRole.objects.filter(membership=membership).exclude(
                role__in=selected_roles
            ).delete()
            for role in selected_roles:
                MembershipRole.objects.get_or_create(
                    membership=membership,
                    role=role,
                    defaults={"assigned_by": getattr(self, "assigned_by", None)},
                )
            self.save_m2m()
        return membership
