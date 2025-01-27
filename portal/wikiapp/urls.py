
from django.urls import path
from . import views

app_name = "wikiapp"
urlpatterns = [
        path("index/", views.LoginView.as_view(), name="login")
        ]
