from django.urls import path

from .views import AnalyticsSummaryView, ClientAnalyticsView


urlpatterns = [path("summary/", AnalyticsSummaryView.as_view(), name="analytics-summary"), path("client/", ClientAnalyticsView.as_view(), name="client-analytics")]

