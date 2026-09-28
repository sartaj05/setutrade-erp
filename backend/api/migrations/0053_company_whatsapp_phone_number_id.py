from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('api', '0052_operations_control_center')]

    operations = [
        migrations.AddField(
            model_name='company',
            name='whatsapp_phone_number_id',
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
