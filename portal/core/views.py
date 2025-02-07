# pyright: reportUnknownVariableType=false
from django.http import Http404, HttpResponseNotFound, HttpResponse
from django.views.generic.base import TemplateView
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import mixins
from django.db.models import Q
from django.urls import reverse_lazy
from core.forms import SectionForm, FileForm
from typing import override

from .models import Section, Archive

class SectionView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_view.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"

    @override
    def get(self, request, root_section_id):
        assert self.template_name is not None
        user = request.user
        if not root_section_id:
            return HttpResponseNotFound("Section not found")

        root_section = get_object_or_404(Section, pk=root_section_id)
        sections = root_section.sections \
                .filter(
                        Q(access_lists__groups__user__id = user.id) | Q(access_lists__user__id = user.id),
                        access_lists__can_read = True)

        archives = root_section.archives.all()

        context = {
                "root_section": root_section,
                "sections": sections,
                "archives": archives
                }

        return render(request, self.template_name, context)

# get/post for appending a section to a section
class SectionModalView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_modal_form.html"
    extra_context = {"form": SectionForm()}

    def post(self, request, root_section_id): 
        root_section = get_object_or_404(Section, pk=root_section_id)

        user = request.user
        user_can_write = root_section.user_has_perm(user, 'write')

        if not user_can_write:
            return HttpResponse("Unauthorized", status=401)

        new_sec = root_section.sections.create(name = request.POST["name"])

        # inherits permissions
        new_sec.access_lists.add(*root_section.access_lists.all())

        return HttpResponse("success", 
                            headers={
                                "HX-Trigger": "newSection_root_" + str(root_section_id)
                                },
                            status = 200)

    def delete(self, request, root_section_id): 
        root_section = get_object_or_404(Section, pk=root_section_id)

        user = request.user
        user_can_write = root_section.user_has_perm(user, 'write')

        if not user_can_write:
            return HttpResponse("Unauthorized", status=401)

        root_section.delete()

        return HttpResponse("success", 
                            headers={
                                "HX-Trigger": "deleteSection_root_" + str(root_section_id)
                                },
                            status = 200)

# get/post for appending a file to a section
class FileModalView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/file_modal_form.html"   
    extra_context = {"form": FileForm()}

    def post(self, request, root_section_id): 
        return render(self, self.template_name)


class WikiView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/main.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"
