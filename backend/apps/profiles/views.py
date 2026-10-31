from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser

from apps.accounts.models import User

from .models import ClientProfile, ProfessionalPortfolio, WorkerProfile
from .serializers import ClientProfileSerializer, ProfessionalPortfolioSerializer, WorkerProfileSerializer


class MyProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, *APIView.parser_classes]

    def _profile(self, user):
        if user.role == User.Role.CLIENT:
            return ClientProfile.objects.get_or_create(user=user, defaults={})
        if user.role == User.Role.WORKER:
            profile, created = WorkerProfile.objects.get_or_create(user=user, defaults={})
            if not profile.payout_qr_token:
                from uuid import uuid4
                profile.payout_qr_token = f"WN-{uuid4().hex}"
                profile.save(update_fields=["payout_qr_token", "updated_at"])
            return profile, created
        return None, False

    def _serializer_class(self, user):
        return ClientProfileSerializer if user.role == User.Role.CLIENT else WorkerProfileSerializer

    def get(self, request):
        profile, _ = self._profile(request.user)
        if profile is None:
            return Response({"detail": "Administrators do not have a marketplace profile."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._serializer_class(request.user)(profile, context={"request": request}).data)

    def patch(self, request):
        profile, _ = self._profile(request.user)
        if profile is None:
            return Response({"detail": "Administrators do not have a marketplace profile."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self._serializer_class(request.user)(profile, data=request.data, partial=True, context={"request": request})
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


class ProfessionalPortfolioView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id=None):
        target = request.user if user_id is None else User.objects.filter(pk=user_id, is_active=True).first()
        if target is None or target.role != User.Role.WORKER:
            return Response({"detail": "A worker portfolio could not be found."}, status=status.HTTP_404_NOT_FOUND)
        if target.id != request.user.id and request.user.role == User.Role.CLIENT:
            from apps.applications.models import Application
            if not Application.objects.filter(worker=target, task__owner=request.user).exists():
                return Response({"detail": "You may only view portfolios for workers who applied to your tasks."}, status=status.HTTP_403_FORBIDDEN)
        if target.id != request.user.id and request.user.role not in (User.Role.CLIENT, User.Role.ADMIN):
            return Response({"detail": "You may only view your own portfolio."}, status=status.HTTP_403_FORBIDDEN)
        from .services import refresh_professional_portfolio
        portfolio = refresh_professional_portfolio(target)
        return Response(ProfessionalPortfolioSerializer(portfolio, context={"request": request}).data)
