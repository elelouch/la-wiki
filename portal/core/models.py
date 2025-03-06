# pyright: reportUnknownVariableType=false
import enum
from django.core.files import File
from django.db.models import Q
import os
from django.db import models
from typing import final
from django.contrib.auth.models import AbstractUser, Group
from django.conf import settings


class Access(models.Model):
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)

    class Meta:
        abstract = True

@final
class UserAccess(Access):
    user = models.ForeignKey(
            "User",
            null=True,
            on_delete=models.CASCADE,
            related_name="accesses"
            )
    section = models.ForeignKey(
            "Section",
            null=True,
            on_delete=models.CASCADE,
            related_name="user_accesses"
            )

@final
class GroupAccess(Access):
    group = models.ForeignKey(
            Group,
            null=True,
            related_name="accesses",
            on_delete=models.CASCADE
            )
    section = models.ForeignKey(
            "Section",
            null=True,
            related_name="group_accesses",
            on_delete=models.CASCADE
            )
    
@final
class User(AbstractUser):
    main_section = models.ForeignKey(
            "Section",
            on_delete=models.SET_NULL,
            null=True
            )
    can_write_main_section = models.BooleanField(default=False)

@final
class Section(models.Model):
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
    
    def archive_availables(self, user: User):
        testing = """
        SELECT sec.name FROM core_user user
INNER JOIN core_user_groups ug
ON ug.user_id = user.id
INNER JOIN auth_group g 
ON ug.group_id = g.id
INNER JOIN core_groupaccess ga
ON ga.group_id = g.id 
INNER JOIN core_section sec
ON sec.id = ga.section_id
INNER JOIN core_archive ar;

WITH RECURSIVE ancestor AS (
    SELECT * FROM core_section sec
    WHERE sec.id=1
    UNION ALL
    SELECT children.*
    FROM core_section children, ancestor as a 
    WHERE children.parent_id = a.id
) SELECT * FROM ancestor;
"""
        pass

    def children_available(self, user: User):
        """
        Obtains children sections that the user can read, based on the access list
        """
        assert user is not None
        groups_access = Q(group_accesses__group__in = user.groups.all(),group_accesses__can_read = True)
        users_access = Q(user_accesses__user = user, user_accesses__can_read = True)
        # arreglar el modelo de estar query O mejorar la query para evitar usar distinct
        return self.children.filter(groups_access | users_access).distinct()

    def create_children(self, name: str):
        """
        Creates children and inherits permissions of the parent 
        """
        assert len(name)

        print("murio aca")
        new_sec = self.children.create(name = name)
        users_access = self.user_accesses.all()
        groups_access = self.group_accesses.all()

        users_acl = [
                UserAccess(
                    section=new_sec,
                    user=acc.user,
                    can_read=acc.can_read,
                    can_write=acc.can_write
                ) 
                for acc in users_access
            ]
        new_sec.user_accesses.bulk_create(users_acl)

        groups_acl = [
                GroupAccess(
                    section=new_sec,
                    group=acc.group,
                    can_read=acc.can_read,
                    can_write=acc.can_write
                ) 
                for acc in groups_access
            ]
        new_sec.group_accesses.bulk_create(groups_acl)

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

    def user_can_read(self, user):
        user_permission = self.user_accesses.filter(user=user, can_read=True)
        group_permission = self.group_accesses.filter(group__in=user.groups.all(), can_read=True)
        return user_permission.exists() or group_permission.exists()

    def user_can_write(self, user):
        user_permission = self.user_accesses.filter(user=user, can_write=True)
        group_permission = self.group_accesses.filter(group__in=user.groups.all(), can_write=True)
        return user_permission.exists() or group_permission.exists()

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
