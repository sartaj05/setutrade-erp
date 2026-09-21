from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Customer', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('code', models.CharField(max_length=30, unique=True)), ('name', models.CharField(max_length=160)),
            ('city', models.CharField(blank=True, max_length=100)), ('phone', models.CharField(blank=True, max_length=20)),
            ('gstin', models.CharField(blank=True, max_length=20)), ('outstanding', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('credit_limit', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('due_date', models.DateField(blank=True, null=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='Product', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('sku', models.CharField(max_length=40, unique=True)), ('name', models.CharField(max_length=160)), ('category', models.CharField(blank=True, max_length=100)),
            ('stock', models.DecimalField(decimal_places=2, default=0, max_digits=12)), ('unit', models.CharField(default='pcs', max_length=30)),
            ('purchase_price', models.DecimalField(decimal_places=2, default=0, max_digits=12)), ('sell_price', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
            ('reorder_level', models.DecimalField(decimal_places=2, default=0, max_digits=12)), ('location', models.CharField(blank=True, max_length=40)),
            ('is_active', models.BooleanField(default=True)), ('updated_at', models.DateTimeField(auto_now=True)),
        ]),
        migrations.CreateModel(name='Profile', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('role', models.CharField(choices=[('OWNER','Owner'),('MANAGER','Manager'),('SALES','Sales'),('WAREHOUSE','Warehouse'),('ACCOUNTANT','Accountant')], default='SALES', max_length=20)),
            ('business_name', models.CharField(default='Khanna Electrical Distributors', max_length=160)),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='Order', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('order_no', models.CharField(max_length=30, unique=True)), ('total', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('status', models.CharField(choices=[('Processing','Processing'),('Packed','Packed'),('Ready','Ready'),('Dispatched','Dispatched')], default='Processing', max_length=20)),
            ('payment_status', models.CharField(choices=[('Paid','Paid'),('Credit','Credit'),('Overdue','Overdue')], default='Credit', max_length=20)),
            ('order_date', models.DateField()), ('notes', models.TextField(blank=True)), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='api.customer')),
        ]),
    ]
