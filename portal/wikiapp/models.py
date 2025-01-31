from typing import final
from django.db import models
from django.contrib.auth.models import Group

@final
class Menu(models.Model):
    name = models.CharField(max_length=200)
    reverse_view_url = models.CharField(max_length=200, default="wikiapp:home")
    groups = models.ManyToManyField(Group)

