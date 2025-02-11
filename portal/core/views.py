# pyright: reportUnknownVariableType=false
from django.http import HttpRequest, HttpResponseNotFound, HttpResponse
from django.views.generic.base import TemplateView
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import mixins
from django.db.models import Q
from django.urls import reverse_lazy
from .forms import SectionForm, FileForm
from typing import override, final

from .models import PermissionType, Section

@final
class ChildrenView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_view.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"

    @override
    def get(self, request, root_section_id: int, mode:str):
        assert self.template_name is not None
        user = request.user

        if mode not in [perm.value for perm in PermissionType]:
            return HttpResponseNotFound("Not valid permission mode")

        if not root_section_id:
            return HttpResponseNotFound("Section not found")
        root_section = get_object_or_404(Section, pk=root_section_id)
        sections = root_section.children \
                .filter(
                        Q(access_lists__group__user = user) | Q(access_lists__user = user),
                        access_lists__can_read = True)

        if mode == PermissionType.WRITE:
            sections = sections.filter(access_lists__can_write=True)

        archives = root_section.archives.all()

        context = {
                "root_section": root_section,
                "sections": sections,
                "archives": archives,
                "mode": mode
                }

        return render(request, self.template_name, context)

# get/post for appending a section to a section
@final
class ModalSectionView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_modal_form.html"
    extra_context = {"form": SectionForm()}

    def post(self, request: HttpRequest, root_section_id: int): 
        root_section = get_object_or_404(Section, pk=root_section_id)

        user = request.user
        user_can_write = root_section.user_has_perm(user, 'write')

        if not user_can_write:
            return HttpResponse("Unauthorized", status=401)

        new_sec = root_section.children.create(name = request.POST["name"])

        # inherits permissions
        new_sec.access_lists.add(*root_section.access_lists.all())

        return HttpResponse("success", 
                            headers={
                                "HX-Trigger": "newSection_root_" + str(root_section_id)
                                },
                            status = 200)


class SectionView(mixins.LoginRequiredMixin, TemplateView):
    def delete(self, request, root_section_id): 
        root_section = get_object_or_404(Section, pk=root_section_id)

        user = request.user
        user_can_write = root_section.user_has_perm(user, 'write')

        if not user_can_write:
            return HttpResponse("Unauthorized", status=401)

        parent_id = root_section.parent.id
        root_section.delete()

        return HttpResponse("success", 
                            headers={
                                "HX-Trigger": "deletedSection_root_" + str(parent_id)
                                },
                            status = 200)

# get/post for appending a file to a section
@final
class ModalFileView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/file_modal_form.html"   
    extra_context = {"form": FileForm()}

    def post(self, request, root_section_id): 
        return render(self, self.template_name)


@final
class WikiViewRead (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/main.html"
    login_url = reverse_lazy("wikiapp:login")
    extra_context = {"mode": PermissionType.READ.value}
    redirect_field_name="login"


@final
class WikiViewWrite (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/main.html"
    login_url = reverse_lazy("wikiapp:login")
    extra_context = {"mode": PermissionType.WRITE.value}
    redirect_field_name="login"
