from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('api', '0015_tenant_reference_constraints')]
    operations = [
        migrations.CreateModel(name='CustomerPortalAccess', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('email', models.EmailField(max_length=254)), ('pin_hash', models.CharField(max_length=180)),
            ('is_active', models.BooleanField(default=True)), ('last_login_at', models.DateTimeField(blank=True, null=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portal_access', to='api.company')),
            ('customer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='portal_access', to='api.customer')),
        ], options={'constraints': [models.UniqueConstraint(fields=('company','email'), name='unique_company_portal_email')]}),
        migrations.CreateModel(name='CustomerPortalOrder', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('request_no', models.CharField(max_length=40, unique=True)),
            ('status', models.CharField(choices=[('Submitted','Submitted'),('Accepted','Accepted'),('Rejected','Rejected'),('Converted','Converted')], default='Submitted', max_length=20)),
            ('items', models.JSONField(default=list)), ('estimated_total', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('notes', models.TextField(blank=True)), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portal_orders', to='api.company')),
            ('converted_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='portal_requests', to='api.order')),
            ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='portal_orders', to='api.customer')),
        ]),
    ]
