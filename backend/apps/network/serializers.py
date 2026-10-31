from django.db.models import Q
from rest_framework import serializers

from apps.accounts.models import User

from .models import Connection, DirectMessage, Follow, Post, PostComment


def display_name(user):
    return " ".join(part for part in (user.first_name, user.last_name) if part).strip() or user.email


class NetworkUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    headline = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    followers_count = serializers.IntegerField(source="followers.count", read_only=True)
    following_count = serializers.IntegerField(source="following.count", read_only=True)
    connections_count = serializers.SerializerMethodField()
    mutual_connections = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "name", "role", "headline", "location", "followers_count", "following_count", "connections_count", "mutual_connections")

    def get_name(self, obj): return display_name(obj)

    def get_headline(self, obj):
        profile = getattr(obj, "worker_profile", None) or getattr(obj, "client_profile", None)
        return getattr(profile, "headline", "") or getattr(profile, "organization_name", "")

    def get_location(self, obj):
        profile = getattr(obj, "worker_profile", None) or getattr(obj, "client_profile", None)
        return getattr(profile, "location", "") or getattr(profile, "current_city", "")

    def get_connections_count(self, obj):
        return Connection.objects.filter(status=Connection.Status.ACCEPTED).filter(requester=obj).count() + Connection.objects.filter(status=Connection.Status.ACCEPTED, recipient=obj).count()

    def get_mutual_connections(self, obj):
        current = self.context.get("request").user if self.context.get("request") else None
        if not current or current.id == obj.id:
            return []
        def peers(user):
            sent = Connection.objects.filter(requester=user, status=Connection.Status.ACCEPTED).values_list("recipient_id", flat=True)
            received = Connection.objects.filter(recipient=user, status=Connection.Status.ACCEPTED).values_list("requester_id", flat=True)
            return set(sent) | set(received)
        shared = list(peers(current) & peers(obj))[:5]
        users = User.objects.filter(id__in=shared)
        return [{"id": item.id, "name": display_name(item)} for item in users]


class PostCommentSerializer(serializers.ModelSerializer):
    author = NetworkUserSerializer(read_only=True)

    class Meta:
        model = PostComment
        fields = ("id", "author", "body", "created_at")
        read_only_fields = ("id", "author", "created_at")


class PostSerializer(serializers.ModelSerializer):
    author = NetworkUserSerializer(read_only=True)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)
    comments_count = serializers.IntegerField(source="comments.count", read_only=True)
    saves_count = serializers.IntegerField(source="saves.count", read_only=True)
    liked = serializers.SerializerMethodField()
    saved = serializers.SerializerMethodField()
    comments = PostCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ("id", "author", "kind", "title", "body", "portfolio_url", "created_at", "updated_at", "likes_count", "comments_count", "saves_count", "liked", "saved", "comments")
        read_only_fields = ("id", "author", "created_at", "updated_at", "likes_count", "comments_count", "saves_count", "liked", "saved", "comments")

    def get_liked(self, obj): return obj.likes.filter(user=self.context["request"].user).exists()
    def get_saved(self, obj): return obj.saves.filter(user=self.context["request"].user).exists()


class ConnectionSerializer(serializers.ModelSerializer):
    requester = NetworkUserSerializer(read_only=True)
    recipient = NetworkUserSerializer(read_only=True)

    class Meta:
        model = Connection
        fields = ("id", "requester", "recipient", "status", "created_at", "updated_at")
        read_only_fields = fields


class FollowSerializer(serializers.ModelSerializer):
    following = NetworkUserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ("id", "following", "created_at")
        read_only_fields = fields


class DirectMessageSerializer(serializers.ModelSerializer):
    sender = NetworkUserSerializer(read_only=True)
    recipient = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True))

    class Meta:
        model = DirectMessage
        fields = ("id", "sender", "recipient", "body", "read_at", "created_at")
        read_only_fields = ("id", "sender", "read_at", "created_at")

    def validate(self, attrs):
        request = self.context["request"]
        recipient = attrs["recipient"]
        if recipient.id == request.user.id:
            raise serializers.ValidationError("You cannot message yourself.")
        connected = Connection.objects.filter(status=Connection.Status.ACCEPTED).filter(Q(requester=request.user, recipient=recipient) | Q(requester=recipient, recipient=request.user)).exists()
        if not connected:
            raise serializers.ValidationError("You can only message accepted connections.")
        return attrs
