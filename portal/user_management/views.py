from django.shortcuts import render
from django.urls import reverse_lazy
from django.http import HttpRequest, HttpResponse
from django.db import models
from typing import final
from django.contrib.auth import authenticate, login, views, mixins
from django.views.generic.base import TemplateView
from core.models import User

@final
class ProfileView(mixins.LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy("wiki:login")
    template_name = "user_management/profile_view.html"
    redirect_field_name="login"

    def get(self, request: HttpRequest, user_id: int):
        assert self.template_name 
        user = User.objects.get(id=user_id)
        return render(request, self.template_name, {})
