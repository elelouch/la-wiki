from django.urls import path
from . import views
from django.views.generic import RedirectView

app_name = "core"

urlpatterns = [
        path("", views.WikiView.as_view(), name="wiki_read"),
        path("section/<int:root_section_id>/children", views.ChildrenView.as_view(), name="children"),
        path("section/<int:root_section_id>", views.SectionView.as_view(), name="section"), 
        path("section/modal", views.ModalSectionView.as_view(), name="modal_section"), 
        path("file/modal", views.ModalFileView.as_view(), name="modal_file"), 
        path("archive/<str:filename>", views.ArchiveView.as_view(), name="archive"), 
        path("text/markdown", views.MarkdownTextView.as_view(), name="markdown_text"),
        path("search/", views.SearchArchiveView.as_view(), name="search"), 
        ]


