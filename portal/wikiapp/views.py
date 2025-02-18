from typing import final
from django.http import HttpRequest
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.contrib.auth import authenticate, login, views, mixins
from django.utils.translation import gettext_lazy as _
from core.models import User
from . import forms

# Create your views here.

@final
class LoginView(TemplateView):
    template_name = "wikiapp/login.html"
    extra_context = {"form": forms.LoginForm()}

    def post(self, request: HttpRequest):
        assert self.template_name is not None

        form = forms.LoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form}) 

        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None: 
            login(request, user)
            return redirect("wikiapp:home")

        form.add_error("username", _("Check if credentials are correct."))
        return render(request, self.template_name, {"form": form}) 

@final
class HomeView(mixins.LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy("wikiapp:login")
    template_name = "wikiapp/home.html"
    redirect_field_name="login"

@final
class LogoutView(views.LogoutView):
    template_name = "wikiapp/logout.html"
    next_page = reverse_lazy("wikiapp:login")

@final
class UserFormView(mixins.LoginRequiredMixin, TemplateView):
    template_name = "core/user_profile.html"   
    extra_context = {"form": forms.UserForm()}

    def post(self, request: HttpRequest):
        user = User(**request.POST)
        if not user.id:
            return HttpResponse("Id is not valid", status = 401)

        return redirect(request, self.template_name)
