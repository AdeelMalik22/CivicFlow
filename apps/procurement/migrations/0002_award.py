import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Award',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('decision_note', models.TextField(blank=True)),
                ('awarded_at', models.DateTimeField(auto_now_add=True)),
                ('awarded_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('tender', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='award', to='procurement.tender')),
                ('winning_bid', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='award', to='procurement.bid')),
            ],
        ),
    ]
