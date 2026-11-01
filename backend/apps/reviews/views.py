from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Review
from .serializers import ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Review.objects.select_related("reviewer", "reviewed_user", "assignment__task", "assignment__task__owner")
        if getattr(self.request.user, "role", "") == "WORKER":
            return queryset.filter(reviewed_user=self.request.user, reviewer__role="CLIENT")
        return queryset.filter(reviewer=self.request.user) | queryset.filter(reviewed_user=self.request.user)

    def create(self, request, *args, **kwargs):
        if request.user.role == "WORKER":
            return Response({"detail": "Workers can view reviews they receive but cannot create reviews."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        review = serializer.save()
        if review.reviewed_user.role == "WORKER":
            from apps.profiles.services import refresh_professional_portfolio
            refresh_professional_portfolio(review.reviewed_user)
        from apps.reputation.services import update_reputation
        update_reputation(review.reviewed_user)
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        create_notification(review.reviewed_user, Notification.Kind.REVIEW_RECEIVED, "New review", f"{self.request.user.email} left you a review.", f"/reviews/{review.id}")
