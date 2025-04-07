from django.urls import path
from . import views
# from django.views.generic import RedirectView

app_name = "core"

urlpatterns = [
        path("", views.WikiView.as_view(), name="wiki_read"),
    ]


