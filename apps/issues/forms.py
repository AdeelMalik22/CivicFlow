from django import forms
from django.contrib.gis.forms import OSMWidget
from django.core.exceptions import ValidationError
import re

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
            "contact_email": (
                "Pre-filled from your account; used only if you request email updates."
            ),
            "contact_preference": "Your public report never displays your email address.",
        }

    def __init__(self, *args, **kwargs) -> None:
        user = kwargs.pop("user", None)
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["service_area"].queryset = ServiceArea.objects.active().select_related("tenant")
        if user is not None and getattr(user, "is_authenticated", False):
            self.fields["contact_email"].initial = user.email

    def clean(self):
        cleaned_data = super().clean()
        service_area = cleaned_data.get("service_area")
        location = cleaned_data.get("location")
        if self.data.get("service_area") and not service_area:
            self.add_error("service_area", "Select an active service area.")
        outside = False
        raw_location = self.data.get("location", "")
        coordinates = re.search(r"POINT\s*\(\s*([\d.-]+)\s+([\d.-]+)\s*\)", raw_location)
        if service_area and coordinates:
            x, y = map(float, coordinates.groups())
            min_x, min_y, max_x, max_y = service_area.boundary.extent
            outside = not (min_x <= x <= max_x and min_y <= y <= max_y)
        if service_area and not location:
            self.add_error("location", "Enter a valid map location inside the selected service area.")
        elif service_area and location:
            if not coordinates:
                min_x, min_y, max_x, max_y = service_area.boundary.extent
                outside = not (min_x <= location.x <= max_x and min_y <= location.y <= max_y)
        if outside:
            self.add_error("location", "The location must be inside the selected service area.")
        if self.user is not None and not self.user.email_verified:
            self.add_error(None, "Verify your email address before submitting a report.")
        if self.user is not None and not self.user.cnic:
            self.add_error(None, "Add your CNIC to your account before submitting a report.")
        wants_email = cleaned_data.get("contact_preference") == Issue.ContactPreference.EMAIL
        if wants_email and not cleaned_data.get("contact_email"):
            self.add_error("contact_email", "Enter an email address to receive updates.")
        return cleaned_data


class StaffIssueUpdateForm(forms.Form):
    status = forms.ChoiceField(choices=Issue.Status.choices)
    assigned_to = forms.ModelChoiceField(queryset=None, required=False, empty_label="Unassigned")
    public_message = forms.CharField(required=False, max_length=500, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, staff_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = staff_queryset if staff_queryset is not None else self.fields["assigned_to"].queryset.none()


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
