from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0007_whatsappmessage_whatsapporderdraft')]
    operations = [
        migrations.AddField(model_name='product', name='hsn_code', field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(model_name='product', name='gst_rate', field=models.DecimalField(decimal_places=2, default=18, max_digits=5)),
        migrations.AddField(model_name='invoice', name='place_of_supply', field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='invoice', name='supply_type', field=models.CharField(default='Intra-state', max_length=20)),
        migrations.AddField(model_name='invoice', name='e_invoice_irn', field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='invoice', name='e_invoice_status', field=models.CharField(default='Not generated', max_length=30)),
        migrations.CreateModel(name='TaxNote', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('note_no', models.CharField(max_length=40, unique=True)), ('note_type', models.CharField(choices=[('Credit Note','Credit Note'),('Debit Note','Debit Note')], max_length=20)),
            ('taxable_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('gst_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('total', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('note_date', models.DateField()), ('reason', models.CharField(blank=True, max_length=240)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tax_notes', to='api.customer')),
            ('invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tax_notes', to='api.invoice')),
        ]),
    ]
