from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_issue_received_email(self, recipient, reference, tracking_url):
    return send_mail(
        subject=f"CivicFlow report received: {reference}",
        message=f"We received your infrastructure report ({reference}).\n\nTrack progress securely: {tracking_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
    )


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_issue_status_email(self, recipient, reference, status_label, message):
    return send_mail(
        subject=f"CivicFlow update: {reference}",
        message=f"There is an update to your CivicFlow report {reference}.\n\nStatus: {status_label}\n{message}\n\nUse your existing reference and verification code to view the full timeline.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
    )
