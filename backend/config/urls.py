from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoginView, MeView, PasswordChangeView, PasswordResetConfirmView, PasswordResetRequestView, RegisterView
from config.health import HealthView


urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("admin/", admin.site.urls),
    path("api/auth/register/", RegisterView.as_view(), name="auth-register"),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("api/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/auth/password/", PasswordChangeView.as_view(), name="auth-password"),
    path("api/auth/password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path("api/auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
    path("api/profiles/", include("apps.profiles.urls")),
    path("api/employers/", include("apps.employers.urls")),
    path("api/search/", include("apps.search.urls")),
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
    path("api/admin/", include("apps.administration.urls")),
    path("api/admin/", include("apps.employers.admin_urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/ai/", include("apps.assistant.urls")),
    path("api/messaging/", include("apps.messaging.urls")),
    path("api/network/", include("apps.network.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
