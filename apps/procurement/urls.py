from django.urls import path
from .views import TenderListView, TenderCreateView, BidCreateView
app_name = "procurement"
urlpatterns = [path("tenders/", TenderListView.as_view(), name="tenders"), path("tenders/create/", TenderCreateView.as_view(), name="tender-create"), path("tenders/<int:pk>/bid/", BidCreateView.as_view(), name="bid")]
