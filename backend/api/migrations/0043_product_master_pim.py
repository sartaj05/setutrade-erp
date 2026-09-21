from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('api','0042_ai_action_copilot'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='ProductMasterProfile',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('brand',models.CharField(blank=True,max_length=100)),('manufacturer',models.CharField(blank=True,max_length=140)),
            ('primary_uom',models.CharField(default='pcs',max_length=30)),('purchase_uom',models.CharField(default='pcs',max_length=30)),('sales_uom',models.CharField(default='pcs',max_length=30)),
            ('uom_conversions',models.JSONField(blank=True,default=dict)),('alternate_barcodes',models.JSONField(blank=True,default=list)),
            ('mrp',models.DecimalField(decimal_places=2,default=0,max_digits=14)),('dealer_price',models.DecimalField(decimal_places=2,default=0,max_digits=14)),('distributor_price',models.DecimalField(decimal_places=2,default=0,max_digits=14)),
            ('weight_kg',models.DecimalField(decimal_places=3,default=0,max_digits=10)),('dimensions',models.JSONField(blank=True,default=dict)),
            ('batch_required',models.BooleanField(default=False)),('serial_required',models.BooleanField(default=False)),('expiry_required',models.BooleanField(default=False)),
            ('minimum_stock',models.DecimalField(decimal_places=2,default=0,max_digits=12)),('maximum_stock',models.DecimalField(decimal_places=2,default=0,max_digits=12)),('reorder_quantity',models.DecimalField(decimal_places=2,default=0,max_digits=12)),
            ('data_quality_score',models.PositiveSmallIntegerField(default=0)),('governance_status',models.CharField(default='Approved',max_length=30)),('updated_at',models.DateTimeField(auto_now=True)),
            ('company',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='product_master_profiles',to='api.company')),
            ('preferred_supplier',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='preferred_products',to='api.supplier')),
            ('product',models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name='master_profile',to='api.product')),
            ('updated_by',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='product_master_updates',to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='ProductChangeRequest',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('change_type',models.CharField(max_length=80)),('requested_changes',models.JSONField(default=dict)),('reason',models.CharField(blank=True,max_length=240)),
            ('status',models.CharField(choices=[('Pending','Pending'),('Approved','Approved'),('Rejected','Rejected')],default='Pending',max_length=20)),('created_at',models.DateTimeField(auto_now_add=True)),('reviewed_at',models.DateTimeField(blank=True,null=True)),
            ('approved_by',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='approved_product_changes',to=settings.AUTH_USER_MODEL)),('company',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='product_change_requests',to='api.company')),
            ('product',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='change_requests',to='api.product')),('requested_by',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='requested_product_changes',to=settings.AUTH_USER_MODEL)),
        ])]
