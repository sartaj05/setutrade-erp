from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('api', '0014_workflow_choices')]

    operations = [
        migrations.AlterField(
            model_name='product', name='sku', field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name='product', name='barcode', field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='customer', name='code', field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='warehouse', name='code', field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='supplier', name='code', field=models.CharField(max_length=30),
        ),
        migrations.AddConstraint(
            model_name='product', constraint=models.UniqueConstraint(fields=('company', 'sku'), name='unique_company_product_sku'),
        ),
        migrations.AddConstraint(
            model_name='product', constraint=models.UniqueConstraint(fields=('company', 'barcode'), name='unique_company_product_barcode'),
        ),
        migrations.AddConstraint(
            model_name='customer', constraint=models.UniqueConstraint(fields=('company', 'code'), name='unique_company_customer_code'),
        ),
        migrations.AddConstraint(
            model_name='warehouse', constraint=models.UniqueConstraint(fields=('company', 'code'), name='unique_company_warehouse_code'),
        ),
        migrations.AddConstraint(
            model_name='supplier', constraint=models.UniqueConstraint(fields=('company', 'code'), name='unique_company_supplier_code'),
        ),
    ]
