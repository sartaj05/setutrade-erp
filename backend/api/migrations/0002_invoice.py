from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('api', '0001_initial')]
    operations = [
        migrations.CreateModel(name='Invoice', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('invoice_no', models.CharField(max_length=40, unique=True)), ('gstin', models.CharField(blank=True, max_length=20)),
            ('taxable_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('cgst', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('sgst', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('igst', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('total', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('status', models.CharField(choices=[('Paid','Paid'),('Unpaid','Unpaid'),('Credit','Credit')], default='Unpaid', max_length=20)),
            ('invoice_date', models.DateField()), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('order', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='invoice', to='api.order')),
        ]),
    ]
