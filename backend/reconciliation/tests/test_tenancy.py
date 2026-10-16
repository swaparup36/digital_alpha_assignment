from django.test import TestCase

from reconciliation.models import BankTransaction, LineItem, Match
from reconciliation.tests.helpers import client_for, seed, upload


class TenancyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def test_header_and_record_isolation(self):
        northwind = client_for()
        bluebird = client_for("bluebird")
        no_org = client_for("")
        unknown = client_for("unknown")
        self.assertEqual(no_org.get("/api/transactions/").status_code, 400)
        self.assertEqual(unknown.get("/api/transactions/").status_code, 404)
        upload(northwind, "2026-04-03,HALLER CC-1001,27500.00,credit,SHARED-REF\n")
        upload(bluebird, "2026-04-16,CEDAR GROVE CC-2001,40000.00,credit,SHARED-REF\n")
        self.assertEqual(len(northwind.get("/api/transactions/").data), 1)
        self.assertEqual(len(bluebird.get("/api/transactions/").data), 1)
        self.assertEqual(len(northwind.get("/api/line-items/").data), 6)
        self.assertEqual(len(bluebird.get("/api/line-items/").data), 1)
        northwind_match = Match.objects.get(transaction__organization__slug="northwind")
        self.assertEqual(bluebird.post(f"/api/matches/{northwind_match.id}/approve/").status_code, 404)
        self.assertEqual(BankTransaction.objects.get(pk=northwind_match.transaction_id).status, "suggested")

    def test_seed_is_idempotent(self):
        seed()
        seed()
        self.assertEqual(LineItem.objects.count(), 7)
