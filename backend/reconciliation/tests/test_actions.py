from decimal import Decimal

from django.test import TestCase

from reconciliation.models import BankTransaction, LineItem, Match
from reconciliation.tests.helpers import client_for, seed, upload


class ActionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def setUp(self):
        self.client = client_for()

    def test_approval_updates_funding_and_repeat_conflicts(self):
        upload(self.client, "2026-04-03,HALLER cc1001,20000.00,credit,PART-A\n")
        match = Match.objects.get(transaction__reference="PART-A")
        url = f"/api/matches/{match.id}/approve/"
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(self.client.post(url).status_code, 409)
        item = LineItem.objects.get(expected_reference="CC-1001")
        self.assertEqual(item.amount_funded, Decimal("20000.00"))
        self.assertEqual(item.status, "partially_funded")
        self.assertEqual(BankTransaction.objects.get(reference="PART-A").status, "reconciled")

    def test_approval_rechecks_remaining_amount(self):
        upload(self.client, (
            "2026-04-03,HALLER cc1001,20000.00,credit,PART-A\n"
            "2026-04-04,HALLER cc1001,20000.00,credit,PART-B\n"
        ))
        first = Match.objects.get(transaction__reference="PART-A")
        second = Match.objects.get(transaction__reference="PART-B")
        self.assertEqual(self.client.post(f"/api/matches/{first.id}/approve/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/matches/{second.id}/approve/").status_code, 409)
        item = LineItem.objects.get(expected_reference="CC-1001")
        self.assertEqual(item.amount_funded, Decimal("20000.00"))

    def test_reject_and_ignore(self):
        upload(self.client, "2026-04-07,PATEL FAMILY TRUST,12500.00,credit,REJECT-ME\n")
        payment = BankTransaction.objects.get(reference="REJECT-ME")
        match = payment.matches.get()
        self.assertEqual(self.client.post(f"/api/matches/{match.id}/reject/").status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "needs_review")
        self.assertEqual(match.__class__.objects.get(pk=match.pk).status, "rejected")
        self.assertEqual(self.client.post(f"/api/transactions/{payment.id}/ignore/").status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "ignored")

    def test_ignore_reconciled_conflicts(self):
        upload(self.client, "2026-04-07,PATEL FAMILY TRUST,12500.00,credit,APPROVE-ME\n")
        payment = BankTransaction.objects.get(reference="APPROVE-ME")
        self.client.post(f"/api/matches/{payment.matches.get().id}/approve/")
        self.assertEqual(self.client.post(f"/api/transactions/{payment.id}/ignore/").status_code, 409)
