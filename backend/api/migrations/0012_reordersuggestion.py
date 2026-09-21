from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0011_salesvisit_salestarget')]
    operations = [migrations.CreateModel(name='ReorderSuggestion', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('current_stock', models.DecimalField(decimal_places=2, default=0, max_digits=12)), ('avg_daily_sales', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        ('lead_time_days', models.PositiveIntegerField(default=1)), ('suggested_quantity', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        ('days_cover', models.DecimalField(decimal_places=2, default=0, max_digits=8)), ('risk', models.CharField(choices=[('High','High'),('Medium','Medium'),('Low','Low')], default='Medium', max_length=10)),
        ('generated_at', models.DateTimeField(auto_now=True)),
        ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reorder_suggestions', to='api.product')),
        ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reorder_suggestions', to='api.warehouse')),
    ], options={'constraints': [models.UniqueConstraint(fields=('product','warehouse'), name='unique_reorder_suggestion')]})]
