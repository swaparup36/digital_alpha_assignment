import django.db.models.deletion
from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("slug", models.SlugField(unique=True)),
                ("name", models.CharField(max_length=120)),
            ],
        ),
        migrations.CreateModel(
            name="InvestorEntity",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reconciliation.organization")),
            ],
        ),
        migrations.CreateModel(
            name="CapitalCall",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("number", models.PositiveIntegerField()),
                ("call_date", models.DateField()),
                ("due_date", models.DateField()),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reconciliation.organization")),
            ],
        ),
        migrations.CreateModel(
            name="LineItem",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("expected_reference", models.CharField(max_length=80)),
                ("amount_called", models.DecimalField(decimal_places=2, max_digits=14)),
                ("amount_funded", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("status", models.CharField(choices=[("open", "Open"), ("partially_funded", "Partially funded"), ("funded", "Funded")], default="open", max_length=20)),
                ("capital_call", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reconciliation.capitalcall")),
                ("investor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reconciliation.investorentity")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reconciliation.organization")),
            ],
        ),
        migrations.CreateModel(
            name="BankTransaction",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("date", models.DateField()),
                ("description", models.TextField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("type", models.CharField(choices=[("credit", "Credit"), ("debit", "Debit")], max_length=6)),
                ("reference", models.CharField(max_length=120)),
                ("status", models.CharField(choices=[("suggested", "Suggested"), ("needs_review", "Needs review"), ("reconciled", "Reconciled"), ("ignored", "Ignored")], max_length=20)),
                ("review_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reconciliation.organization")),
            ],
            options={"ordering": ["-date", "-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="Match",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("proposed", "Proposed"), ("approved", "Approved"), ("rejected", "Rejected")], default="proposed", max_length=8)),
                ("reason", models.TextField()),
                ("line_item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="matches", to="reconciliation.lineitem")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reconciliation.organization")),
                ("transaction", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="matches", to="reconciliation.banktransaction")),
            ],
        ),
        migrations.AddConstraint(model_name="investorentity", constraint=models.UniqueConstraint(fields=("organization", "name"), name="unique_investor_per_org")),
        migrations.AddConstraint(model_name="capitalcall", constraint=models.UniqueConstraint(fields=("organization", "number"), name="unique_call_per_org")),
        migrations.AddConstraint(model_name="lineitem", constraint=models.UniqueConstraint(fields=("organization", "expected_reference"), name="unique_wire_ref_per_org")),
        migrations.AddConstraint(model_name="lineitem", constraint=models.UniqueConstraint(fields=("capital_call", "investor"), name="unique_investor_per_call")),
        migrations.AddConstraint(model_name="lineitem", constraint=models.CheckConstraint(condition=Q(amount_called__gt=0), name="called_positive")),
        migrations.AddConstraint(model_name="lineitem", constraint=models.CheckConstraint(condition=Q(amount_funded__gte=0) & Q(amount_funded__lte=F("amount_called")), name="funded_in_range")),
        migrations.AddConstraint(model_name="banktransaction", constraint=models.UniqueConstraint(fields=("organization", "reference"), name="unique_bank_ref_per_org")),
        migrations.AddConstraint(model_name="banktransaction", constraint=models.CheckConstraint(condition=~Q(amount=0), name="nonzero_bank_amount")),
        migrations.AddConstraint(model_name="match", constraint=models.UniqueConstraint(fields=("transaction", "line_item"), name="unique_match_per_pair")),
    ]
