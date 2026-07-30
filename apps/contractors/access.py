from .models import ContractorApplication

def can_submit_bids(user) -> bool:
    return bool(user.is_authenticated and user.is_active and ContractorApplication.objects.filter(applicant=user, status=ContractorApplication.Status.APPROVED).exists())
