from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('api', '0062_auth_security_controls')]

    operations = [
        migrations.AddField(model_name='paymentlink', name='provider', field=models.CharField(default='UPI', max_length=30)),
        migrations.AddField(model_name='paymentlink', name='provider_order_id', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='paymentlink', name='upi_uri', field=models.CharField(blank=True, max_length=500)),
        migrations.AddField(model_name='paymentlink', name='paid_at', field=models.DateTimeField(blank=True, null=True)),
    ]
