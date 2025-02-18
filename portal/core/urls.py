from django.urls import path
from . import views
from django.views.generic import RedirectView

app_name = "core"

urlpatterns = [
        path("", RedirectView.as_view(pattern_name=("core:wiki_read")), name="wiki_read"),
        path("read/", views.WikiView.as_view(), name="wiki_read"),
        path("section/<int:root_section_id>/<str:mode>/children", views.ChildrenView.as_view(), name="children"),
        path("section/<int:root_section_id>", views.SectionView.as_view(), name="section"), 
        path("section/modal", views.ModalSectionView.as_view(), name="modal_section"), 
        path("section/file/modal", views.ModalFileView.as_view(), name="modal_file"), 
        ]
