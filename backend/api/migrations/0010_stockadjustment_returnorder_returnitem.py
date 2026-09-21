from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0009_pricelist_pricerule')]
    operations = [
        migrations.CreateModel(name='StockAdjustment', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('adjustment_no', models.CharField(max_length=40, unique=True)), ('adjustment_type', models.CharField(choices=[('Damaged','Damaged'),('Count correction','Count correction'),('Expired','Expired'),('Other','Other')], max_length=30)),
            ('quantity', models.DecimalField(decimal_places=2, max_digits=12)), ('reason', models.CharField(max_length=240)), ('adjustment_date', models.DateField()), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='stock_adjustments', to='api.product')),
            ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='stock_adjustments', to='api.warehouse')),
        ]),
        migrations.CreateModel(name='ReturnOrder', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('return_no', models.CharField(max_length=40, unique=True)), ('return_type', models.CharField(choices=[('Sales Return','Sales Return'),('Purchase Return','Purchase Return')], max_length=20)),
            ('status', models.CharField(choices=[('Open','Open'),('Inspected','Inspected'),('Completed','Completed')], default='Open', max_length=20)),
            ('total', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('return_date', models.DateField()), ('reason', models.CharField(blank=True, max_length=240)),
            ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='returns', to='api.customer')),
            ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='returns', to='api.supplier')),
            ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='returns', to='api.warehouse')),
        ]),
        migrations.CreateModel(name='ReturnItem', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('quantity', models.DecimalField(decimal_places=2, max_digits=12)), ('unit_price', models.DecimalField(decimal_places=2, default=0, max_digits=12)), ('condition', models.CharField(default='Resellable', max_length=30)),
            ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='return_items', to='api.product')),
            ('return_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='api.returnorder')),
        ]),
    ]
