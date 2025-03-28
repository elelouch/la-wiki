# pyright: reportUnknownVariableType=false
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
import markdown as markdown_tool

from .models import GroupSectionPermission, Section, Archive, User, UserSectionPermission

@final
class ChildrenView (mixins.LoginRequiredMixin, TemplateView):
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

# get/post for appending a section to a section
@final
class ModalSectionView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/section_modal_form.html"
    def get(self, request: HttpRequest, root_section_id: int):
        assert self.template_name
        return render(request, self.template_name, {
            "root_id": root_section_id,
            "form": SectionForm()
            })
    

class SectionView(mixins.LoginRequiredMixin, TemplateView):
    template_section_item = "core/section_item.html"
    def delete(self, request: HttpRequest, root_section_id: int): 
        root_section = get_object_or_404(Section, pk=int(root_section_id))
        root_section.delete()
        return HttpResponse("")
    
    def post(self, request: HttpRequest, root_section_id: int): 
        data = request.POST
        root_section = None
        if not root_section_id:
            user = cast(User, request.user)
            root_section = user.main_section
            if not root_section:
                return HttpResponse("Main section not assigned", status=400)
        else:
            root_section = get_object_or_404(Section, pk=root_section_id)
        name = data.get("name")
        if not name:
            return HttpResponse("Invalid request", status=400)
        new_child = root_section.create_children(name)
        res = render(
                request,
                self.template_section_item,
                {"sec": new_child,"root": root_section}
           )
        res["HX-Trigger"] = "clearMainSection"
        return res

# get/post for appending a file to a section
@final
class ModalArchiveView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/file_modal_form.html"   
    archive_item_template = "core/archive_item.html"
    extra_context = {"form": FileForm()}

    def get(self, request: HttpRequest, root_section_id: int):
        assert self.template_name
        return render(
        	request,
        	self.template_name,
        	{"root_id": root_section_id, "form":FileForm()}
        )

    def post(self, request: HttpRequest, root_section_id: int):
        user = cast(User, request.user)
        files = request.FILES
        root_section = None
        can_write_section = False

        if not root_section_id:
            root_section = user.main_section
            if not root_section:
                return HttpResponse("Main section not assigned", status=400)
        else:
            root_section = get_object_or_404(Section, pk=root_section_id)
        #root_section cannot be null at this point

        can_write_section = root_section.find_permission(user, 'can_write_section')
        if not can_write_section:
            return HttpResponse("Unauthorized", status=401)

        file = files.get("file")
        if not file: 
            return HttpResponse("File not uploaded", status=400)
        new_archive = root_section.create_children_archive(file)
        response = render(
            request,
            self.archive_item_template,
            {
            	"root_id": root_section_id,
            	"arch": new_archive
            }
        )
        response["HX-Trigger"] = "clearMainSection"
        return response

@final
class WikiView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/main.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"

@final
class ArchiveView (mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/archive_view.html"
    markdown_template = "core/markdown_view.html"
    default_template = "core/archive_view_default.html"
    login_url = reverse_lazy("wikiapp:login")
    redirect_field_name="login"
    iframe_render=[".pdf", ".svg", ".jpg", ".jpeg", ".png"]

    @method_decorator(xframe_options_sameorigin)
    def get(self, request: HttpRequest, archive_id: int):
        arch = get_object_or_404(Archive, pk=int(archive_id))

        if ".md" == arch.extension :
            text = arch.file.read()
            html = markdown_tool.markdown(text.decode("utf-8"))
            return render(request, self.markdown_template, {"archive": arch, "file": html})

        if arch.extension in self.iframe_render:
            return render(
                request,
                self.template_name,
                {
                    "archive": arch,
                    "file": arch.file,
                    "date_str": arch.first_time_upload.strftime("%Y/%m/%d")
                })

        return render(request, self.default_template, {"content":arch.file.read().decode("utf-8")})

    def delete(self, request: HttpRequest, archive_id: int):
        archive = get_object_or_404(Archive, pk=int(archive_id))
        archive.file.delete()
        archive.delete()
        response = HttpResponse("")
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
        user = self.request.user
        search_content = data.get("name")
        if not search_content or len(search_content) <= 2 :
            return []
        ilike_content = "%{content}%".format(content=search_content)
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
                    AND cs.id NOT IN (
                        SELECT nacc.section_id 
                        FROM core_negativeaccess nacc
                        WHERE nacc.user_id = %s
                    )
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
                """, [user.main_section.id, user.id, ilike_content])

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
            return HttpResponse("")
        excluded_refs =  arch.references.all().exclude(id__in=new_refs)
        for eref in excluded_refs:
            eref.delete()
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
