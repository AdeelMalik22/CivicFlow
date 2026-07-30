from django.db import migrations


PERMISSIONS = (
    ("issue.submit", "Submit issues", "Create and update own citizen reports.", "own", False),
    ("issue.triage", "Triage issues", "Review and route assigned issue reports.", "assigned", False),
    ("tender.manage", "Manage tenders", "Create and manage procurement tenders.", "tenant", True),
    ("bid.submit", "Submit bids", "Create and submit contractor bids.", "own", False),
    ("award.approve", "Approve awards", "Approve a procurement award.", "tenant", True),
    ("evidence.submit", "Submit work evidence", "Submit contract progress and evidence.", "own", False),
    ("inspection.approve", "Approve inspections", "Approve assigned inspection work.", "assigned", True),
    ("payment.request", "Request payment", "Submit an eligible payment request.", "assigned", False),
    ("payment.approve", "Approve payments", "Approve eligible payment requests.", "assigned", True),
    ("payment.record", "Record payments", "Record an external payment reference.", "assigned", True),
    ("audit.view", "View audit trail", "Review organization audit events.", "tenant", True),
    ("users.manage", "Manage users", "Invite, suspend, and assign roles to members.", "tenant", True),
    ("configuration.manage", "Manage configuration", "Manage tenant reference data and policies.", "tenant", True),
    ("data.export", "Export data", "Export permitted organization records.", "tenant", True),
)


def seed_permissions(apps, schema_editor):
    permission_model = apps.get_model("accounts", "AccessPermission")
    for code, name, description, scope, sensitive in PERMISSIONS:
        permission_model.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "description": description,
                "default_scope": scope,
                "is_sensitive": sensitive,
            },
        )


def remove_permissions(apps, schema_editor):
    permission_model = apps.get_model("accounts", "AccessPermission")
    permission_model.objects.filter(code__in=[item[0] for item in PERMISSIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_accesspermission_rolepermission_tenantrole_and_more")]

    operations = [migrations.RunPython(seed_permissions, remove_permissions)]
