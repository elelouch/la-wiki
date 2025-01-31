# pyright: reportUnknownVariableType=false
from django.db import models
from typing import final
from django.contrib.auth.models import User, Permission

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

# can_read_directory
# can_write_directory

@final
class DirectoryAccessList(models.Model):
    user = models.ForeignKey(
            User,
            null=True,
            on_delete=models.CASCADE,
            related_name="dir_access_list"
            )
    permissions = models.ManyToManyField(Permission)
    dir = models.ForeignKey(Directory, null=True, on_delete=models.CASCADE)

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

@final
class FileAccessList(models.Model):
    user = models.ForeignKey(
            User,
            null=True,
            on_delete=models.CASCADE,
            related_name="file_access_list"
            )
    permissions = models.ManyToManyField(Permission)
    dir = models.ForeignKey(File, null=True, on_delete=models.CASCADE)
