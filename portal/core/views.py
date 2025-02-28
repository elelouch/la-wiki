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

        if not root_section.user_can_read(user):
            return HttpResponse("User does not have read permission", status = 403)

        children_available = root_section.children_available(user)

        for i in children_available:
            print(i)
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
    extra_context = {"form": SectionForm()}
    def post(self, request: HttpRequest): 
        data = request.POST

        root_section_id = int(data.get("id") or 0)

        if not root_section_id:
            user = request.user
            root_section_id = user.main_section.id

        root_section = get_object_or_404(Section, pk=root_section_id)

        user = request.user
        if not root_section.user_can_write(user):
            return HttpResponse("Unauthorized", status=401)

        name = data.get("name")
        if not name:
            return HttpResponse("Invalid request", status=400)

        root_section.create_children(name)

        return HttpResponse(
            "success", 
            headers={"HX-Trigger": "new_section_parent_" + str(root_section_id)},
            status = 200
        )
    

class SectionView(mixins.LoginRequiredMixin, TemplateView):
    def delete(self, request, root_section_id): 
        user = request.user
        root_section = get_object_or_404(Section, pk=root_section_id)
        if not root_section.user_can_write(user):
            return HttpResponse("Unauthorized", status=401)
        root_section.delete()
        return HttpResponse(
                "Success",
                headers={"HX-Trigger": "deleted_section_parent_" + str(root_section.parent.id)},
                status = 200)

# get/post for appending a file to a section
@final
class ModalArchiveView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/file_modal_form.html"   
    extra_context = {"form": FileForm()}

    def post(self, request: HttpRequest): 
        user = request.user
        data = request.POST
        files = request.FILES

        root_section_id = int(data.get("id") or 0)
        if not root_section_id:
            root_section_id = user.main_section.id

        root_section = get_object_or_404(Section, pk=root_section_id)
        if not root_section.user_can_write(user):
            return HttpResponse("Unauthorized", status=401)

        file = files.get("file")
        
        if not file: 
            return HttpResponse("File not uploaded", status=400)

        root_section.create_children_archive(file)
        
        return HttpResponse(
            "success", 
            headers={"HX-Trigger": "new_archive_parent_" + str(root_section_id)},
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
        return render(request, self.template_name, {"user_can_write": main_section.user_can_write(user)})

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
        archive.file.delete()
        archive.delete()
        return HttpResponse("")



@final
class SearchArchiveView(mixins.LoginRequiredMixin,ListView):
    template_name="core/archive_list.html"
    paginate_by = 15
    model = Archive
    login_url = reverse_lazy("wikiapp:login")

    def get_queryset(self):
        qs = super().get_queryset()
        data = self.request.GET
        search_content = data.get("content")
        if not search_content or len(search_content) <= 2 :
            return []
        return qs.filter(fullname__icontains=search_content)

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
