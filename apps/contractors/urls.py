from django.urls import path

from .views import ContractorApplyView, ContractorBiddingView, ContractorReviewListView, ContractorReviewView, MyContractorApplicationsView

app_name = "contractors"
urlpatterns = [path("apply/", ContractorApplyView.as_view(), name="apply"), path("applications/", MyContractorApplicationsView.as_view(), name="mine"), path("review/", ContractorReviewListView.as_view(), name="review"), path("review/<int:pk>/<str:action>/", ContractorReviewView.as_view(), name="review-action"), path("bidding/", ContractorBiddingView.as_view(), name="bidding")]
