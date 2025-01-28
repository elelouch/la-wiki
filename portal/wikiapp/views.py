from typing import final, override
from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.contrib.auth import models, authenticate

from . import forms

# Create your views here.

@final
class LoginView(TemplateView):
    template_name = "theme/login.html"

    @override
    def get(self, request: HttpRequest):
        return render(request, self.template_name, {"form": forms.LoginForm()})

    def post(self, request: HttpRequest):
        form = forms.LoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form}) 

        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        user = authenticate(request, username= username, password=password)
        if user is not None: 
            return redirect("wikiapp:home")

        form.add_error("username", "User does not exist")
        return render(request, self.template_name, {"form": form}) 


@final
class HomeView(TemplateView):
    template_name = "theme/home.html"

    @override
    def get(self, request: HttpRequest):
        return render(request, self.template_name)
