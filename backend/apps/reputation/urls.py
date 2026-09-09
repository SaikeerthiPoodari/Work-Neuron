from django.urls import path

from .views import MyReputationView, UserReputationView


urlpatterns = [
    path("me/", MyReputationView.as_view(), name="my-reputation"),
    path("users/<int:user_id>/", UserReputationView.as_view(), name="user-reputation"),
]

