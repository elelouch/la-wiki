# pyright: reportUnknownVariableType=false
from django.contrib.auth.models import Permission
from django.http import HttpRequest, HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth import mixins
from django.urls import reverse_lazy
from .forms import MarkdownForm, SectionForm, FileForm, SearchForm
from typing import cast, final
from django.core.files.base import ContentFile
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic.edit import CreateView
from .models import Section, Archive, User
from .service import elastic_service, fscrawler_service

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
        target="#sec_{root_id} .children-sections"
        initial = { "root_id": root_id }
        form = SectionForm(initial=initial)
        ctx = { 
            "target": target.format(root_id=root_id),
            "form": form
        }
        return render(request, self.template_name, ctx) 

class SectionView(mixins.LoginRequiredMixin, TemplateView):
    template_section_item = "core/section_item.html"
    def delete(self, request: HttpRequest, root_section_id: int): 
        root_section = get_object_or_404(Section, pk=int(root_section_id))
        root_section.delete()
        return HttpResponse("")
    
@final
class ModalArchiveView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/file_modal_form.html"   

    def get(self, request, root_id: int):
        target = "#sec_{root_id} > div > .children-archives"
        initial = { "root_id": root_id }
        ctx = {
            "target": target.format(root_id=root_id),
            "form": FileForm(initial=initial)
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
                "date_str": arch.first_time_upload.strftime("%Y/%m/%d")
            } 
            return render(request, self.template_name, ctx)

        ctx = { "content":arch.file.read().decode("utf-8") }

        return render(request, self.default_template, ctx)

    def delete(self, request: HttpRequest, archive_id: int):
        if not archive_id:
            return HttpResponse("Archive id not valid", status=400)
        user = cast(User, request.user)
        archive = get_object_or_404(Archive, pk=int(archive_id))

        if not archive.find_permission(user, "delete_archive"):
            return HttpResponse("Unauthorized", status=401)

        archive.file.delete()
        archive.delete()
        response = HttpResponse("")
        # agregamos header
        response["HX-Trigger"] = "clearMainSection"
        return response

class SearchArchiveListView(mixins.LoginRequiredMixin,ListView):
    template_name="core/archive_list.html"
    paginate_by = 10
    model = Archive
    login_url = reverse_lazy("wikiapp:login")

    def get_queryset(self):
        qs = super().get_queryset()
        data = self.request.GET
        # hacer la busqueda, despues revisar si puedo acotar por usuario
        search_content = (data.get("name") or "").strip()
        if not search_content or len(search_content) <= 2 :
            return []

        by_content = data.get("by_content")
        if by_content == "true":
            res = elastic_service.search_by_content(
                index="idx",
                content=search_content.strip(),
                extra={}
            )
            hits = res["hits"]["hits"]
            ids = [h for h in hits if int(h["id"])]

        ilike_content = "%{content}%".format(content=search_content)

        user = cast(User, self.request.user)
        main_section = user.main_section
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
                ) SELECT 
                        arch.id, 
                        arch.fullname, 
                        arch.name,
                        arch.description,
                        arch.section_id,
                        arch.first_time_upload,
                        arch.last_time_modified,
                        arch.extension,
                        arch.file
                FROM ancestors
                INNER JOIN core_archive arch
                ON ancestors.id = arch.section_id
                WHERE arch.fullname LIKE %s;
                """, [main_section.id, ilike_content])

@final
class SearchArchiveListReferencesView(SearchArchiveListView):
    template_name="core/archive_references_list.html"

@final
class ReferencesView(mixins.LoginRequiredMixin, TemplateView):
    template_name="core/reference_view.html"

    def get(self, request: HttpRequest, archive_id: int):
        assert self.template_name
        if not archive_id :
            return render(request, self.template_name, {}) 
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
        data = request.POST
        if not archive_id:
            return HttpResponse("Archive id is not valid", status=400)
        arch = get_object_or_404(Archive, pk=archive_id)
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
class MarkdownTextView(mixins.LoginRequiredMixin,TemplateView):
    template_name="core/markdown_form.html"
    markdown_template = "core/markdown_view.html"
    login_url = reverse_lazy("wikiapp:login")

    def get(self, request: HttpRequest):
        data = request.GET
        root_section_id = int(data.get("root_id") or 0)
        if not root_section_id:
            return HttpResponse("root id not provided", status = 400)
        md_form = MarkdownForm()
        ctx = { "form": md_form, "root_id": root_section_id }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest):
        data = request.POST
        markdown_ext = ".md"
        user = cast(User,request.user)
        filename = (data.get("name") or "").strip()
        file_content = data.get("file")
        root_section_id = int(data.get("root_id") or 0)
        if not root_section_id:
            return HttpResponse("No root id provided", status = 400)
        if not file_content:
            return HttpResponse("No files provided", status = 400)
        if not filename:
            return HttpResponse("No name provided", status = 400)
        root_section = get_object_or_404(Section, pk=root_section_id)
        fullname = filename + markdown_ext
        with ContentFile(file_content, name=fullname) as content_file:
            root_section.create_child_archive(
                content_file,
                user,
                'view_archive',
                'delete_archive'
            )
        
        ctx = {"file":markdown_tool.markdown(file_content)}
        return render(request, self.markdown_template, ctx)

class CreateArchiveView(CreateView):
    http_method_names = ['post']
    template_name = "core/archive_item.html"

    def post(self, request: HttpRequest):
        """
        Alta/modificacion de archivos.
        """
        form = FileForm(request.POST, request.FILES)
        if not form.is_valid(): 
            return HttpResponse("Form is not valid", status=400)

        root_id = form.cleaned_data["root_id"]
        root_section = get_object_or_404(Section, pk=root_id)

        user = cast(User, request.user)
        add_archive_perm = root_section.find_permission(user, "add_archive")
        if not add_archive_perm:
            return HttpResponse("Unauthorized", status=401)

        file = form.cleaned_data["file"]
        fscrawler_res = fscrawler_service.upload_file(file=file)
        res_ok = fscrawler_res["ok"]
        if not res_ok:
            return HttpResponse("Error during file indexing", status=400)

        archive_uuid = cast(str, fscrawler_res["id"])
        new_archive = root_section.create_child_archive(
            file=file,
            user=user,
            perms=["delete_archive","view_archive"],
            fields={
                "uuid": archive_uuid
            }
        )
        new_archive.uuid = archive_uuid
        new_archive.save()
        ctx = { "arch": new_archive }
        response = render(request, self.template_name, ctx)
        response["HX-Trigger"] = "clearMainSection"
        return response

class CreateSectionView(CreateView):
    http_method_names = ['post']
    template_name = "core/section_item.html"

    def post(self, request: HttpRequest): 
        data = SectionForm(request.POST)
        if not data.is_valid():
            return HttpResponse("Form is not valid", status=400)
        root_id = data.cleaned_data["root_id"]
        root_section = get_object_or_404(Section, pk=root_id)

        user = cast(User, request.user)
        can_add_section = root_section.find_permission(user, "add_section")
        if not can_add_section:
            return HttpResponse("Unauthorized", status = 401)
        cleaned_data = data.cleaned_data
        new_name = cast(str, cleaned_data.get("name"))
        new_child = root_section.create_child(
            name=new_name,
            user=user,
            perms=["delete_section", "view_section", "add_archive"]
        )
        ctx = {"sec": new_child, "root": root_section}
        res = render(request,self.template_name,ctx)
        res["HX-Trigger"] = "clearMainSection"
        return res
