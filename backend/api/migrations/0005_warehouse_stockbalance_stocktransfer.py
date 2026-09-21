from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0004_ledgerentry')]
    operations = [
        migrations.CreateModel(name='Warehouse', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('code', models.CharField(max_length=30, unique=True)), ('name', models.CharField(max_length=120)),
            ('city', models.CharField(blank=True, max_length=100)), ('address', models.CharField(blank=True, max_length=240)),
            ('is_active', models.BooleanField(default=True)),
        ]),
        migrations.CreateModel(name='StockBalance', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('quantity', models.DecimalField(decimal_places=2, default=0, max_digits=12)), ('reserved', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
            ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='warehouse_balances', to='api.product')),
            ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_balances', to='api.warehouse')),
        ], options={'constraints': [models.UniqueConstraint(fields=('warehouse', 'product'), name='unique_warehouse_product')]}),
        migrations.CreateModel(name='StockTransfer', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('transfer_no', models.CharField(max_length=40, unique=True)), ('transfer_date', models.DateField()),
            ('status', models.CharField(choices=[('Draft','Draft'),('In Transit','In Transit'),('Received','Received')], default='Draft', max_length=20)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('from_warehouse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='outgoing_transfers', to='api.warehouse')),
            ('to_warehouse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='incoming_transfers', to='api.warehouse')),
        ]),
        migrations.CreateModel(name='StockTransferItem', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('quantity', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
            ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transfer_items', to='api.product')),
            ('transfer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='api.stocktransfer')),
        ]),
    ]
