from django.urls import path

from .views import VoiceSearchView

urlpatterns = [path("voice/", VoiceSearchView.as_view(), name="voice-search")]
