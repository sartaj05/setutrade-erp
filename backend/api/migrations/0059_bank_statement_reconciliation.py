import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0058_onboarding_feedback_detail"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BankStatementImport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("filename", models.CharField(max_length=180)),
                ("account_label", models.CharField(blank=True, max_length=120)),
                ("status", models.CharField(choices=[("Imported", "Imported"), ("Failed", "Failed")], default="Imported", max_length=20)),
                ("row_count", models.PositiveIntegerField(default=0)),
                ("imported_count", models.PositiveIntegerField(default=0)),
                ("duplicate_count", models.PositiveIntegerField(default=0)),
                ("error_count", models.PositiveIntegerField(default=0)),
                ("errors", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bank_statement_imports", to="api.company")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bank_statement_imports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="BankStatementLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("line_number", models.PositiveIntegerField()),
                ("transaction_date", models.DateField()),
                ("reference", models.CharField(blank=True, max_length=120)),
                ("description", models.CharField(blank=True, max_length=300)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("direction", models.CharField(choices=[("Credit", "Credit"), ("Debit", "Debit")], max_length=12)),
                ("status", models.CharField(choices=[("Unmatched", "Unmatched"), ("Matched", "Matched"), ("Skipped", "Skipped")], default="Unmatched", max_length=20)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bank_statement_lines", to="api.company")),
                ("customer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bank_statement_lines", to="api.customer")),
                ("payment_transaction", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="statement_lines", to="api.paymenttransaction")),
                ("statement", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="api.bankstatementimport")),
            ],
            options={"ordering": ["line_number"]},
        ),
        migrations.AddConstraint(
            model_name="bankstatementline",
            constraint=models.UniqueConstraint(fields=("statement", "line_number"), name="unique_statement_line_number"),
        ),
    ]
