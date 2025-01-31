from django.views.generic.base import TemplateView
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404
from typing import override
from .models import Directory,AccessList

# Create your views here.

class DirectoryView (TemplateView):
    template_name = "core/folder_view.html"
    
    @override
    def get(self, request, dir_id):
        assert self.template_name is not None
        root_dir = get_object_or_404(Directory, id=dir_id)

        context = {
                "root_dir": root_dir,
                "dirs": dir.directories.all(),
                "files": dir.files.all()
                }

        return render(request, self.template_name, context)

class WikiView (TemplateView):
    template_name = "core/main.html"

    @override
    def get(self, request):
        user = request.user

        return render(request, self.template_name, {"root_dir": root_dir})
