from typing import final
from django.db import models
from django.contrib.auth.models import Group
from django.urls import reverse_lazy, reverse

# Create your models here.

@final
class Menu(models.Model):
    name = models.CharField(max_length=200)
    parent = models.ForeignKey("Menu", on_delete=models.CASCADE, null=True)
    reverse_view_url = models.CharField(max_length=200, default="wikiapp:home")
    groups = models.ManyToManyField(Group)

@final
class File(models.Model):
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    references = models.ManyToManyField("File")
    extension = models.CharField(max_length=12)
    last_time_modified = models.DateField()


@final
class Folder(models.Model):
    parent = models.ForeignKey("Folder", on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
