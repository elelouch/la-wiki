# pyright: reportUnknownVariableType=false
from django.contrib.auth.models import Permission
from django.http import HttpRequest, HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth import mixins
from django.urls import reverse, reverse_lazy
from .forms import MarkdownForm, SectionForm, FileForm, SearchForm
from typing import cast, final
from django.core.files.base import ContentFile
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic.edit import CreateView
from .models import Section, Archive, User

import markdown as markdown_tool

@final
class ChildrenView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_view.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name = "login"

    def get(self, request: HttpRequest):
        assert self.template_name
        user = cast(User,request.user)
        ms = cast(Section, user.main_section)
        if not ms:
            return HttpResponse("Main section not assigned", status = 404)
        a,b = ms.all_children_map(user)
        return render(
                request,
                self.template_name,
                {
                    "archmap": b,
                    "secmap": a,
                    "root_id": ms.id
                }
            )

@final
class ModalSectionView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_modal_form.html"

    def get(self, request, root_id: int):
        assert self.template_name and root_id
        target="#sec_{root_id} .children-sections"
        initial = { "root_id": root_id }
        form = SectionForm(initial=initial)
        ctx = { 
            "target": target.format(root_id=root_id),
            "form": form
        }
        return render(request, self.template_name, ctx) 

class SectionView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_item.html"
    def delete(self, request: HttpRequest, root_section_id: int): 
        root_section = get_object_or_404(Section, pk=int(root_section_id))
        root_section.delete_section()
        return HttpResponse("")
    
@final
class ModalArchiveView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/file_modal_form.html"   

    def get(self, request, root_id: int):
        assert self.template_name and root_id
        target = "#sec_{root_id} > div > .children-archives"
        initial = { "root_id": root_id }
        md_piv_url = reverse("core:markdown_text") + "?root_id={root_id}"
        md_url = md_piv_url.format(root_id=root_id)
        ctx = {
            "target": target.format(root_id=root_id),
            "form": FileForm(initial=initial),
            "markdown_url": md_url,
        }
        return render(request, self.template_name, ctx)

@final
class WikiView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/main.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"

@final
class ArchiveView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/archive_view.html"
    markdown_template = "core/markdown_view.html"
    default_template = "core/archive_view_default.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"
    iframe_render=[".pdf", ".svg", ".jpg", ".jpeg", ".png"]

    @method_decorator(xframe_options_sameorigin)
    def get(self, request: HttpRequest, archive_id: int):
        assert self.template_name
        arch = get_object_or_404(Archive, pk=int(archive_id))
        user = cast(User, request.user)
        can_view_archive = arch.find_permission(user, 'view_archive')
        if not can_view_archive:
            return HttpResponse("Unauthorized", status=401)
        if ".md" == arch.extension :
            text = arch.file.read()
            ctx = {
                "archive": arch,
                "file": markdown_tool.markdown(text.decode('utf-8'))
            }
            return render(request,self.markdown_template,ctx)

        if arch.extension in self.iframe_render:
            ctx = {
                "archive": arch,
                "file": arch.file,
            } 
            return render(request, self.template_name, ctx)

        ctx = { "content":arch.file.read().decode("utf-8") }

        return render(request, self.default_template, ctx)

    def delete(self, request: HttpRequest, archive_id: int):
        user = cast(User, request.user)
        archive = get_object_or_404(Archive, pk=archive_id)

        if not archive.find_permission(user, "delete_archive"):
            return HttpResponse("Unauthorized", status=401)
        archive.delete_archive()
        response = HttpResponse("")
        response["HX-Trigger"] = "clearMainSection"
        return response

class SearchArchiveListView(mixins.LoginRequiredMixin,ListView):
    template_name="core/archive_list.html"
    paginate_by = 10
    model = Archive
    login_url = reverse_lazy("wikiapp:login")

    def get_queryset(self):
        form = SearchForm(self.request.GET)
        if not form.is_valid():
            return []

        search_content = form.cleaned_data["name"]
        if len(search_content) <= 2 :
            return []

        by_content = form.cleaned_data["by_content"]

        user = cast(User, self.request.user)
        main_section = user.main_section
        if not by_content:
            return main_section.find_archive_by_name(name=search_content)
        return main_section.find_archive_by_content(content=search_content)
        
@final
class SearchArchiveListReferencesView(SearchArchiveListView):
    template_name="core/archive_references_list.html"

@final
class ReferencesView(mixins.LoginRequiredMixin, TemplateView):
    template_name="core/reference_view.html"

    def get(self, request: HttpRequest, archive_id: int):
        assert self.template_name
        if not archive_id:
            return render(request, self.template_name) 
        arch = get_object_or_404(Archive, pk=archive_id)
        refs = arch.references
        return render(
            request, 
            self.template_name, 
            {
                "arch": arch,
                "form": SearchForm(),
                "references": refs.all(),
                "ids": list(refs.values_list('id', flat=True))
            }
        ) 

    def post(self, request: HttpRequest, archive_id: int):
        assert archive_id
        arch = get_object_or_404(Archive, pk=archive_id)
        data = request.POST
        new_refs = data.get("refs")
        if not new_refs:
            arch.references.clear()
            return HttpResponse("")
        excluded_refs = arch.references \
            .exclude(id__in=new_refs) \
            .values_list('id', flat=True)
        excluded_refs_list = list(excluded_refs)
        if excluded_refs_list:
            arch.references.remove(excluded_refs_list)
        arch.references.add(new_refs)
        return HttpResponse("")

@final
class SearchArchiveView(mixins.LoginRequiredMixin,TemplateView):
    template_name="core/search_modal.html"
    login_url = reverse_lazy("wikiapp:login")
    extra_context = {"form": SearchForm()}

@final
class ChildrenViewTest(mixins.LoginRequiredMixin,ListView):
    template_name = "core/section_view.html"

@final
class MarkdownView(mixins.LoginRequiredMixin,TemplateView):
    template_name="core/markdown_form.html"
    markdown_template="core/markdown_view.html"
    login_url = reverse_lazy("wikiapp:login")

    def get(self, request: HttpRequest):
        assert self.template_name
        md_form = MarkdownForm(initial=request.GET)
        ctx = { "form": md_form }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest):
        assert self.template_name

        md_form = MarkdownForm(request.POST)
        if not md_form.is_valid():
            return HttpResponse("Form is not valid")
        cd = md_form.cleaned_data
            
        root_id = cd["root_id"]
        root_section = get_object_or_404(Section, pk=root_id)

        str_text_file = cd["file"]
        filename = cd["name"] + ".md"
        with ContentFile(str_text_file, name=filename) as content_file:
            user = cast(User, request.user)
            created_archive = root_section.create_child_archive(
                file=content_file,
                user=user,
                perms=["view_archive","delete_archive"],
            )
            target = "#sec_{root_id} > div > .children-archives"
            oob_target = target.format(root_id=root_id)
            ctx = { 
                "file": markdown_tool.markdown(str_text_file),
                "archive": created_archive,
                "oob_target": oob_target,
            }
            return render(request, self.markdown_template, ctx)

class CreateArchiveView(mixins.LoginRequiredMixin, CreateView):
    http_method_names = ['post']
    template_name = "core/archive_item.html"

    def post(self, request: HttpRequest):
        """
        Alta/modificacion de archivos.
        """
        assert self.template_name
        form = FileForm(request.POST, request.FILES)
        if not form.is_valid(): 
            return HttpResponse("Form is not valid", status=400)
        cd = form.cleaned_data

        root_id = cd["root_id"]
        root_section = get_object_or_404(Section, pk=root_id)

        user = cast(User, request.user)
        add_archive_perm = root_section.find_permission(user, "add_archive")
        if not add_archive_perm:
            return HttpResponse("Unauthorized", status=401)

        file = cd["file"]
        new_archive = root_section.create_child_archive(
            file=file,
            user=user,
            perms=["delete_archive", "view_archive"],
        )

        ctx = { "arch": new_archive }
        response = render(request, self.template_name, ctx)
        response["HX-Trigger"] = "clearMainSection"
        return response

class CreateSectionView(mixins.LoginRequiredMixin, CreateView):
    http_method_names = ['post']
    template_name = "core/section_item.html"

    def post(self, request: HttpRequest): 
        assert self.template_name
        data = SectionForm(request.POST)
        if not data.is_valid():
            return HttpResponse("Form is not valid", status=400)

        cd = data.cleaned_data

        root_id = cd["root_id"]
        root_section = get_object_or_404(Section, pk=root_id)

        user = cast(User, request.user)
        can_add_section = root_section.find_permission(user, "add_section")
        if not can_add_section:
            return HttpResponse("Unauthorized", status = 401)

        child_name = cd["name"]
        new_section = root_section.create_child(
            child_name=child_name,
            user=user,
            perms=[
                "delete_section",
                "view_section",
                "add_archive",
                "add_section"
            ]
        )

        ctx = { "sec": new_section, "root": root_section }
        res = render(request, self.template_name, ctx)
        res["HX-Trigger"] = "clearMainSection"
        return res

