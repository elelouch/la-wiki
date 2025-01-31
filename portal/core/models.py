# pyright: reportUnknownVariableType=false
from django.db import models
from typing import final

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
