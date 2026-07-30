from django import forms
from .models import Tender, Bid, Award
class TenderForm(forms.ModelForm):
    class Meta:
        model = Tender
        fields = ("title", "reference", "category", "procurement_method", "department", "service_area", "description", "budget", "currency", "eligibility", "evaluation_criteria", "submission_instructions", "clarification_deadline", "deadline", "contact_name", "contact_email", "attachment", "cover_image", "published")
        widgets = {
            "deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "clarification_deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 6}),
            "eligibility": forms.Textarea(attrs={"rows": 4}),
            "evaluation_criteria": forms.Textarea(attrs={"rows": 4}),
            "submission_instructions": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "field")
        self.fields["department"].queryset = self.fields["department"].queryset.order_by("name")
        self.fields["service_area"].queryset = self.fields["service_area"].queryset.order_by("name")
        self.fields["budget"].widget.attrs["placeholder"] = "e.g. 25000000"
        self.fields["currency"].widget.attrs["placeholder"] = "PKR"
class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ("amount", "proposal", "document")

    def clean_document(self):
        document = self.cleaned_data["document"]
        if document.content_type not in {"application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}:
            raise forms.ValidationError("Upload a PDF or Word document.")
        if document.size > 15 * 1024 * 1024:
            raise forms.ValidationError("Bid documents must be 15 MB or smaller.")
        return document

class AwardForm(forms.ModelForm):
    class Meta:
        model = Award
        fields = ("winning_bid", "decision_note")
