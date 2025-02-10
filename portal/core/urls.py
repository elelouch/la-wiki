from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
        path("", views.WikiView.as_view(), name="home"),
        path("section/<int:root_section_id>/section/children", views.ChildrenView.as_view(), name="children"),
        path("section/<int:root_section_id>/section", views.SectionView.as_view(), name="section"), 
        #path("section/<int:root_section_id>/file", views.FileView.as_view(), name="file"),
        path("section/<int:root_section_id>/section/modal", views.ModalSectionView.as_view(), name="modal_section"), 
        path("section/<int:root_section_id>/file/modal", views.ModalFileView.as_view(), name="modal_file"), 
        ]
