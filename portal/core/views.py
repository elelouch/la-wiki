# pyright: reportUnknownVariableType=false
from django.http import HttpRequest, HttpResponseNotFound, HttpResponse
from django.views.generic.base import TemplateView
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import mixins
from django.db.models import Q
from django.urls import reverse_lazy
from .forms import SectionForm, FileForm
from typing import final
from django.conf import settings
import os

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
        sections = root_section.children \
                .filter(
                        Q(access_lists__group__user = user) | Q(access_lists__user = user),
                        access_lists__can_read = True)
        archives = root_section.archives.all()
        context = {
                "parent": root_section,
                "sections": sections,
                "archives": archives,
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
        new_sec = root_section.children.create(name = request.POST["name"])
        # inherits permissions
        new_sec.access_lists.add(*root_section.access_lists.all())
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
        filename, extension = os.path.splitext(file.name)
        arch = root_section.archives.create(
                extension = extension,
                name = filename,
                file = file
                )
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

    def get(self, request: HttpRequest, file_id: int):
        arch = Archive.objects.get(pk=file_id)
        return render(request, self.template_name, {arch: arch})
