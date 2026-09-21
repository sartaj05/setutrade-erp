from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('api', '0013_production_foundation')]
    operations = [
        migrations.AlterField(model_name='order', name='status', field=models.CharField(choices=[('Draft','Draft'),('Confirmed','Confirmed'),('Processing','Processing'),('Packed','Packed'),('Ready','Ready'),('Dispatched','Dispatched'),('Cancelled','Cancelled')], default='Draft', max_length=20)),
        migrations.AlterField(model_name='order', name='payment_status', field=models.CharField(choices=[('Paid','Paid'),('Partial','Partial'),('Credit','Credit'),('Overdue','Overdue')], default='Credit', max_length=20)),
        migrations.AlterField(model_name='invoice', name='status', field=models.CharField(choices=[('Paid','Paid'),('Partial','Partial'),('Unpaid','Unpaid'),('Credit','Credit'),('Cancelled','Cancelled')], default='Unpaid', max_length=20)),
        migrations.AlterField(model_name='purchaseorder', name='status', field=models.CharField(choices=[('Draft','Draft'),('Approved','Approved'),('Sent','Sent'),('Partial','Partial'),('Received','Received'),('Cancelled','Cancelled')], default='Draft', max_length=20)),
        migrations.AlterField(model_name='stocktransfer', name='status', field=models.CharField(choices=[('Draft','Draft'),('Approved','Approved'),('In Transit','In Transit'),('Received','Received'),('Cancelled','Cancelled')], default='Draft', max_length=20)),
    ]
