from django.db import models
from django.db.models import F, Q


class Organization(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class InvestorEntity(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "name"], name="unique_investor_per_org")]

    def __str__(self):
        return self.name


class CapitalCall(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    call_date = models.DateField()
    due_date = models.DateField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "number"], name="unique_call_per_org")]


class LineItem(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PARTIAL = "partially_funded", "Partially funded"
        FUNDED = "funded", "Funded"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    capital_call = models.ForeignKey(CapitalCall, on_delete=models.CASCADE)
    investor = models.ForeignKey(InvestorEntity, on_delete=models.CASCADE)
    expected_reference = models.CharField(max_length=80)
    amount_called = models.DecimalField(max_digits=14, decimal_places=2)
    amount_funded = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organization", "expected_reference"], name="unique_wire_ref_per_org"),
            models.UniqueConstraint(fields=["capital_call", "investor"], name="unique_investor_per_call"),
            models.CheckConstraint(condition=Q(amount_called__gt=0), name="called_positive"),
            models.CheckConstraint(condition=Q(amount_funded__gte=0) & Q(amount_funded__lte=F("amount_called")), name="funded_in_range"),
        ]

    @property
    def amount_remaining(self):
        return self.amount_called - self.amount_funded


class BankTransaction(models.Model):
    class Type(models.TextChoices):
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"

    class Status(models.TextChoices):
        SUGGESTED = "suggested", "Suggested"
        NEEDS_REVIEW = "needs_review", "Needs review"
        RECONCILED = "reconciled", "Reconciled"
        IGNORED = "ignored", "Ignored"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    type = models.CharField(max_length=6, choices=Type.choices)
    reference = models.CharField(max_length=120)
    status = models.CharField(max_length=20, choices=Status.choices)
    review_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organization", "reference"], name="unique_bank_ref_per_org"),
            models.CheckConstraint(condition=~Q(amount=0), name="nonzero_bank_amount"),
        ]
        ordering = ["-date", "-created_at", "-id"]


class Match(models.Model):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    transaction = models.ForeignKey(BankTransaction, on_delete=models.CASCADE, related_name="matches")
    line_item = models.ForeignKey(LineItem, on_delete=models.CASCADE, related_name="matches")
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PROPOSED)
    reason = models.TextField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["transaction", "line_item"], name="unique_match_per_pair")]
