from django.urls import path
from . import views

app_name = "core"
urlpatterns = [
        path("folder/<int:dir_id>", views.DirectoryView.as_view(), name="folder")
        ]
