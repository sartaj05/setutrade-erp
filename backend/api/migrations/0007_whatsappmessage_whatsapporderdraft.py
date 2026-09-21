from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0006_product_barcode_qr_barcodescanlog')]
    operations = [
        migrations.CreateModel(name='WhatsAppMessage', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('direction', models.CharField(choices=[('Inbound','Inbound'),('Outbound','Outbound')], max_length=10)),
            ('message', models.TextField()), ('status', models.CharField(default='Delivered', max_length=20)), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='whatsapp_messages', to='api.customer')),
        ]),
        migrations.CreateModel(name='WhatsAppOrderDraft', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('draft_no', models.CharField(max_length=40, unique=True)), ('raw_message', models.TextField()), ('parsed_items', models.JSONField(default=list)),
            ('status', models.CharField(choices=[('Draft','Draft'),('Quoted','Quoted'),('Confirmed','Confirmed')], default='Draft', max_length=20)),
            ('estimated_total', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='whatsapp_order_drafts', to='api.customer')),
        ]),
    ]
