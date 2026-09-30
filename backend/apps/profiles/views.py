from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User

from .models import ClientProfile, WorkerProfile
from .serializers import ClientProfileSerializer, WorkerProfileSerializer


class MyProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _profile(self, user):
        if user.role == User.Role.CLIENT:
            return ClientProfile.objects.get_or_create(user=user, defaults={})
        if user.role == User.Role.WORKER:
            return WorkerProfile.objects.get_or_create(user=user, defaults={})
        return None, False

    def _serializer_class(self, user):
        return ClientProfileSerializer if user.role == User.Role.CLIENT else WorkerProfileSerializer

    def get(self, request):
        profile, _ = self._profile(request.user)
        if profile is None:
            return Response({"detail": "Administrators do not have a marketplace profile."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._serializer_class(request.user)(profile).data)

    def patch(self, request):
        profile, _ = self._profile(request.user)
        if profile is None:
            return Response({"detail": "Administrators do not have a marketplace profile."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self._serializer_class(request.user)(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        profile, _ = self._profile(request.user)
        if profile is None:
            return Response({"detail": "Administrators do not have a marketplace profile."}, status=status.HTTP_403_FORBIDDEN)
        if request.user.role == User.Role.WORKER:
            fields = ("location", "current_city", "current_area", "current_state", "latitude", "longitude", "preferred_job_location")
        else:
            fields = ("location",)
        for field in fields:
            setattr(profile, field, None if field in ("latitude", "longitude") else "")
        profile.save(update_fields=[*fields, "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
