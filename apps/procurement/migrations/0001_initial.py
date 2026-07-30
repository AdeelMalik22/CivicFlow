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
            name='Tender',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('reference', models.CharField(max_length=40, unique=True)),
                ('description', models.TextField()),
                ('published', models.BooleanField(default=False)),
                ('deadline', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('proposal', models.TextField()),
                ('document', models.FileField(upload_to='bids/%Y/%m/')),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('contractor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bids', to=settings.AUTH_USER_MODEL)),
                ('tender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bids', to='procurement.tender')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('tender', 'contractor'), name='one_bid_per_tender')],
            },
        ),
    ]
