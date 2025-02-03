from django.http import Http404
from django.views.generic.base import TemplateView
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404
from typing import override

from .models import Section, Archive

class DirectoryView (TemplateView):
    template_name = "core/section_view.html"

    @override
    def get(self, request, section_id):
        assert self.template_name is not None
        root_section = get_object_or_404(Section, id=section_id)
        user = request.user()

        if not user:
            return Http404()

        if not root_section.user_has_perm(user, 'read'):
            return Http404()

        context = {
                "root_section": root_section,
                "section": dir.sections.all(),
                "archives": dir.archives.all()
            }

        return render(request, self.template_name, context)


class WikiView (TemplateView):
    template_name = "core/main.html"
