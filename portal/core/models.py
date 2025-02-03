# pyright: reportUnknownVariableType=false
from django.db import models
from typing import final
from django.contrib.auth.models import User

@final
class AccessList(models.Model):
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    user = models.ForeignKey(
            User,
            null=True,
            on_delete=models.CASCADE,
            related_name="dir_access_list"
        )

@final
class PermissionHandler(models.Model):
    access_list = models.ManyToManyField(AccessList)

    def user_has_perm(self, user, perm):
        access_list = AccessList.objects.get(user_id=user.id)
        if perm == 'read':
            return access_list.can_read
        if perm == 'write':
            return access_list.can_write
        return False

@final
class Section(models.Model):
    name = models.CharField(max_length=256, default="")
    description = models.CharField(max_length=256, default="")
    parent = models.ForeignKey(
            "self",
            on_delete=models.CASCADE,
            null=True,
            related_name="sections"
            )
        
@final
class Archive(models.Model):
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    references = models.ManyToManyField("self")
    extension = models.CharField(max_length=12)
    last_time_modified = models.DateField()
    section = models.ForeignKey(
            Section, 
            on_delete=models.CASCADE,
            null=True,
            related_name="archives"
            )
