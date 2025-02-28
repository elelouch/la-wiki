
from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView
from . import views

app_name = "wikiapp"

urlpatterns = [
        path("login/", views.LoginView.as_view(), name="login"),
        path("home/", views.HomeView.as_view(), name="home"),
        path("", RedirectView.as_view(url=reverse_lazy("wikiapp:home"))),
        path("logout/", views.LogoutView.as_view(), name="logout"),
        ]
