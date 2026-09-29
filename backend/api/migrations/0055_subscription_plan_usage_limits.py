from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('api', '0054_deliveryrun_eta_at_deliveryrun_last_latitude_and_more')]

    operations = [
        migrations.AddField(
            model_name='subscriptionplan',
            name='product_limit',
            field=models.PositiveIntegerField(default=100),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='order_limit',
            field=models.PositiveIntegerField(default=100),
        ),
    ]
