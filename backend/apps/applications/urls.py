from django.urls import path

from .views import ApplicationComparisonView, ApplicationDecisionView, ApplicationDetailView, ApplicationInviteView, ApplicationListCreateView, ApplicationWithdrawView


urlpatterns = [
    path("tasks/<int:task_id>/comparison/", ApplicationComparisonView.as_view(), name="application-comparison"),
    path("invite/", ApplicationInviteView.as_view(), name="application-invite"),
    path("", ApplicationListCreateView.as_view(), name="application-list-create"),
    path("<int:pk>/", ApplicationDetailView.as_view(), name="application-detail"),
    path("<int:pk>/decide/", ApplicationDecisionView.as_view(), name="application-decide"),
    path("<int:pk>/withdraw/", ApplicationWithdrawView.as_view(), name="application-withdraw"),
]
