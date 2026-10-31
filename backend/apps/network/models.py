from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Post(models.Model):
    class Kind(models.TextChoices):
        UPDATE = "UPDATE", "Professional update"
        PROJECT = "PROJECT", "Project"
        ACHIEVEMENT = "ACHIEVEMENT", "Achievement"
        CERTIFICATION = "CERTIFICATION", "Certification"
        OPPORTUNITY = "OPPORTUNITY", "Job opportunity"
        TASK_COMPLETION = "TASK_COMPLETION", "Completed task"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="network_posts")
    kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.UPDATE)
    body = models.TextField(max_length=5000)
    title = models.CharField(max_length=180, blank=True)
    portfolio_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["author", "created_at"])]


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="network_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["post", "user"], name="unique_network_post_like")]


class PostSave(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saves")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_network_posts")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["post", "user"], name="unique_network_post_save")]


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="network_comments")
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["follower", "following"], name="unique_network_follow")]


class Connection(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        DECLINED = "DECLINED", "Declined"

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_connections")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_connections")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["requester", "recipient"], name="unique_network_connection_request")]
        indexes = [models.Index(fields=["recipient", "status"]), models.Index(fields=["requester", "status"])]


class DirectMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="network_sent_messages")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="network_received_messages")
    body = models.TextField(max_length=4000)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["recipient", "read_at"]), models.Index(fields=["sender", "recipient", "created_at"])]
