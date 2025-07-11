from typing import final
from django.http import HttpRequest
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.contrib.auth import authenticate, login, views, mixins
from django.utils.translation import gettext_lazy as _
from . import forms

@final
class LoginView(TemplateView):
    template_name = "wikiapp/login.html"
    extra_context = {"form": forms.LoginForm()}

    def post(self, request: HttpRequest):
        assert self.template_name

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
