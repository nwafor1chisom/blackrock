import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── AuditLog ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False,
                    default=uuid.uuid4, editable=False)),
                ('user', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True,
                    related_name='audit_logs',
                )),
                ('action', models.CharField(max_length=30, choices=[
                    ('LOGIN','User Login'),('LOGOUT','User Logout'),
                    ('DEPOSIT_SUBMIT','Deposit Submitted'),('DEPOSIT_APPROVE','Deposit Approved'),
                    ('DEPOSIT_REJECT','Deposit Rejected'),('WITHDRAW_SUBMIT','Withdrawal Submitted'),
                    ('WITHDRAW_APPROVE','Withdrawal Approved'),('WITHDRAW_REJECT','Withdrawal Rejected'),
                    ('KYC_SUBMIT','KYC Submitted'),('KYC_APPROVE','KYC Approved'),
                    ('KYC_REJECT','KYC Rejected'),('BONUS_CREDIT','Bonus Credited'),
                    ('REFERRAL_APPROVE','Referral Approved'),('PROFILE_UPDATE','Profile Updated'),
                    ('ADMIN_ACTION','Admin Action'),
                ])),
                ('description', models.TextField()),
                ('ip_address', models.GenericIPAddressField(null=True, blank=True)),
                ('user_agent', models.TextField(blank=True)),
                ('extra_data', models.JSONField(default=dict, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'audit_logs', 'ordering': ['-created_at']},
        ),

        # ── InvestmentPlan ────────────────────────────────────────────────
        migrations.CreateModel(
            name='InvestmentPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('interest', models.FloatField()),
                ('duration', models.CharField(max_length=50)),
                ('min_amount', models.DecimalField(max_digits=14, decimal_places=2)),
                ('max_amount', models.DecimalField(max_digits=14, decimal_places=2,
                    null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveSmallIntegerField(default=0)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Investment Plan',
                'verbose_name_plural': 'Investment Plans',
                'db_table': 'investment_plans',
                'ordering': ['sort_order', 'min_amount'],
            },
        ),

        # ── ContactMessage ─────────────────────────────────────────────────
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField()),
                ('subject', models.CharField(max_length=255, blank=True)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('ip_address', models.GenericIPAddressField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Contact Message',
                'verbose_name_plural': 'Contact Messages',
                'db_table': 'contact_messages',
                'ordering': ['-created_at'],
            },
        ),

        # ── Indexes ────────────────────────────────────────────────────────
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', 'action'], name='audit_user_action_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['created_at'], name='audit_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='investmentplan',
            index=models.Index(fields=['is_active'], name='plan_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='investmentplan',
            index=models.Index(fields=['sort_order'], name='plan_sort_order_idx'),
        ),
        migrations.AddIndex(
            model_name='contactmessage',
            index=models.Index(fields=['is_read'], name='contact_is_read_idx'),
        ),
        migrations.AddIndex(
            model_name='contactmessage',
            index=models.Index(fields=['email'], name='contact_email_idx'),
        ),
    ]
