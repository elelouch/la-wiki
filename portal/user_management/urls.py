from django.urls import path
from . import views
# from django.views.generic import RedirectView

app_name = "core"

urlpatterns = [
        path("<int:user_id>", views.ProfileView.as_view(), name="profile_view"),
    ]


