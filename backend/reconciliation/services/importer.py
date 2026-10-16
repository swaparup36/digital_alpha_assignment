import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction

from reconciliation.models import BankTransaction
from reconciliation.services.matching import suggest_matches


REQUIRED_COLUMNS = {"date", "description", "amount", "type", "reference"}
AMOUNT_PATTERN = re.compile(r"^[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?$")


class InvalidFile(ValueError):
    pass


def parse_row(row):
    if None in row or any(value is None for value in row.values()):
        raise ValueError("Row has missing or extra fields.")
    values = {key: value.strip() for key, value in row.items()}
    try:
        parsed_date = date.fromisoformat(values["date"])
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", values["date"]):
            raise ValueError
    except ValueError:
        raise ValueError("Date must be a real date in YYYY-MM-DD format.") from None
    if not values["description"]:
        raise ValueError("Description is required.")
    if not values["reference"]:
        raise ValueError("Bank reference is required.")
    if not AMOUNT_PATTERN.fullmatch(values["amount"]):
        raise ValueError("Amount must be a valid number with at most two decimal places.")
    try:
        amount = Decimal(values["amount"].replace(",", ""))
    except InvalidOperation:
        raise ValueError("Amount is invalid.") from None
    if not amount or amount.copy_abs() >= Decimal("1000000000000"):
        raise ValueError("Amount must be nonzero and fit within 12 whole digits.")
    bank_type = values["type"].lower()
    if bank_type not in {"credit", "debit"}:
        raise ValueError("Type must be credit or debit.")
    if (bank_type == "credit" and amount < 0) or (bank_type == "debit" and amount > 0):
        raise ValueError("Amount sign does not match transaction type.")
    if len(values["reference"]) > 120:
        raise ValueError("Bank reference is too long.")
    return {
        "date": parsed_date,
        "description": values["description"],
        "amount": amount,
        "type": bank_type,
        "reference": values["reference"],
    }


def import_statement(upload, organization):
    try:
        content = upload.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InvalidFile("CSV must be UTF-8 encoded.") from None
    reader = csv.DictReader(io.StringIO(content, newline=""), strict=True)
    if not reader.fieldnames:
        raise InvalidFile("CSV must have a header row.")
    names = [name.strip() for name in reader.fieldnames]
    missing = sorted(REQUIRED_COLUMNS - set(names))
    if missing:
        raise InvalidFile(f"Missing columns: {', '.join(missing)}.")
    if len(names) != len(set(names)):
        raise InvalidFile("CSV has duplicate column names.")
    reader.fieldnames = names

    summary = {"imported": 0, "duplicates": 0, "errors": []}
    seen = set()
    try:
        for row in reader:
            line = reader.line_num
            try:
                values = parse_row(row)
            except ValueError as exc:
                summary["errors"].append({"line": line, "message": str(exc)})
                continue
            bank_reference = values["reference"]
            if bank_reference in seen:
                summary["duplicates"] += 1
                continue
            seen.add(bank_reference)
            with transaction.atomic():
                payment, created = BankTransaction.objects.get_or_create(
                    organization=organization,
                    reference=bank_reference,
                    defaults={
                        **values,
                        "status": (
                            BankTransaction.Status.IGNORED if values["type"] == "debit"
                            else BankTransaction.Status.NEEDS_REVIEW
                        ),
                        "review_reason": "Outgoing debit." if values["type"] == "debit" else "",
                    },
                )
                if created and values["type"] == "credit":
                    suggest_matches(payment)
            summary["imported" if created else "duplicates"] += 1
    except csv.Error as exc:
        raise InvalidFile(f"Malformed CSV: {exc}.") from exc
    return summary
