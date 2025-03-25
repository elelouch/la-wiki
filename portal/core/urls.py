from django.urls import path
from . import views
# from django.views.generic import RedirectView

app_name = "core"

urlpatterns = [
        path("", views.WikiView.as_view(), name="wiki_read"),
        path("section", views.ChildrenView.as_view(), name="children"),
        path("section/<int:root_section_id>", views.SectionView.as_view(), name="section"), 
        path("section/modal/<int:root_section_id>", views.ModalSectionView.as_view(), name="modal_section"), 
        path("archive/modal/<int:root_section_id>", views.ModalArchiveView.as_view(), name="modal_archive"), 
        path("archive/<int:archive_id>", views.ArchiveView.as_view(), name="archive"), 
        path("text/markdown", views.MarkdownTextView.as_view(), name="markdown_text"),
        path("search/", views.SearchArchiveView.as_view(), name="search"), 
        path("search-list/", views.SearchArchiveListView.as_view(), name="search-list"), 
        path("search-list/references", views.SearchArchiveListReferencesView.as_view(), name="search_list_references"), 
        path("references/<int:archive_id>", views.ReferencesView.as_view(), name="references"), 
        path("testing/children", views.ChildrenViewTest.as_view(), name="test-children"),
        ]


