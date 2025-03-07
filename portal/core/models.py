# pyright: reportUnknownVariableType=false
import enum
from django.core.files import File
from django.db.models import Q, ForeignKey
import os
from django.db import models
from typing import final
from django.contrib.auth.models import AbstractUser, Group
from django.conf import settings

@final
class User(AbstractUser):
    can_write_main_section = models.BooleanField(default=False)
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

    def create_children(self, name: str):
        assert len(name)
        return self.children.create(name = name)

    def children_available(self, user: User):
        return Section.objects.raw(
                """
                SELECT * FROM core_section cs
                WHERE cs.parent_id = %s AND cs.id NOT IN (
                    SELECT nacc.section_id 
                    FROM core_negativeaccess nacc
                    WHERE nacc.user_id = %s);
                """, [self.id, user.id])

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

@final
class NegativeAccess(models.Model):
    user = ForeignKey(User, on_delete=models.SET_NULL, null=True)
    section = ForeignKey(Section, on_delete=models.SET_NULL, null=True)

