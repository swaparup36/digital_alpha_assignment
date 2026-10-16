from rest_framework import serializers

from reconciliation.models import BankTransaction, LineItem, Match


class MatchSerializer(serializers.ModelSerializer):
    investor_name = serializers.CharField(source="line_item.investor.name", read_only=True)
    expected_reference = serializers.CharField(source="line_item.expected_reference", read_only=True)
    capital_call_number = serializers.IntegerField(source="line_item.capital_call.number", read_only=True)

    class Meta:
        model = Match
        fields = ["id", "status", "reason", "line_item", "investor_name", "expected_reference", "capital_call_number"]


class TransactionSerializer(serializers.ModelSerializer):
    matches = MatchSerializer(many=True, read_only=True)

    class Meta:
        model = BankTransaction
        fields = ["id", "date", "description", "amount", "type", "reference", "status", "review_reason", "matches"]


class LineItemSerializer(serializers.ModelSerializer):
    investor_name = serializers.CharField(source="investor.name", read_only=True)
    capital_call_number = serializers.IntegerField(source="capital_call.number", read_only=True)
    call_date = serializers.DateField(source="capital_call.call_date", read_only=True)
    due_date = serializers.DateField(source="capital_call.due_date", read_only=True)
    amount_remaining = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = LineItem
        fields = [
            "id", "investor_name", "expected_reference", "capital_call_number", "call_date",
            "due_date", "amount_called", "amount_funded", "amount_remaining", "status",
        ]
