from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("issues", "0003_issue_assigned_to")]
    operations = [
        migrations.AddField(
            model_name="issue", name="assigned_department",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_issues", to="tenants.department"),
        ),
        migrations.CreateModel(
            name="IssueInternalNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField(max_length=2000)),
                ("created_at", models.DateTimeField()),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="issue_internal_notes", to=settings.AUTH_USER_MODEL)),
                ("issue", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="internal_notes", to="issues.issue")),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
