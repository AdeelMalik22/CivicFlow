import secrets
from hashlib import sha256

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from .forms import IssueReportForm
from .models import Issue, IssueAttachment, IssueStatusEvent, create_tracking_token


def _reference() -> str:
    return f"CF-{timezone.now():%Y%m%d}-{secrets.token_hex(3).upper()}"


@transaction.atomic
def submit_issue(form: IssueReportForm, *, request) -> tuple[Issue, str]:
    issue = form.save(commit=False)
    issue.service_area = form.cleaned_data["service_area"]
    issue.tenant = issue.service_area.tenant
    issue.reporter = request.user if request.user.is_authenticated else None
    token = create_tracking_token()
    issue.set_tracking_token(token)

    for _ in range(3):
        issue.reference = _reference()
        try:
            issue.full_clean()
            issue.save()
            break
        except IntegrityError:
            continue
    else:
        raise IntegrityError("Could not allocate a unique issue reference.")

    IssueStatusEvent.objects.create(
        issue=issue,
        status=Issue.Status.SUBMITTED,
        public_message="Your report was received and is awaiting review.",
        actor=None,
    )

    for uploaded in form.cleaned_data.get("attachments", []):
        digest = sha256()
        for chunk in uploaded.chunks():
            digest.update(chunk)
        uploaded.seek(0)
        IssueAttachment.objects.create(
            issue=issue,
            file=uploaded,
            original_name=uploaded.name[:255],
            checksum=digest.hexdigest(),
            uploaded_by=issue.reporter,
        )

    if issue.contact_preference == Issue.ContactPreference.EMAIL and issue.contact_email:
        tracking_url = request.build_absolute_uri(
            reverse("issues:track", kwargs={"reference": issue.reference, "token": token})
        )
        transaction.on_commit(
            lambda: send_mail(
                subject=f"CivicFlow report received: {issue.reference}",
                message=(
                    f"We received your infrastructure report ({issue.reference}).\n\n"
                    f"Track progress securely: {tracking_url}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[issue.contact_email],
            )
        )
    return issue, token
