import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0003_tenantmembership'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('reference', models.CharField(editable=False, max_length=24, unique=True)),
                ('category', models.CharField(choices=[('pothole', 'Pothole or road damage'), ('streetlight', 'Streetlight or signal'), ('drainage', 'Blocked drain or flooding'), ('sidewalk', 'Sidewalk or accessibility'), ('public-building', 'Public building'), ('other', 'Other infrastructure issue')], max_length=32)),
                ('description', models.TextField(max_length=4000)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('contact_preference', models.CharField(choices=[('email', 'Email updates'), ('none', 'No updates')], default='none', max_length=12)),
                ('status', models.CharField(choices=[('submitted', 'Submitted'), ('under-review', 'Under review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('duplicate', 'Duplicate'), ('closed', 'Closed')], default='submitted', max_length=24)),
                ('tracking_token_hash', models.CharField(editable=False, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reporter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reported_issues', to=settings.AUTH_USER_MODEL)),
                ('service_area', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='issues', to='tenants.servicearea')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='issues', to='tenants.tenant')),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='IssueStatusEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('submitted', 'Submitted'), ('under-review', 'Under review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('duplicate', 'Duplicate'), ('closed', 'Closed')], max_length=24)),
                ('public_message', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='issue_status_events', to=settings.AUTH_USER_MODEL)),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_events', to='issues.issue')),
            ],
            options={
                'ordering': ('created_at',),
            },
        ),
        migrations.AddIndex(
            model_name='issue',
            index=models.Index(fields=['tenant', 'status', 'created_at'], name='issue_tenant_status_idx'),
        ),
        migrations.AddIndex(
            model_name='issue',
            index=models.Index(fields=['reference'], name='issue_reference_idx'),
        ),
    ]
