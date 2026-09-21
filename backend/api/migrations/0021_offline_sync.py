from django.db import migrations,models
import django.db.models.deletion
class Migration(migrations.Migration):
 dependencies=[('api','0020_accounting_integration')]
 operations=[migrations.CreateModel(name='OfflineSyncReceipt',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('event_id',models.CharField(max_length=80)),('event_type',models.CharField(max_length=50)),('payload',models.JSONField(blank=True,default=dict)),('device_id',models.CharField(blank=True,max_length=100)),('synced_at',models.DateTimeField(auto_now_add=True)),('company',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='offline_sync_receipts',to='api.company')),('user',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,to='auth.user'))],options={'constraints':[models.UniqueConstraint(fields=('company','event_id'),name='unique_company_offline_event')]})]
