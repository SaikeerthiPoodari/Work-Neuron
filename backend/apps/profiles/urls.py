from django.urls import path

from .views import MyProfileView, ProfessionalPortfolioView


urlpatterns = [path("me/", MyProfileView.as_view(), name="my-profile"), path("portfolio/", ProfessionalPortfolioView.as_view(), name="my-portfolio"), path("portfolio/<int:user_id>/", ProfessionalPortfolioView.as_view(), name="worker-portfolio")]

