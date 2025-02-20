# pyright: reportUnknownVariableType=false
import enum
from django.core.files import File
from django.db.models import Q
import os
from django.db import models
from typing import final
from django.contrib.auth.models import AbstractUser, Group
from django.conf import settings

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
class User(AbstractUser):
    main_section = models.ForeignKey(
            "Section",
            on_delete=models.SET_NULL,
            null=True
            )

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

    def children_available(self, user: User):
        """
        Obtains children sections that the user can read, based on the access list
        """
        assert user is not None
        sections = self.children \
                .filter(
                        Q(access_lists__group__user = user) | Q(access_lists__user = user),
                        access_lists__can_read = True)
        return sections 

    def create_children(self, name: str):
        """
        Creates children an inherits permissions of the parent 
        """
        assert len(name)
        new_sec = self.children.create(name = name)
        new_sec.access_lists.add(*self.access_lists.all())
        return new_sec

    def create_children_archive(self, file):
        assert file is not None
        fullname = str(file.name)
        filename, extension = os.path.splitext(fullname)
        arch = self.archives.create(
                fullname = file.name,
                name = filename,
                extension = extension,
                file = file
                )
        return arch

@final
class Archive(models.Model):
    fullname = models.CharField(max_length=256, default="")
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=256, default = "")
    references = models.ManyToManyField("self")
    extension = models.CharField(max_length=12, default = "")
    last_time_modified = models.DateField(auto_now_add=True)
    section = models.ForeignKey(
            Section, 
            on_delete=models.CASCADE,
            null=True,
            related_name="archives"
            )
    # setup name if necessary through file.name (must specify the path)
    file = models.FileField(upload_to="uploads", blank=True)
