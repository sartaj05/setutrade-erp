from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0010_stockadjustment_returnorder_returnitem')]
    operations = [
        migrations.CreateModel(name='SalesVisit', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('visit_date', models.DateField()), ('status', models.CharField(choices=[('Planned','Planned'),('Visited','Visited'),('Missed','Missed')], default='Planned', max_length=20)),
            ('territory', models.CharField(blank=True, max_length=100)), ('order_value', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('collection_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('notes', models.CharField(blank=True, max_length=240)),
            ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sales_visits', to='api.customer')),
            ('salesperson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sales_visits', to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='SalesTarget', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('month', models.DateField()), ('target_sales', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('target_collection', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('salesperson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sales_targets', to=settings.AUTH_USER_MODEL)),
        ], options={'constraints': [models.UniqueConstraint(fields=('salesperson','month'), name='unique_sales_target_month')]}),
    ]
