from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("issues", "0004_issue_assignment_and_internal_notes")]
    operations = [migrations.CreateModel(
        name="IssueAssignmentAudit",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("previous_staff_id", models.IntegerField(blank=True, null=True)),
            ("new_staff_id", models.IntegerField(blank=True, null=True)),
            ("previous_department_id", models.IntegerField(blank=True, null=True)),
            ("new_department_id", models.IntegerField(blank=True, null=True)),
            ("created_at", models.DateTimeField()),
            ("actor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="issue_assignment_audits", to=settings.AUTH_USER_MODEL)),
            ("issue", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignment_audits", to="issues.issue")),
        ],
        options={"ordering": ("-created_at",)},
    )]
