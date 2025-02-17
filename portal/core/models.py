# pyright: reportUnknownVariableType=false
import enum
from django.db import models
from typing import final
from django.contrib.auth.models import AbstractUser, Group

class PermissionType(enum.Enum):
    READ = "read"
    WRITE = "write"

@final
class Access(models.Model):
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    user = models.ForeignKey(
            'User',
            null=True,
            on_delete=models.CASCADE,
            related_name="access_lists"
            )
    group = models.ForeignKey(
            Group,
            null=True,
            related_name="access_lists",
            on_delete=models.CASCADE
            )

class PermissionHandler(models.Model):
    access_lists = models.ManyToManyField(Access)
    def user_has_perm(self, user, perm):
        Q = models.Q
        acls_availables = self.access_lists \
                .filter(Q(group__in=user.groups.all()) | Q(user=user))

        if not acls_availables:
            return False

        for acl in acls_availables:
            if perm == PermissionType.READ and acl.can_read:
                return True
            if perm == PermissionType.WRITE and acl.can_write:
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
            related_name="children"
            )

    def __str__(self):
        return self.name

@final
class User(AbstractUser):
    main_section = models.ForeignKey(
            Section,
            on_delete=models.SET_NULL,
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
