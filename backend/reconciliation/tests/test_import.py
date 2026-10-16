from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from reconciliation.models import BankTransaction
from reconciliation.tests.helpers import client_for, seed, upload


class ImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def setUp(self):
        self.client = client_for()

    def test_missing_column_rejects_entire_file(self):
        response = self.client.post(
            "/api/imports/",
            {"file": SimpleUploadedFile("bad.csv", b"date,description,amount,type\n2026-04-03,Wire,10.00,credit\n")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(BankTransaction.objects.count(), 0)

    def test_amount_date_type_and_sign_validation(self):
        response = upload(self.client, (
            '2026-04-03,Valid wire,"25,000.00",credit,A\n'
            '2026-04-31,Bad date,10.00,credit,B\n'
            '2026-04-03,Bad sign,-10.00,credit,C\n'
            '2026-04-03,Bad debit,10.00,debit,D\n'
            '2026-04-03,Outgoing,-25.00,DEBIT,E\n'
        ))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["imported"], 2)
        self.assertEqual([error["line"] for error in response.data["errors"]], [3, 4, 5])
        self.assertEqual(BankTransaction.objects.get(reference="A").amount, Decimal("25000.00"))
        self.assertEqual(BankTransaction.objects.get(reference="E").status, "ignored")

    def test_duplicate_in_file_and_reupload(self):
        rows = "2026-04-03,Wire,10.00,credit,DUP\n2026-04-04,Another wire,20.00,credit,DUP\n"
        first = upload(self.client, rows)
        second = upload(self.client, rows)
        self.assertEqual((first.data["imported"], first.data["duplicates"]), (1, 1))
        self.assertEqual((second.data["imported"], second.data["duplicates"]), (0, 2))
        self.assertEqual(BankTransaction.objects.count(), 1)

    def test_spaces_are_trimmed_and_invalid_rows_do_not_block_valid_rows(self):
        response = upload(self.client, (
            ' 2026-04-03 ,  Valid wire  , 100.00 , CREDIT ,  SPACED  \n'
            '2026-04-03, ,5.00,credit,BLANK\n'
        ))
        self.assertEqual(response.data["imported"], 1)
        self.assertEqual(response.data["errors"][0]["line"], 3)
        payment = BankTransaction.objects.get(reference="SPACED")
        self.assertEqual(payment.description, "Valid wire")
