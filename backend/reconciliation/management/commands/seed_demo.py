from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from reconciliation.models import CapitalCall, InvestorEntity, LineItem, Organization


DEMO = {
    "northwind": {
        "name": "Northwind Ventures",
        "calls": [
            (1, "2026-03-25", "2026-04-10", [
                ("Haller Capital LLC", "CC-1001", "27500.00"),
                ("Rahul Shah Trust", "CC-1002", "25000.00"),
                ("Patel Family Trust", "CC-1003", "12500.00"),
                ("Meridian Partners LP", "CC-1004", "15000.00"),
                ("Oakridge Holdings LLC", "CC-1005", "15000.00"),
            ]),
            (2, "2026-04-01", "2026-04-20", [
                ("Oakridge Holdings LLC", "CC-1006", "15000.00"),
            ]),
        ],
    },
    "bluebird": {
        "name": "Bluebird Capital",
        "calls": [
            (1, "2026-04-01", "2026-04-15", [
                ("Cedar Grove Fund LP", "CC-2001", "40000.00"),
            ]),
        ],
    },
}


class Command(BaseCommand):
    help = "Create the assessment demo organizations and capital calls without duplicates."

    @transaction.atomic
    def handle(self, *args, **options):
        for slug, data in DEMO.items():
            organization, _ = Organization.objects.get_or_create(slug=slug, defaults={"name": data["name"]})
            for number, call_date, due_date, investors in data["calls"]:
                call, _ = CapitalCall.objects.get_or_create(
                    organization=organization,
                    number=number,
                    defaults={"call_date": date.fromisoformat(call_date), "due_date": date.fromisoformat(due_date)},
                )
                for name, reference, amount in investors:
                    investor, _ = InvestorEntity.objects.get_or_create(organization=organization, name=name)
                    LineItem.objects.get_or_create(
                        organization=organization,
                        capital_call=call,
                        investor=investor,
                        defaults={"expected_reference": reference, "amount_called": Decimal(amount)},
                    )
        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
