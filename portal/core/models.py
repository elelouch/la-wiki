# pyright: reportUnknownVariableType=false
from django.db import models
from typing import final
from django.contrib.auth.models import AbstractUser

@final
class AccessList(models.Model):
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    user = models.ForeignKey(
            'User',
            null=True,
            on_delete=models.CASCADE,
            related_name="dir_access_list"
        )

class PermissionHandler(models.Model):
    access_list = models.ManyToManyField(AccessList)

    def user_has_perm(self, user, perm):

        try:
            access_list = self.access_list.get(user_id=user.id)
        except AccessList.DoesNotExist:
            return False

        if perm == 'read':
            return access_list.can_read
        if perm == 'write':
            return access_list.can_write
        return False
        
@final
class Section(PermissionHandler):
    name = models.CharField(max_length=256, default="")
    description = models.CharField(max_length=256, default="")
    parent = models.ForeignKey(
            "self",
            on_delete=models.CASCADE,
            null=True,
            related_name="sections"
            )

@final
class User(AbstractUser):
    main_section = models.ForeignKey(
            Section,
            on_delete=models.CASCADE,
            null=True
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
