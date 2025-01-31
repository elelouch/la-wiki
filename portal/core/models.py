# pyright: reportUnknownVariableType=false
from django.db import models
from typing import final
from django.contrib.auth.models import Permission, User

@final
class Directory(models.Model):
    name = models.CharField(max_length=256, default="")
    description = models.CharField(max_length=256, default="")
    parent = models.ForeignKey(
            "self",
            on_delete=models.CASCADE,
            null=True,
            related_name="directories"
            )
    @final
    class Meta:
        permissions = [
                ("can_write_dir", "Can write directory"),
                ("can_read_dir", "Can read directory")
                ]

@final
class AccessList(models.Model):
    dir = models.ForeignKey(Directory, null=True, on_delete=models.CASCADE)
    user = models.OneToOneField(
            User,
            null=True,
            on_delete=models.CASCADE,
            related_name="access_list"
            )

@final
class File(models.Model):
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    references = models.ManyToManyField("File")
    extension = models.CharField(max_length=12)
    last_time_modified = models.DateField()
    folder = models.ForeignKey(
            Directory, 
            on_delete=models.CASCADE,
            null=True,
            related_name="files"
            )
