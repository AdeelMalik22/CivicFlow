from django import forms
from .models import Tender, Bid, Award
class TenderForm(forms.ModelForm):
    class Meta:
        model = Tender
        fields = ("title", "reference", "description", "deadline", "published")
        widgets = {"deadline": forms.DateTimeInput(attrs={"type": "datetime-local"})}
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
