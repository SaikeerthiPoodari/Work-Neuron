from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from apps.accounts.models import User

from .models import ReputationScore
from .serializers import ReputationSerializer
from .services import update_reputation


class MyReputationView(generics.RetrieveAPIView):
    serializer_class = ReputationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return update_reputation(self.request.user)


class UserReputationView(generics.RetrieveAPIView):
    serializer_class = ReputationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = get_object_or_404(User, pk=self.kwargs["user_id"])
        return update_reputation(user)

