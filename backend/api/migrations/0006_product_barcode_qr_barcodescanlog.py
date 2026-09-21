from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0005_warehouse_stockbalance_stocktransfer')]
    operations = [
        migrations.AddField(model_name='product', name='barcode', field=models.CharField(blank=True, max_length=80, unique=True, null=True)),
        migrations.AddField(model_name='product', name='qr_code', field=models.CharField(blank=True, max_length=160)),
        migrations.CreateModel(name='BarcodeScanLog', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('action', models.CharField(choices=[('Lookup','Lookup'),('Stock In','Stock In'),('Stock Out','Stock Out'),('Count','Count')], default='Lookup', max_length=20)),
            ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=12)), ('scanned_at', models.DateTimeField(auto_now_add=True)),
            ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='scan_logs', to='api.product')),
            ('warehouse', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='scan_logs', to='api.warehouse')),
            ('scanned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='barcode_scans', to=settings.AUTH_USER_MODEL)),
        ]),
    ]
