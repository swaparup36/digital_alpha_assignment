from django.urls import path

from reconciliation import views


urlpatterns = [
    path("transactions/", views.TransactionListView.as_view(), name="transactions"),
    path("line-items/", views.LineItemListView.as_view(), name="line-items"),
    path("imports/", views.ImportView.as_view(), name="imports"),
    path("matches/<int:match_id>/approve/", views.ApproveView.as_view(), name="approve-match"),
    path("matches/<int:match_id>/reject/", views.RejectView.as_view(), name="reject-match"),
    path("transactions/<int:transaction_id>/ignore/", views.IgnoreView.as_view(), name="ignore-transaction"),
]
