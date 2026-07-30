from django.urls import path
from .views import TenderListView, TenderCreateView, BidCreateView, AwardCreateView
app_name = "procurement"
urlpatterns = [path("tenders/", TenderListView.as_view(), name="tenders"), path("tenders/create/", TenderCreateView.as_view(), name="tender-create"), path("tenders/<int:pk>/bid/", BidCreateView.as_view(), name="bid"), path("tenders/<int:pk>/award/", AwardCreateView.as_view(), name="award")]
