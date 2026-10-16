from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import APIView

from reconciliation.models import BankTransaction, LineItem, Organization
from reconciliation.serializers import LineItemSerializer, TransactionSerializer
from reconciliation.services.actions import Conflict, approve_match, ignore_transaction, reject_match
from reconciliation.services.importer import InvalidFile, import_statement


class OrganizationView(APIView):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        slug = request.headers.get("X-Organization", "").strip()
        if not slug:
            raise ParseError("X-Organization header is required.")
        self.organization = get_object_or_404(Organization, slug=slug)


class TransactionListView(OrganizationView):
    def get(self, request):
        transactions = BankTransaction.objects.filter(organization=self.organization).prefetch_related(
            "matches__line_item__investor", "matches__line_item__capital_call"
        )
        return Response(TransactionSerializer(transactions, many=True).data)


class LineItemListView(OrganizationView):
    def get(self, request):
        items = LineItem.objects.filter(organization=self.organization).select_related(
            "investor", "capital_call"
        ).order_by("capital_call__number", "expected_reference")
        return Response(LineItemSerializer(items, many=True).data)


class ImportView(OrganizationView):
    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            raise ParseError("Choose a CSV file in the file field.")
        try:
            return Response(import_statement(upload, self.organization), status=status.HTTP_201_CREATED)
        except InvalidFile as exc:
            raise ParseError(str(exc)) from exc


class ApproveView(OrganizationView):
    def post(self, request, match_id):
        try:
            approve_match(self.organization, match_id)
        except Conflict as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response({"detail": "Match approved."})


class RejectView(OrganizationView):
    def post(self, request, match_id):
        try:
            reject_match(self.organization, match_id)
        except Conflict as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response({"detail": "Match rejected."})


class IgnoreView(OrganizationView):
    def post(self, request, transaction_id):
        try:
            ignore_transaction(self.organization, transaction_id)
        except Conflict as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response({"detail": "Transaction ignored."})
