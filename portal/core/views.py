# pyright: reportUnknownVariableType=false
from django.db.models.functions import Concat, Lower
from django.http import HttpRequest, HttpResponseNotFound, HttpResponse
from django.views.generic.base import TemplateView
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth import mixins
from django.urls import reverse_lazy
from .forms import SectionForm, FileForm
from typing import final
from django.conf import settings
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .models import PermissionType, Section, Archive

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
        if not root_section.user_has_perm(user, PermissionType.READ):
            return HttpResponse("User does not have read permission", status = 403)

        context = {
                "parent": root_section,
                "sections": root_section.children_available(user),
                "archives": root_section.archives.all(),
            }
        return render(request, self.template_name, context)

# get/post for appending a section to a section
@final
class ModalSectionView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_modal_form.html"
    extra_context = {"form": SectionForm()}
    def post(self, request: HttpRequest): 
        root_section_id = int(request.POST["id"])

        if not root_section_id:
            user = request.user
            root_section_id = user.main_section.id

        root_section = get_object_or_404(Section, pk=root_section_id)

        user = request.user
        user_can_write = root_section.user_has_perm(user, PermissionType.WRITE)
        if not user_can_write:
            return HttpResponse("Unauthorized", status=401)

        name = request.POST["name"]
        if not len(name):
            return HttpResponse("Invalid request", status=400)

        root_section.create_children(name)

        return HttpResponse(
            "success", 
            headers={"HX-Trigger": "new_section_parent_" + str(root_section_id)},
            status = 200
        )
    

class SectionView(mixins.LoginRequiredMixin, TemplateView):
    def delete(self, request, root_section_id): 
        root_section = get_object_or_404(Section, pk=root_section_id)
        user = request.user
        user_can_write = root_section.user_has_perm(user, PermissionType.WRITE)
        if not user_can_write:
            return HttpResponse("Unauthorized", status=401)
        root_section.delete()
        return HttpResponse(
                "Success",
                headers={"HX-Trigger": "deleted_section_parent_" + str(root_section.parent.id)},
                status = 200)

# get/post for appending a file to a section
@final
class ModalFileView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/file_modal_form.html"   
    extra_context = {"form": FileForm()}

    def post(self, request: HttpRequest): 
        root_section_id = int(request.POST["id"])
        if not root_section_id:
            user = request.user
            root_section_id = user.main_section.id
        root_section = get_object_or_404(Section, pk=root_section_id)
        user = request.user
        user_can_write = root_section.user_has_perm(user, PermissionType.WRITE)
        if not user_can_write:
            return HttpResponse("Unauthorized", status=401)

        file = request.FILES["file"] 
        
        if not file: 
            return HttpResponse("File not uploaded", status=400)

        root_section.create_children_archive(file)
        
        return HttpResponse(
            "success", 
            headers={"HX-Trigger": "new_file_parent_" + str(root_section_id)},
            status = 200
        )

@final
class WikiView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/main.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"

@final
class ArchiveView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/archive_view.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"

    @method_decorator(xframe_options_sameorigin)
    def get(self, request: HttpRequest, filename: str):
        name, extension = os.path.splitext(filename)
        arch = Archive.objects.get(name = name, extension = extension)
        return render(request, self.template_name, {"archive": arch, "file": arch.file})

@final
class SearchView(mixins.LoginRequiredMixin, TemplateView):
    def get(self, request):
        search_content = request.GET["content"]
        search_content = str(search_content)

        list_str = "<ul class=\"bg-blue-500 absolute\">"
        if len(search_content) <= 3 :
            list_str += "</ul>"
            return HttpResponse(list_str, status=401)

        found_archives = Archive.objects.filter(fullname__icontains=search_content)

        for archive in found_archives: 
            list_str += "<li>"
            list_str += archive.fullname
            list_str += "</li>"
        list_str += "</ul>"

        return HttpResponse(list_str)
