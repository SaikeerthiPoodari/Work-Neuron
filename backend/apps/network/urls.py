from django.urls import path

from .views import ConnectionActionView, ConnectionListCreateView, DirectMessageListCreateView, DirectMessageReadView, DiscoverView, FeedView, FollowView, PostActionView, PostCommentView, ProfileOverviewView, SavedPostsView

urlpatterns = [
    path("feed/", FeedView.as_view(), name="network-feed"),
    path("saved/", SavedPostsView.as_view(), name="network-saved"),
    path("discover/", DiscoverView.as_view(), name="network-discover"),
    path("posts/<int:pk>/comments/", PostCommentView.as_view(), name="network-post-comments"),
    path("posts/<int:pk>/<str:action>/", PostActionView.as_view(), name="network-post-action"),
    path("users/<int:user_id>/follow/", FollowView.as_view(), name="network-follow"),
    path("connections/", ConnectionListCreateView.as_view(), name="network-connections"),
    path("connections/<int:pk>/<str:action>/", ConnectionActionView.as_view(), name="network-connection-action"),
    path("direct-messages/", DirectMessageListCreateView.as_view(), name="network-direct-messages"),
    path("direct-messages/<int:pk>/read/", DirectMessageReadView.as_view(), name="network-direct-message-read"),
    path("users/<int:user_id>/profile/", ProfileOverviewView.as_view(), name="network-profile-overview"),
]
