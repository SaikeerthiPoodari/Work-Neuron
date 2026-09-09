from django.urls import path

from .views import MySkillDetailView, MySkillsView, SkillDetailView, SkillListCreateView


urlpatterns = [
    path("", SkillListCreateView.as_view(), name="skill-list-create"),
    path("<int:pk>/", SkillDetailView.as_view(), name="skill-detail"),
    path("mine/", MySkillsView.as_view(), name="my-skills"),
    path("mine/<int:pk>/", MySkillDetailView.as_view(), name="my-skill-detail"),
]

