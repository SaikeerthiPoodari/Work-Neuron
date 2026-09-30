from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmployerVerification, VerificationDocument
from .permissions import IsAdmin, IsEmployer
from .serializers import EmployerVerificationSerializer, VerificationDocumentSerializer


class EmployerVerificationView(APIView):
    permission_classes = [IsEmployer]

    def get_object(self):
        return EmployerVerification.objects.filter(employer=self.request.user).first()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response({"status": EmployerVerification.Status.UNVERIFIED, "detail": "No verification request has been submitted."})
        return Response(EmployerVerificationSerializer(instance).data)

    def post(self, request, *args, **kwargs):
        if self.get_object() is not None:
            return Response({"detail": "A verification request already exists. Use PATCH to resubmit it."}, status=status.HTTP_409_CONFLICT)
        serializer = EmployerVerificationSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(EmployerVerificationSerializer(serializer.save()).data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response({"detail": "Submit a verification request before updating it."}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmployerVerificationSerializer(instance, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(EmployerVerificationSerializer(serializer.save()).data)


class VerificationDocumentCreateView(generics.CreateAPIView):
    serializer_class = VerificationDocumentSerializer
    permission_classes = [IsEmployer]
    parser_classes = [MultiPartParser, FormParser]
    throttle_scope = "sensitive"

    def perform_create(self, serializer):
        verification = get_object_or_404(EmployerVerification, employer=self.request.user)
        if verification.status == EmployerVerification.Status.VERIFIED:
            raise serializers.ValidationError("Documents cannot be changed after verification.")
        serializer.save(verification=verification)


class AdminVerificationListView(generics.ListAPIView):
    serializer_class = EmployerVerificationSerializer
    permission_classes = [IsAdmin]
    queryset = EmployerVerification.objects.select_related("employer", "reviewed_by").prefetch_related("documents")

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get("status"):
            queryset = queryset.filter(status=self.request.query_params["status"])
        return queryset


class AdminVerificationActionView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        verification = get_object_or_404(EmployerVerification, pk=pk)
        action = request.data.get("action")
        allowed = {"approve": EmployerVerification.Status.VERIFIED, "reject": EmployerVerification.Status.REJECTED, "suspend": EmployerVerification.Status.SUSPENDED}
        if action not in allowed:
            return Response({"detail": "Action must be approve, reject, or suspend."}, status=status.HTTP_400_BAD_REQUEST)
        verification.status = allowed[action]
        verification.admin_notes = str(request.data.get("admin_notes", "")).strip()
        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.save(update_fields=["status", "admin_notes", "reviewed_by", "reviewed_at", "updated_at"])
        return Response(EmployerVerificationSerializer(verification).data)


class AdminVerificationDocumentView(generics.RetrieveAPIView):
    serializer_class = VerificationDocumentSerializer
    permission_classes = [IsAdmin]
    queryset = VerificationDocument.objects.select_related("verification", "verification__employer")
