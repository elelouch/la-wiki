from django.urls import path
from . import views
# from django.views.generic import RedirectView

app_name = "core"

urlpatterns = [
    path("", views.WikiView.as_view(), name="wiki_read"),
    path("section", views.ChildrenView.as_view(), name="children"),
    path("section/<int:root_section_id>", views.SectionView.as_view(), name="section"), 
    path("section/", views.CreateSectionView.as_view(), name="create_section"), 
    path("section/<int:root_id>/modal", views.ModalSectionView.as_view(), name="modal_section"), 
    path("archive/<int:root_id>/modal", views.ModalArchiveView.as_view(), name="modal_archive"), 
    path("archive/<int:archive_id>", views.ArchiveView.as_view(), name="archive"), 
    path("archive/", views.CreateArchiveView.as_view(), name="create_archive"), 
    path("text/markdown", views.MarkdownView.as_view(), name="markdown_text"),
    path("search/", views.SearchArchiveView.as_view(), name="search"), 
    path("search-list/", views.SearchArchiveListView.as_view(), name="search-list"), 
    path("search-list/references", views.SearchArchiveListReferencesView.as_view(), name="search_list_references"), 
    path("references/<int:archive_id>", views.ReferencesView.as_view(), name="references"), 
]
