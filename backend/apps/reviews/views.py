from rest_framework import generics, permissions

from .models import Review
from .serializers import ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(reviewer=self.request.user) | Review.objects.filter(reviewed_user=self.request.user)

    def perform_create(self, serializer):
        review = serializer.save()
        from apps.reputation.services import update_reputation
        update_reputation(review.reviewed_user)
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        create_notification(review.reviewed_user, Notification.Kind.REVIEW_RECEIVED, "New review", f"{self.request.user.email} left you a review.", f"/reviews/{review.id}")
