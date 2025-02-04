# pyright: reportUnknownVariableType=false
from django.db import models
from typing import final
from django.contrib.auth.models import AbstractUser, Group

@final
class AccessList(models.Model):
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    user = models.ForeignKey(
            'User',
            null=True,
            on_delete=models.CASCADE,
            related_name="access_list"
            )
    groups = models.ManyToManyField(
            Group,
            related_name="access_lists"
            )

class PermissionHandler(models.Model):
    access_lists = models.ManyToManyField(AccessList)

    def user_has_perm(self, user, perm):
        acls_availables = self.access_lists.filter(groups__user__id=user.id)

        if not acls_availables:
            try:
                acls_availables = [self.access_lists.get(user_id=user.id)]
            except AccessList.DoesNotExist:
                return False

        for acl in acls_availables:
            if perm == 'read' and acl.can_read:
                return True
            if perm == 'write' and acl.can_write:
                return True
            
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
