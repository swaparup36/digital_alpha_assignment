from django.db import transaction
from django.shortcuts import get_object_or_404

from reconciliation.models import BankTransaction, LineItem, Match


class Conflict(Exception):
    pass


@transaction.atomic
def approve_match(organization, match_id):
    match = get_object_or_404(Match, pk=match_id, organization=organization)
    payment = BankTransaction.objects.select_for_update().get(pk=match.transaction_id, organization=organization)
    if payment.status not in {BankTransaction.Status.SUGGESTED, BankTransaction.Status.NEEDS_REVIEW}:
        raise Conflict("This transaction has already been finalized.")
    match = Match.objects.select_for_update().get(pk=match_id, organization=organization)
    if match.status != Match.Status.PROPOSED:
        raise Conflict("This match is no longer proposed.")
    item = LineItem.objects.select_for_update().get(pk=match.line_item_id, organization=organization)
    if payment.amount > item.amount_remaining:
        raise Conflict("Payment exceeds the line item's remaining amount.")
    item.amount_funded += payment.amount
    item.status = (
        LineItem.Status.FUNDED if item.amount_remaining == 0 else LineItem.Status.PARTIAL
    )
    item.save(update_fields=["amount_funded", "status"])
    match.status = Match.Status.APPROVED
    match.save(update_fields=["status"])
    Match.objects.filter(transaction=payment, organization=organization).exclude(pk=match.pk).update(
        status=Match.Status.REJECTED
    )
    payment.status = BankTransaction.Status.RECONCILED
    payment.review_reason = ""
    payment.save(update_fields=["status", "review_reason"])


@transaction.atomic
def reject_match(organization, match_id):
    match = get_object_or_404(Match, pk=match_id, organization=organization)
    payment = BankTransaction.objects.select_for_update().get(pk=match.transaction_id, organization=organization)
    if payment.status in {BankTransaction.Status.RECONCILED, BankTransaction.Status.IGNORED}:
        raise Conflict("This transaction has already been finalized.")
    match = Match.objects.select_for_update().get(pk=match_id, organization=organization)
    if match.status != Match.Status.PROPOSED:
        raise Conflict("This match is no longer proposed.")
    match.status = Match.Status.REJECTED
    match.save(update_fields=["status"])
    if not Match.objects.filter(transaction=payment, status=Match.Status.PROPOSED).exists():
        payment.status = BankTransaction.Status.NEEDS_REVIEW
        payment.review_reason = "All suggested matches were rejected."
        payment.save(update_fields=["status", "review_reason"])


@transaction.atomic
def ignore_transaction(organization, transaction_id):
    payment = get_object_or_404(
        BankTransaction.objects.select_for_update(), pk=transaction_id, organization=organization
    )
    if payment.status == BankTransaction.Status.RECONCILED:
        raise Conflict("A reconciled transaction cannot be ignored.")
    if payment.type != BankTransaction.Type.CREDIT or payment.status == BankTransaction.Status.IGNORED:
        raise Conflict("Only open credits can be ignored.")
    Match.objects.filter(transaction=payment, organization=organization).update(status=Match.Status.REJECTED)
    payment.status = BankTransaction.Status.IGNORED
    payment.review_reason = "Ignored by the GP."
    payment.save(update_fields=["status", "review_reason"])
