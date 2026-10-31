from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="admin_audit_events")
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80)
    target_id = models.CharField(max_length=80)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at"]), models.Index(fields=["target_type", "target_id"])]


def record_audit_event(request, action, target, metadata=None):
    return AuditEvent.objects.create(
        actor=request.user,
        action=action,
        target_type=target.__class__.__name__,
        target_id=str(target.pk),
        metadata=metadata or {},
        ip_address=request.META.get("REMOTE_ADDR"),
    )
