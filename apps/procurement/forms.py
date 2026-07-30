from django import forms
from .models import Tender, Bid
class TenderForm(forms.ModelForm):
    class Meta:
        model = Tender
        fields = ("title", "reference", "description", "deadline", "published")
        widgets = {"deadline": forms.DateTimeInput(attrs={"type": "datetime-local"})}
class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ("amount", "proposal", "document")
