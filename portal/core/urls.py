from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
        path("", views.WikiView.as_view(), name="home"),
        path("section/<int:root_section_id>/children", views.SectionView.as_view(), name="section"),
        path("section/<int:root_section_id>/append/section", views.SectionModalView.as_view(), name="section_modal_form"), 
        path("section/<int:root_section_id>/append/file", views.FileModalView.as_view(), name="file_modal_form"),
        ]
