from django.conf import settings
from django.core import mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Verify CivicFlow email configuration and optionally send a test message."

    def add_arguments(self, parser):
        parser.add_argument("--to", help="Send a test email to this address.")

    def handle(self, *args, **options):
        backend = settings.EMAIL_BACKEND
        sender = settings.DEFAULT_FROM_EMAIL
        self.stdout.write(f"Backend: {backend}")
        self.stdout.write(f"Sender: {sender}")
        if not sender or "@" not in sender:
            raise CommandError("DEFAULT_FROM_EMAIL must contain a valid email address.")
        if "smtp" in backend.lower():
            for name in ("EMAIL_HOST", "EMAIL_PORT"):
                if not getattr(settings, name, None):
                    raise CommandError(f"{name} is missing for the SMTP backend.")
            self.stdout.write(self.style.SUCCESS("SMTP configuration is present."))
        else:
            self.stdout.write(self.style.WARNING("Non-SMTP backend active; email may be console-only."))
        recipient = options.get("to")
        if recipient:
            sent = mail.send(
                "CivicFlow email configuration test",
                "CivicFlow successfully delivered this configuration test.",
                sender,
                [recipient],
                fail_silently=False,
            )
            if sent != 1:
                raise CommandError("The email backend did not report a successful delivery.")
            self.stdout.write(self.style.SUCCESS(f"Test email sent to {recipient}."))
        else:
            self.stdout.write("Configuration check complete. Use --to someone@example.com to send a test.")
