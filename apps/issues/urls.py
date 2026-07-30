from django.urls import path

from .views import (
    IssueReportView,
    IssueSubmittedView,
    PublicIssueTrackingView,
    PublicTrackingLookupView,
)

app_name = "issues"

urlpatterns = [
    path("report/", IssueReportView.as_view(), name="report"),
    path(
        "report/submitted/<str:reference>/<str:token>/",
        IssueSubmittedView.as_view(),
        name="submitted",
    ),
    path("track/", PublicTrackingLookupView.as_view(), name="track-lookup"),
    path(
        "track/<str:reference>/<str:token>/",
        PublicIssueTrackingView.as_view(),
        name="track",
    ),
]
