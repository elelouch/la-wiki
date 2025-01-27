from django.http import HttpRequest
from django.shortcuts import render
from django.views.generic.base import TemplateView

# Create your views here.

class LoginView(TemplateView):
    template_name = "theme/base.html"

    def get(self, request: HttpRequest):
        return render(request, self.template_name)
