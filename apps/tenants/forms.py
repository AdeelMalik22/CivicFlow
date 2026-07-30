from django import forms
from django.contrib.auth import get_user_model
from django.contrib.gis.forms import OSMWidget

from .models import ServiceArea, Tenant, TenantMembership

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
    class Meta:
        model = TenantMembership
        fields = ("tenant", "user", "status")
        help_texts = {
            "tenant": "The organization this account may access.",
            "user": "Select an existing CivicFlow account.",
            "status": "Roles and department permissions are assigned separately.",
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["tenant"].queryset = Tenant.objects.order_by("name")
        self.fields["user"].queryset = User.objects.order_by("email")
