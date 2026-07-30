from django import forms

from .models import ContractorApplication


class ContractorApplicationForm(forms.ModelForm):
    class Meta:
        model = ContractorApplication
        fields = ("company_name", "registration_number", "contact_person", "phone", "cnic_ntn", "category", "years_experience", "registration_document", "tax_document", "cnic_document", "references_document")
        widgets = {"years_experience": forms.NumberInput(attrs={"min": 0})}


class ContractorReviewForm(forms.Form):
    reason = forms.CharField(required=False)
