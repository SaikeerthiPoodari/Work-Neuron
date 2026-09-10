from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoginView, RegisterView, MeView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/register/", RegisterView.as_view(), name="auth-register"),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("api/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/profiles/", include("apps.profiles.urls")),
    path("api/skills/", include("apps.skills.urls")),
    path("api/tasks/", include("apps.tasks.urls")),
    path("api/applications/", include("apps.applications.urls")),
    path("api/assignments/", include("apps.assignments.urls")),
    path("api/matching/", include("apps.matching.urls")),
    path("api/recommendations/", include("apps.recommendations.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/reputation/", include("apps.reputation.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/complaints/", include("apps.complaints.urls")),
    path("api/fraud/", include("apps.fraud.urls")),
]
