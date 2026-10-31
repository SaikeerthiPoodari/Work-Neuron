from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.employers.models import EmployerVerification
from apps.employers.serializers import EmployerVerificationSerializer
from apps.profiles.models import ClientProfile, WorkerProfile
from apps.profiles.serializers import ClientProfileSerializer, WorkerProfileSerializer

from django.utils import timezone

from .models import Connection, DirectMessage, Follow, Post, PostComment, PostLike, PostSave
from .serializers import ConnectionSerializer, DirectMessageSerializer, FollowSerializer, NetworkUserSerializer, PostCommentSerializer, PostSerializer


class FeedView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()
        queryset = Post.objects.select_related("author", "author__worker_profile", "author__client_profile").prefetch_related("likes", "saves", "comments__author")
        if query:
            queryset = queryset.filter(Q(body__icontains=query) | Q(title__icontains=query) | Q(author__first_name__icontains=query) | Q(author__last_name__icontains=query))
        if self.request.query_params.get("author"):
            queryset = queryset.filter(author_id=self.request.query_params["author"])
        return queryset

    def perform_create(self, serializer): serializer.save(author=self.request.user)


class PostActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, action):
        post = get_object_or_404(Post, pk=pk)
        if action == "like":
            item, created = PostLike.objects.get_or_create(post=post, user=request.user)
            if not created: item.delete()
            return Response({"liked": created, "likes_count": post.likes.count()})
        if action == "save":
            item, created = PostSave.objects.get_or_create(post=post, user=request.user)
            if not created: item.delete()
            return Response({"saved": created, "saves_count": post.saves.count()})
        if action == "share":
            create_notification(post.author, Notification.Kind.MESSAGE_RECEIVED, "Your post was shared", f"{request.user.email} shared your professional post.", "/feed")
            return Response({"shared": True})
        return Response({"detail": "Unsupported post action."}, status=status.HTTP_400_BAD_REQUEST)


class PostCommentView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostCommentSerializer

    def get_queryset(self): return PostComment.objects.filter(post_id=self.kwargs["pk"]).select_related("author")
    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs["pk"])
        comment = serializer.save(post=post, author=self.request.user)
        if post.author_id != self.request.user.id: create_notification(post.author, Notification.Kind.MESSAGE_RECEIVED, "New comment", f"{self.request.user.email} commented on your post.", "/feed")


class DiscoverView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NetworkUserSerializer

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True).exclude(id=self.request.user.id).select_related("worker_profile", "client_profile")
        query = self.request.query_params.get("q", "").strip()
        role = self.request.query_params.get("role", "").upper()
        if query: queryset = queryset.filter(Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(worker_profile__headline__icontains=query) | Q(worker_profile__location__icontains=query) | Q(client_profile__organization_name__icontains=query) | Q(client_profile__location__icontains=query))
        if role in User.Role.values: queryset = queryset.filter(role=role)
        return queryset.order_by("first_name", "last_name")[:100]


class FollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        target = get_object_or_404(User, pk=user_id, is_active=True)
        if target == request.user: return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)
        item, created = Follow.objects.get_or_create(follower=request.user, following=target)
        if not created: item.delete()
        return Response({"following": created})


class ConnectionListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConnectionSerializer

    def get_queryset(self): return Connection.objects.filter(Q(requester=self.request.user) | Q(recipient=self.request.user)).select_related("requester", "recipient")

    def create(self, request, *args, **kwargs):
        target = get_object_or_404(User, pk=request.data.get("user_id"), is_active=True)
        if target == request.user: return Response({"detail": "You cannot connect with yourself."}, status=status.HTTP_400_BAD_REQUEST)
        item, created = Connection.objects.get_or_create(requester=request.user, recipient=target, defaults={"status": Connection.Status.PENDING})
        if not created and item.status == Connection.Status.DECLINED: item.status = Connection.Status.PENDING; item.save(update_fields=["status", "updated_at"])
        if not created and item.status != Connection.Status.PENDING: return Response(ConnectionSerializer(item, context={"request": request}).data)
        create_notification(target, Notification.Kind.MESSAGE_RECEIVED, "New connection request", f"{request.user.email} wants to connect with you.", "/discover")
        return Response(ConnectionSerializer(item, context={"request": request}).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ConnectionActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, action):
        connection = get_object_or_404(Connection, pk=pk)
        if action in {"accept", "decline"}:
            if connection.recipient_id != request.user.id: return Response({"detail": "Only the recipient can respond."}, status=status.HTTP_403_FORBIDDEN)
            connection.status = Connection.Status.ACCEPTED if action == "accept" else Connection.Status.DECLINED
            connection.save(update_fields=["status", "updated_at"])
            if action == "accept":
                create_notification(connection.requester, Notification.Kind.MESSAGE_RECEIVED, "Connection accepted", f"{request.user.email} accepted your connection request.", "/discover")
            return Response(ConnectionSerializer(connection, context={"request": request}).data)
        if action == "remove" and request.user.id in (connection.requester_id, connection.recipient_id):
            connection.delete(); return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Unsupported connection action."}, status=status.HTTP_400_BAD_REQUEST)


class DirectMessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DirectMessageSerializer

    def get_queryset(self):
        queryset = DirectMessage.objects.filter(Q(sender=self.request.user) | Q(recipient=self.request.user)).select_related("sender", "recipient")
        user_id = self.request.query_params.get("user")
        if user_id: queryset = queryset.filter(Q(sender_id=user_id) | Q(recipient_id=user_id))
        if self.request.query_params.get("unread") in {"1", "true", "True"}: queryset = queryset.filter(recipient=self.request.user, read_at__isnull=True)
        return queryset

    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)
        create_notification(message.recipient, Notification.Kind.MESSAGE_RECEIVED, "New direct message", f"{self.request.user.email} sent you a message.", "/network-messages")


class DirectMessageReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        message = get_object_or_404(DirectMessage, pk=pk)
        if message.recipient_id != request.user.id: return Response({"detail": "Only the recipient can mark this message as read."}, status=status.HTTP_403_FORBIDDEN)
        if message.read_at is None: message.read_at = timezone.now(); message.save(update_fields=["read_at"])
        return Response(DirectMessageSerializer(message, context={"request": request}).data)


class ProfileOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User.objects.select_related("worker_profile", "client_profile"), pk=user_id, is_active=True)
        profile = getattr(user, "worker_profile", None) or getattr(user, "client_profile", None)
        profile_data = None
        if isinstance(profile, WorkerProfile): profile_data = WorkerProfileSerializer(profile, context={"request": request}).data
        if isinstance(profile, ClientProfile): profile_data = ClientProfileSerializer(profile, context={"request": request}).data
        accepted = Connection.objects.filter(status=Connection.Status.ACCEPTED).filter(Q(requester=user) | Q(recipient=user)).select_related("requester", "recipient")
        connections = [item.recipient if item.requester_id == user.id else item.requester for item in accepted]
        followers = User.objects.filter(following__following=user, is_active=True).select_related("worker_profile", "client_profile")
        following = User.objects.filter(followers__follower=user, is_active=True).select_related("worker_profile", "client_profile")
        verification = EmployerVerification.objects.filter(employer=user).first()
        posts = Post.objects.filter(author=user).select_related("author").prefetch_related("likes", "saves", "comments__author")[:50]
        return Response({
            "user": NetworkUserSerializer(user, context={"request": request}).data,
            "profile": profile_data,
            "followers": NetworkUserSerializer(followers, many=True, context={"request": request}).data,
            "following": NetworkUserSerializer(following, many=True, context={"request": request}).data,
            "connections": NetworkUserSerializer(connections, many=True, context={"request": request}).data,
            "posts": PostSerializer(posts, many=True, context={"request": request}).data,
            "verification": EmployerVerificationSerializer(verification).data if verification else None,
        })
