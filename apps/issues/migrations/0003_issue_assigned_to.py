from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("issues", "0002_issueattachment")]
    operations = [migrations.AddField(
        model_name="issue",
        name="assigned_to",
        field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_issues", to=settings.AUTH_USER_MODEL),
    )]
