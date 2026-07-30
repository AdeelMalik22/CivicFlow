import django.db.models.deletion
import django.db.models.functions.text
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('tenants', '0003_tenantmembership'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=80, unique=True)),
                ('name', models.CharField(max_length=120)),
                ('description', models.CharField(blank=True, max_length=240)),
                ('default_scope', models.CharField(choices=[('own', 'Own records'), ('assigned', 'Assigned records'), ('tenant', 'Entire organization')], default='tenant', max_length=16)),
                ('is_sensitive', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scope', models.CharField(choices=[('own', 'Own records'), ('assigned', 'Assigned records'), ('tenant', 'Entire organization')], max_length=16)),
                ('permission', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='grants', to='accounts.accesspermission')),
            ],
            options={
                'ordering': ('permission__name',),
            },
        ),
        migrations.CreateModel(
            name='TenantRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=40)),
                ('description', models.CharField(blank=True, max_length=240)),
                ('requires_mfa', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('permissions', models.ManyToManyField(related_name='roles', through='accounts.RolePermission', to='accounts.accesspermission')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='roles', to='tenants.tenant')),
            ],
            options={
                'ordering': ('tenant__name', 'name'),
            },
        ),
        migrations.AddField(
            model_name='rolepermission',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grants', to='accounts.tenantrole'),
        ),
        migrations.CreateModel(
            name='MembershipRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='role_assignments_made', to=settings.AUTH_USER_MODEL)),
                ('membership', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_assignments', to='tenants.tenantmembership')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='membership_assignments', to='accounts.tenantrole')),
            ],
        ),
        migrations.CreateModel(
            name='SeparationOfDutiesPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('is_active', models.BooleanField(default=True)),
                ('approver_permission', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='approver_policies', to='accounts.accesspermission')),
                ('initiator_permission', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='initiator_policies', to='accounts.accesspermission')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='separation_policies', to='tenants.tenant')),
            ],
            options={
                'ordering': ('tenant__name', 'name'),
                'constraints': [models.UniqueConstraint(fields=('tenant', 'initiator_permission', 'approver_permission'), name='tenant_sod_policy_unique')],
            },
        ),
        migrations.AddConstraint(
            model_name='tenantrole',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('code'), models.F('tenant'), name='role_tenant_code_ci_unique'),
        ),
        migrations.AddConstraint(
            model_name='tenantrole',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('name'), models.F('tenant'), name='role_tenant_name_ci_unique'),
        ),
        migrations.AddConstraint(
            model_name='rolepermission',
            constraint=models.UniqueConstraint(fields=('role', 'permission'), name='role_permission_unique'),
        ),
        migrations.AddConstraint(
            model_name='membershiprole',
            constraint=models.UniqueConstraint(fields=('membership', 'role'), name='membership_role_unique'),
        ),
    ]
