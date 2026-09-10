import os

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.mail import send_mail

from .models import Notification


def create_notification(recipient, kind, title, message, related_url=""):
    notification = Notification.objects.create(
        recipient=recipient,
        kind=kind,
        title=title,
        message=message,
        related_url=related_url,
    )
    payload = {
        "id": notification.id,
        "kind": notification.kind,
        "title": notification.title,
        "message": notification.message,
        "related_url": notification.related_url,
        "read_at": None,
        "created_at": notification.created_at.isoformat(),
    }
    channel_layer = get_channel_layer()
    if channel_layer:
        try:
            async_to_sync(channel_layer.group_send)(f"user_{recipient.id}", {"type": "notification.message", "notification": payload})
        except Exception:
            # Persistence remains successful even if a transient WebSocket layer is unavailable.
            pass
    if os.getenv("NOTIFICATIONS_SEND_EMAIL", "False").lower() in {"1", "true", "yes"}:
        try:
            send_mail(notification.title, notification.message, None, [recipient.email], fail_silently=True)
        except Exception:
            pass
    return notification

