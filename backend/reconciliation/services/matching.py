import re

from django.db.models import F

from reconciliation.models import BankTransaction, LineItem, Match


def normalize_reference(value):
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def normalize_name(value):
    words = re.sub(r"[^A-Z0-9]", " ", value.upper()).split()
    if words and words[-1] in {"LLC", "LP", "LTD", "INC"}:
        words.pop()
    return " ".join(words)


def name_in_description(name, description):
    return bool(name and re.search(rf"(?<!\w){re.escape(name)}(?!\w)", description))


def suggest_matches(transaction):
    """Create the import-time snapshot of candidates for one new credit."""
    eligible = list(
        LineItem.objects.filter(
            organization=transaction.organization,
            capital_call__call_date__lte=transaction.date,
            amount_funded__lt=F("amount_called"),
        ).select_related("investor", "capital_call")
    )
    description_ref = normalize_reference(transaction.description)
    bank_ref = normalize_reference(transaction.reference)
    references = [
        item for item in eligible
        if (ref := normalize_reference(item.expected_reference))
        and (ref in description_ref or ref in bank_ref)
    ]

    if references:
        if len(references) == 1 and transaction.amount > references[0].amount_remaining:
            transaction.status = BankTransaction.Status.NEEDS_REVIEW
            transaction.review_reason = (
                f"Reference {references[0].expected_reference} found, but the payment exceeds "
                f"the remaining {references[0].amount_remaining:,.2f}."
            )
            transaction.save(update_fields=["status", "review_reason"])
            return
        candidates = references
        reason_for = lambda item: (
            f"Reference {item.expected_reference} found; payment {transaction.amount:,.2f} "
            f"against remaining {item.amount_remaining:,.2f}."
        )
        review_reason = "Several eligible references were found; choose the correct line item."
    else:
        normalized_description = normalize_name(transaction.description)
        candidates = [
            item for item in eligible
            if transaction.amount == item.amount_remaining
            and name_in_description(normalize_name(item.investor.name), normalized_description)
        ]
        reason_for = lambda item: (
            f"Investor name {item.investor.name} found; amount equals remaining "
            f"{item.amount_remaining:,.2f}."
        )
        review_reason = (
            "Several investor names and amounts match; choose the correct line item."
            if candidates else "No eligible reference or investor name and amount match was found."
        )

    Match.objects.bulk_create([
        Match(
            organization=transaction.organization,
            transaction=transaction,
            line_item=item,
            reason=reason_for(item),
        )
        for item in candidates
    ])
    transaction.status = (
        BankTransaction.Status.SUGGESTED if len(candidates) == 1
        else BankTransaction.Status.NEEDS_REVIEW
    )
    transaction.review_reason = "" if len(candidates) == 1 else review_reason
    transaction.save(update_fields=["status", "review_reason"])
