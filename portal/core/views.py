# pyright: reportUnknownVariableType=false
from django.db.models.functions import Concat, Lower
from django.http import HttpRequest, HttpResponseNotFound, HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth import mixins
from django.urls import reverse_lazy
from django.conf import settings
from .forms import MarkdownForm, SectionForm, FileForm
from typing import final
from django.core.files import File
from django.core.files.base import ContentFile
import os
from django.views.decorators.clickjacking import xframe_options_sameorigin
import markdown as markdown_tool

from .models import Section, Archive

@final
class ChildrenView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_view.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name = "login"

    def get(self, request: HttpRequest, root_section_id: int):
        assert self.template_name is not None
        user = request.user
        if not root_section_id:
            return HttpResponse("Root section must be an integer", status=400)
        root_section = get_object_or_404(Section, pk=root_section_id)

        children_available = root_section.children_available(user)

        context = {
                "parent": root_section,
                "sections": children_available,
                "archives": root_section.archives.all(),
            }
        return render(request, self.template_name, context)

# get/post for appending a section to a section
@final
class ModalSectionView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_modal_form.html"
    def get(self, request: HttpRequest, root_section_id: int):
        return render(request, self.template_name, {
            "root_id": root_section_id,
            "form": SectionForm()
            })
    

class SectionView(mixins.LoginRequiredMixin, TemplateView):
    template_section_item = "core/section_item.html"
    def delete(self, request: HttpRequest, root_section_id: int): 
        user = request.user
        root_section = get_object_or_404(Section, pk=root_section_id)
        parent_id = root_section.parent.id
        root_section.delete()
        return HttpResponse("")
    
    def post(self, request: HttpRequest, root_section_id: int): 
        data = request.POST

        if not root_section_id:
            user = request.user
            root_section_id = user.main_section.id
        root_section = get_object_or_404(Section, pk=root_section_id)
        user = request.user
        name = data.get("name")
        if not name:
            return HttpResponse("Invalid request", status=400)
        new_child = root_section.create_children(name)
        return render(
                request,
                self.template_section_item,
                {
                    "sec": new_child,
                    "root": root_section
                }
           ) 

# get/post for appending a file to a section
@final
class ModalArchiveView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/file_modal_form.html"   
    extra_context = {"form": FileForm()}

    def post(self, request: HttpRequest, root_section_id: int): 
        user = request.user
        files = request.FILES
        if not root_section_id:
            root_section_id = user.main_section.id
        root_section = get_object_or_404(Section, pk=root_section_id)
        file = files.get("file")
        if not file: 
            return HttpResponse("File not uploaded", status=400)
        root_section.create_children_archive(file)
        return HttpResponse(
            "success", 
            headers={"HX-Trigger": "archive_parent_" + str(root_section_id)},
            status = 200
        )

@final
class WikiView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/main.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"

    def get(self, request):
        user = request.user
        main_section = user.main_section
        return render(request, self.template_name)

@final
class ArchiveView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/archive_view.html"
    markdown_template = "core/markdown_view.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"

    @method_decorator(xframe_options_sameorigin)
    def get(self, request: HttpRequest, filename: str):
        name, extension = os.path.splitext(filename)
        arch = get_object_or_404(Archive, name = name, extension = extension)
        if "md" in extension :
            text = arch.file.read()
            html = markdown_tool.markdown(text.decode("ascii"))
            return render(request, self.markdown_template, {"archive": arch, "file": html})
        return render(request, self.template_name, {"archive": arch, "file": arch.file})

    def delete(self, request: HttpRequest, filename: str):
        name, extension = os.path.splitext(filename)

        archive = get_object_or_404(Archive, name = name, extension = extension)
        root_id = archive.section.id
        archive.file.delete()
        archive.delete()
        response = HttpResponse("")
        response["archive_parent_" + root_id]
        return response



@final
class SearchArchiveView(mixins.LoginRequiredMixin,ListView):
    template_name="core/archive_list.html"
    paginate_by = 15
    model = Archive
    login_url = reverse_lazy("wikiapp:login")

    def get_queryset(self):
        qs = super().get_queryset()
        data = self.request.GET
        user = self.request.user

        search_content = data.get("content")
        if not search_content or len(search_content) <= 2 :
            return []

        ilike_content = "%{content}%".format(content=search_content)
        return qs.raw(
                """
                WITH RECURSIVE ancestors AS (
                    SELECT *
                    FROM core_section s 
                    WHERE s.id = %s
                    UNION ALL
                    SELECT cs.*
                    FROM core_section cs, ancestors a 
                    WHERE cs.parent_id = a.id
                    AND cs.id NOT IN (
                        SELECT nacc.section_id 
                        FROM core_negativeaccess nacc
                        WHERE nacc.user_id = %s
                    )
                ) SELECT * FROM ancestors
                INNER JOIN core_archive arch
                ON ancestors.id = arch.section_id
                WHERE arch.fullname LIKE %s;
                """, [user.main_section.id, user.id, ilike_content])


@final
class MarkdownTextView(mixins.LoginRequiredMixin,TemplateView):
    template_name="core/markdown_form.html"
    extra_context = {"form": MarkdownForm()}
    login_url = reverse_lazy("wikiapp:login")

    def post(self,request):
        data = request.POST
        markdown_ext = ".md"

        root_section_id = int(data.get("root_id") or 0)
        filename = data.get("name")
        file_content = data.get("file")
        if not file_content :
            return HttpResponse("No files provided", status = 400)
        if not filename:
            return HttpResponse("No name provided", status = 400)

        user = request.user
        root_section = user.main_section if not root_section_id else get_object_or_404(Section, pk=root_section_id)

        # add markdown suffix
        fullname = filename + markdown_ext

        with ContentFile(file_content, name=fullname) as content_file:
            new_archive = Archive(
                    fullname = fullname,
                    name = filename,
                    extension = markdown_ext,
                    file=content_file,
                    section = root_section
                    ) 
            new_archive.save()

        return HttpResponse("Markdown text success", status = 200)
