from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0055_subscription_plan_usage_limits')]

    operations = [
        migrations.CreateModel(
            name='SubscriptionPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(default='RAZORPAY', max_length=30)),
                ('external_order_id', models.CharField(max_length=120)),
                ('external_payment_id', models.CharField(blank=True, max_length=120)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='INR', max_length=8)),
                ('status', models.CharField(choices=[('Created', 'Created'), ('Pending', 'Pending'), ('Paid', 'Paid'), ('Failed', 'Failed'), ('Refunded', 'Refunded')], default='Created', max_length=20)),
                ('signature', models.CharField(blank=True, max_length=256)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_payments', to='api.company')),
                ('invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='api.subscriptioninvoice')),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='api.companysubscription')),
                ('target_plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subscription_payments', to='api.subscriptionplan')),
            ],
            options={'constraints': [models.UniqueConstraint(fields=('company', 'provider', 'external_order_id'), name='unique_company_subscription_order')]},
        ),
    ]
