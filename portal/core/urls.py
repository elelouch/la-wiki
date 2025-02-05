from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
        path("", views.WikiView.as_view(), name="home"),
        path("section/<int:section_id>/", views.SectionView.as_view(), name="section"),
        path("modal_section", views.FileModalView.as_view(), name="section"),
        path("modal_file", views.SectionModalView.as_view(), name="section"),
        ]
