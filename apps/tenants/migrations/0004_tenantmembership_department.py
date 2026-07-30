import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_tenantmembership'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenantmembership',
            name='department',
            field=models.ForeignKey(blank=True, help_text='The department this staff member belongs to.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='memberships', to='tenants.department'),
        ),
    ]
