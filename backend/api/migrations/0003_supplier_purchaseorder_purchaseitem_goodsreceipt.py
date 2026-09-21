from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0002_invoice')]
    operations = [
        migrations.CreateModel(name='Supplier', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('code', models.CharField(max_length=30, unique=True)), ('name', models.CharField(max_length=160)),
            ('city', models.CharField(blank=True, max_length=100)), ('phone', models.CharField(blank=True, max_length=20)),
            ('gstin', models.CharField(blank=True, max_length=20)), ('outstanding', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='PurchaseOrder', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('po_no', models.CharField(max_length=40, unique=True)), ('status', models.CharField(choices=[('Draft','Draft'),('Sent','Sent'),('Partial','Partial'),('Received','Received')], default='Draft', max_length=20)),
            ('order_date', models.DateField()), ('expected_date', models.DateField(blank=True, null=True)),
            ('total', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('notes', models.TextField(blank=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='purchase_orders', to='api.supplier')),
        ]),
        migrations.CreateModel(name='PurchaseItem', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('quantity', models.DecimalField(decimal_places=2, default=0, max_digits=12)), ('received_quantity', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
            ('unit_price', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
            ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='purchase_items', to='api.product')),
            ('purchase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='api.purchaseorder')),
        ]),
        migrations.CreateModel(name='GoodsReceipt', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('grn_no', models.CharField(max_length=40, unique=True)), ('received_date', models.DateField()), ('notes', models.TextField(blank=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('purchase', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='receipts', to='api.purchaseorder')),
        ]),
    ]
