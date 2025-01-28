
from django.urls import path
from . import views

app_name = "wikiapp"
urlpatterns = [
        path("login/", views.LoginView.as_view(), name="login"),
        path("home/", views.HomeView.as_view(), name="home")
        ]
