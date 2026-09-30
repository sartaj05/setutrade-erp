from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0059_bank_statement_reconciliation')]

    operations = [
        migrations.AddField(
            model_name='whatsapporderdraft',
            name='quotation',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='whatsapp_draft', to='api.quotation'),
        ),
        migrations.AddField(
            model_name='whatsapporderdraft',
            name='converted_order',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='whatsapp_draft', to='api.order'),
        ),
    ]
