from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('api', '0061_whatsapp_message_assignment')]

    operations = [
        migrations.AddField(model_name='profile', name='mfa_enabled', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='profile', name='sso_provider', field=models.CharField(blank=True, max_length=40)),
        migrations.AddField(model_name='profile', name='passkey_enabled', field=models.BooleanField(default=False)),
    ]
