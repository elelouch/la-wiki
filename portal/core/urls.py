from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
        path("", views.WikiView.as_view(), name="home"),
        path("folder/<int:dir_id>", views.DirectoryView.as_view(), name="folder"),
        ]
