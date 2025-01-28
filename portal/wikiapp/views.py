from typing import final, override
from django.http import HttpRequest
from django.shortcuts import render
from django.views.generic.base import TemplateView

from . import forms

# Create your views here.

@final
class LoginView(TemplateView):
    template_name = "theme/login.html"

    @override
    def get(self, request: HttpRequest):
        form = forms.LoginForm()
        return render(request, self.template_name, {"form": form})
