import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContractorApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=180)),
                ('registration_number', models.CharField(max_length=120)),
                ('contact_person', models.CharField(max_length=150)),
                ('phone', models.CharField(max_length=32)),
                ('cnic_ntn', models.CharField(max_length=64)),
                ('category', models.CharField(max_length=120)),
                ('years_experience', models.PositiveSmallIntegerField()),
                ('registration_document', models.FileField(upload_to='contractors/%Y/%m/')),
                ('tax_document', models.FileField(upload_to='contractors/%Y/%m/')),
                ('cnic_document', models.FileField(upload_to='contractors/%Y/%m/')),
                ('references_document', models.FileField(blank=True, upload_to='contractors/%Y/%m/')),
                ('status', models.CharField(choices=[('pending_review', 'Pending review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('info_requested', 'Information requested'), ('suspended', 'Suspended')], default='pending_review', max_length=20)),
                ('review_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contractor_applications', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contractor_reviews', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
