from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0003_supplier_purchaseorder_purchaseitem_goodsreceipt')]
    operations = [migrations.CreateModel(name='LedgerEntry', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('entry_type', models.CharField(choices=[('Invoice','Invoice'),('Payment','Payment'),('Credit Note','Credit Note'),('Adjustment','Adjustment')], max_length=20)),
        ('reference', models.CharField(max_length=50)), ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
        ('entry_date', models.DateField()), ('due_date', models.DateField(blank=True, null=True)),
        ('note', models.CharField(blank=True, max_length=240)), ('created_at', models.DateTimeField(auto_now_add=True)),
        ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ledger_entries', to='api.customer')),
    ])]
