from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("issues", "0005_issue_assignment_audit")]
    operations = [migrations.AddField(model_name="issueattachment", name="public_visible", field=models.BooleanField(default=True, help_text="When disabled, this photo is visible to staff only."))]
