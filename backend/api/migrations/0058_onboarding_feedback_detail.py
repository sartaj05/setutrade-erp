from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api", "0057_client_onboarding_imports_feedback")]

    operations = [
        migrations.AddField(model_name="onboardingfeedback", name="external_tools", field=models.TextField(blank=True)),
        migrations.AddField(model_name="onboardingfeedback", name="data_trust", field=models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="onboardingfeedback", name="offline_needs", field=models.TextField(blank=True)),
        migrations.AddField(model_name="onboardingfeedback", name="daily_report", field=models.TextField(blank=True)),
    ]
