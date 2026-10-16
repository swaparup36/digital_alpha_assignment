from django.test import TestCase

from reconciliation.models import BankTransaction, Match
from reconciliation.tests.helpers import client_for, seed, upload


class MatchingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def setUp(self):
        self.client = client_for()

    def test_normalized_reference_and_partial_payment(self):
        upload(self.client, "2026-04-03,Wire cc1001,20000.00,credit,REF-A\n")
        payment = BankTransaction.objects.get(reference="REF-A")
        self.assertEqual(payment.status, "suggested")
        self.assertEqual(payment.matches.get().line_item.expected_reference, "CC-1001")
        self.assertIn("remaining 27,500.00", payment.matches.get().reason)

    def test_name_and_amount_match(self):
        upload(self.client, "2026-04-07,WIRE INCOMING PATEL FAMILY TRUST,12500.00,credit,REF-B\n")
        payment = BankTransaction.objects.get(reference="REF-B")
        self.assertEqual(payment.status, "suggested")
        self.assertEqual(payment.matches.get().line_item.expected_reference, "CC-1003")

    def test_multiple_name_candidates_need_review(self):
        upload(self.client, "2026-04-11,WIRE INCOMING OAKRIDGE HOLDINGS LLC,15000.00,credit,REF-C\n")
        payment = BankTransaction.objects.get(reference="REF-C")
        self.assertEqual(payment.status, "needs_review")
        self.assertEqual(payment.matches.count(), 2)
        self.assertTrue(payment.review_reason)

    def test_overpayment_has_no_match(self):
        upload(self.client, "2026-04-15,PATEL FAMILY TRUST CC-1003,13000.00,credit,REF-D\n")
        payment = BankTransaction.objects.get(reference="REF-D")
        self.assertEqual(payment.status, "needs_review")
        self.assertEqual(payment.matches.count(), 0)
        self.assertIn("exceeds", payment.review_reason)

    def test_future_call_is_ineligible(self):
        upload(self.client, "2026-03-20,OAKRIDGE CC-1006,15000.00,credit,REF-E\n")
        payment = BankTransaction.objects.get(reference="REF-E")
        self.assertEqual(payment.status, "needs_review")
        self.assertFalse(Match.objects.filter(transaction=payment).exists())
