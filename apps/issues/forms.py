from django import forms
from django.contrib.gis.forms import OSMWidget
from django.core.exceptions import ValidationError

from apps.tenants.models import ServiceArea

from .models import Issue


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleImageInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        cleaned = [single_file_clean(item, initial) for item in files]
        if len(cleaned) > 5:
            raise ValidationError("Attach no more than five images.")
        for uploaded in cleaned:
            content_type = getattr(uploaded, "content_type", "")
            if content_type not in {"image/jpeg", "image/png", "image/webp"}:
                raise ValidationError("Images must be JPEG, PNG, or WebP files.")
            if uploaded.size > 10 * 1024 * 1024:
                raise ValidationError("Each image must be 10 MB or smaller.")
        return cleaned


class IssueReportForm(forms.ModelForm):
    attachments = MultipleImageField(
        required=False,
        label="Photos",
        help_text="Optional. Add up to five JPEG, PNG, or WebP images (10 MB each).",
    )
    class Meta:
        model = Issue
        fields = (
            "service_area",
            "category",
            "description",
            "location",
            "contact_email",
            "contact_preference",
        )
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": (
                        "Tell us what is happening, where it is, and how it affects the community."
                    ),
                }
            ),
            "location": OSMWidget(
                attrs={
                    "map_width": 800,
                    "map_height": 420,
                    "default_lon": 67.0011,
                    "default_lat": 24.8607,
                    "default_zoom": 11,
                }
            ),
            "contact_email": forms.EmailInput(
                attrs={"autocomplete": "email", "placeholder": "you@example.com"}
            ),
        }
        help_texts = {
            "service_area": "Choose the supported area where the issue is located.",
            "location": "Drop the pin as close as possible to the issue.",
            "contact_email": "Optional. Used only if you request email updates.",
            "contact_preference": "Your public report never displays your email address.",
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["service_area"].queryset = ServiceArea.objects.active().select_related("tenant")

    def clean(self):
        cleaned_data = super().clean()
        wants_email = cleaned_data.get("contact_preference") == Issue.ContactPreference.EMAIL
        if wants_email and not cleaned_data.get("contact_email"):
            self.add_error("contact_email", "Enter an email address to receive updates.")
        return cleaned_data


class PublicTrackingForm(forms.Form):
    reference = forms.CharField(
        max_length=24,
        label="Report reference",
        widget=forms.TextInput(attrs={"placeholder": "CF-20260730-AB12CD"}),
    )
    verification_code = forms.CharField(
        max_length=80,
        label="Verification code",
        widget=forms.PasswordInput(
            attrs={"placeholder": "Your private tracking code", "autocomplete": "one-time-code"}
        ),
    )

    def clean_reference(self) -> str:
        return self.cleaned_data["reference"].strip().upper()
