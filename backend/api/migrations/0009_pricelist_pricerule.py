from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0008_gst_compliance_fields_taxnote')]
    operations = [
        migrations.CreateModel(name='PriceList', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('name', models.CharField(max_length=120)), ('is_active', models.BooleanField(default=True)),
            ('valid_from', models.DateField(blank=True, null=True)), ('valid_to', models.DateField(blank=True, null=True)),
            ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='price_lists', to='api.customer')),
        ]),
        migrations.CreateModel(name='PriceRule', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('min_quantity', models.DecimalField(decimal_places=2, default=1, max_digits=12)), ('price', models.DecimalField(decimal_places=2, max_digits=12)),
            ('discount_percent', models.DecimalField(decimal_places=2, default=0, max_digits=6)), ('scheme_text', models.CharField(blank=True, max_length=160)),
            ('price_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='api.pricelist')),
            ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_rules', to='api.product')),
        ], options={'ordering': ['product__name', 'min_quantity']}),
    ]
