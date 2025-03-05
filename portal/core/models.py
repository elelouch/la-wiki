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
            related_name="user_accesses"
            )
    section = models.ForeignKey(
            "Section",
            null=True,
            related_name="users_access",
            on_delete=models.CASCADE
            )
    

@final
class GroupAccess(Access):
    group = models.ForeignKey(
            Group,
            null=True,
            related_name="group_accesses",
            on_delete=models.CASCADE
            )
    section = models.ForeignKey(
            "Section",
            null=True,
            related_name="groups_access",
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

    def archives_availables(self, user: User):
        archives = Archive.objects.raw(
        """
        WITH RECURSIVE ancestors AS (
            SELECT *
            FROM core_section WHERE parent_id = %s
            UNION ALL
            SELECT child.* FROM core_section child, ancestors a
            WHERE child.parent_id = a.id
        ) SELECT * FROM core_archive arch
        INNER JOIN ancestors anc
        ON anc.id = arch.section_id
        """,

        """
        /* WITH RECURSIVE ancestors AS (
    SELECT *
    FROM core_section WHERE parent_id = 1
    UNION ALL
    SELECT child.* FROM core_section child, ancestors a
    WHERE child.parent_id = a.id
) SELECT * FROM core_archive arch
INNER JOIN ancestors anc
ON anc.id = arch.section_id; */


/* WITH RECURSIVE ancestors AS (
    SELECT *
    FROM core_section WHERE parent_id = 1
    UNION ALL
    SELECT child.* FROM core_section child, ancestors a
    WHERE child.parent_id = a.id
) SELECT * FROM core_archive arch
INNER JOIN ancestors anc
ON anc.id = arch.section_id; */

SELECT * FROM core_user user
INNER JOIN core_user_groups ug
ON ug.user_id = user.id
INNER JOIN auth_group g
ON ug.group_id = g.id
INNER JOIN core_groupaccess cga
ON cga.group_id = g.id;

        """
        [user.main_section.id])
        return archives.execute()

    def children_available(self, user: User):
        """
        Obtains children sections that the user can read, based on the access list
        """
        assert user is not None
        groups_access = Q(groups_access__group__in = user.groups.all(),groups_access__can_read = True)
        users_access = Q(users_access__user = user, users_access__can_read = True)
        # arreglar el modelo de estar query O mejorar la query para evitar usar distinct
        return self.children.filter(groups_access | users_access).distinct()

    def create_children(self, name: str):
        """
        Creates children and inherits permissions of the parent 
        """
        assert len(name)
        new_sec = self.children.create(name = name)
        users_access = self.users_access.all()
        groups_access = self.groups_access.all()

        users_acl = [UserAccess(section=new_sec, user=acc.user, can_read=acc.can_read, can_write=acc.can_write) for acc in users_access]
        new_sec.users_access.bulk_create(users_acl)

        groups_acl = [GroupAccess(section=new_sec, group=acc.group, can_read=acc.can_read, can_write=acc.can_write) for acc in groups_access]
        new_sec.groups_access.bulk_create(groups_acl)

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
        user_permission = self.users_access.filter(user=user, can_read=True)
        group_permission = self.groups_access.filter(group__in=user.groups.all(), can_read=True)
        return user_permission.exists() or group_permission.exists()

    def user_can_write(self, user):
        user_permission = self.users_access.filter(user=user, can_write=True)
        group_permission = self.groups_access.filter(group__in=user.groups.all(), can_write=True)
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
