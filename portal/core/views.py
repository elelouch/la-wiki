# pyright: reportUnknownVariableType=false
from django.http import Http404, HttpResponseNotFound
from django.views.generic.base import TemplateView
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import mixins
from django.db.models import Q
from django.urls import reverse_lazy
from core.forms import SectionForm
from typing import override

from .models import Section, Archive

class DirectoryView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_view.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"

    @override
    def get(self, request, section_id):

        assert self.template_name is not None
        root_section = None

        user = request.user
        if not section_id:
            root_section = user.main_section
            if not root_section:
                return HttpResponseNotFound("Main section not available")
        else :
            root_section = get_object_or_404(Section, pk=section_id)

        sections = root_section.sections \
                .filter(
                        Q(access_lists__groups__user__id = user.id) | Q(access_lists__user__id = user.id),
                        access_lists__can_read = True)

        return render(request, self.template_name, {"sections": sections})

    def post(self, request, section_id):
        section = get_object_or_404(Section, pk=section_id)
        user = request.user

        if section.user_has_perm(section, "write"):
            form = request.POST
            print(form)

        return render(request, self.template_name)

class WikiView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/main.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"
    extra_context = {"section_form": SectionForm()}
