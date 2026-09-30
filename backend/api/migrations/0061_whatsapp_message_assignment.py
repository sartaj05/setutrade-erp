from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0060_whatsapp_order_conversion')]

    operations = [
        migrations.AddField(
            model_name='whatsappmessage',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_whatsapp_messages', to='auth.user'),
        ),
    ]
