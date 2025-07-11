from django.core.files import File
from django.db import models
from typing import Dict, final, Iterator
from django.contrib.auth.models import AbstractUser, Group, Permission
from itertools import chain

import os

from django.db.models.query import RawQuerySet

@final
class User(AbstractUser):
    main_section = models.ForeignKey(
        "Section",
        on_delete=models.SET_NULL,
        null=True
    )
    
class PermissionHolder:
    """
    Abstraccion encargada de gestionar los permisos por grupos y usuarios.
    """

    def user_permissions(self, user: User):
        raise NotImplementedError

    def group_permissions(self, user: User):
        """
        Obtiene todos los permisos del usuario segun los grupos en los que esta.
        """
        raise NotImplementedError
    
    def all_permissions(self, user: User) -> list[Permission]:
        assert user
        a = self.user_permissions(user)
        b = self.group_permissions(user)
        return list(chain(a,b))

    def find_permission(self, user: User, *perm_strs: str) -> bool:
        """
        perm_strs es una tupla que contienen los codenames de los permisos.
        """
        word_counter = {p:0 for p in perm_strs}
        for perm in self.all_permissions(user):
            codename = perm.codename 
            if codename in word_counter:
                word_counter[codename] += 1
        return all(val > 0 for val in word_counter.values())

@final
class Section(models.Model, PermissionHolder):
    name = models.CharField(max_length=256, null=False)
    description = models.CharField(max_length=256, default="")
    parent = models.ForeignKey(
            "self",
            on_delete=models.CASCADE,
            null=True,
            related_name="children"
            )

    def __str__(self):
        return self.name

    def create_child(self, *, name: str, user:User, perms: list[str]):
        """
        Crea un hijo y asigna los permisos enviados en formatos string.
        Estas strings tienen que coincidir con el "codename" de la entidad Permission.
        Basicamente, si matchea el codename, asigna ese permiso.
        """
        assert name and perms
        new_section = self.children.create(name = name)
        perm_entities = Permission.objects.filter(codename__in=perms)
        
        usp = new_section.usersectionpermission_set.create(user=user)
        usp.permissions.set(perm_entities)
        return new_section
        

    def all_children(self, user: User) -> RawQuerySet:
        """
        Ejecuta una query recursiva.
        Utiliza la union de un elemento ancla (o anchor, para este caso es la
        seccion actual) y se ubica como el SELECT **antes** del UNION ALL.
        Y una vista, que desde ahora, tendra la logica para la recursion y
        contiene aquellas secciones tales que su padre pertenece a la 
        vista 'ancestors' (que en un principio, solo posee el ancla).
        Esta ultima vista, es el SELECT **luego** del UNION ALL.

        Este metodo puede tener problemas con versiones
        de bases de datos que no permitan usar RECURSIVE.
        """
        assert user
        return Section.objects.raw(
            """
            WITH RECURSIVE ancestors AS (
                SELECT *
                FROM core_section s 
                WHERE s.id = %s
                UNION ALL
                SELECT cs.*
                FROM core_section cs, ancestors a 
                WHERE cs.parent_id = a.id
            ) SELECT * FROM ancestors;
            """, [self.id])

    def all_children_map(self, user: User) -> tuple[dict,dict]:
        """
        Obtiene todas las secciones hijas del elemento actual.
        DjangoORM permite realizar una precarga utilizando un 
        join con .prefetch_related(<nombre_entidad>). 
        Esto ejecuta una segunda query y permite no realizar
        una llamada a la base de datos por cada archivo utilizado.

        Para este caso, se traen los archivos disponibles para
        cada seccion.

        la idea de este metodo es armar dos mapas:
            - treemap, con pares (<id_seccion_padre>, [secciones_hijas])
            - archivesmap, con pares (<id_seccion_padre>, [archivos_hijos])
        """
        assert user
        treemap = {}
        archivesmap = {}
        qs = self.all_children(user)

        qs.prefetch_related("archives")
        for sec in self.all_children(user):
            parentid = sec.parent_id
            secid = sec.id
            if parentid not in treemap:
                treemap[parentid] = []
            treemap[parentid].append(sec)
            if secid not in archivesmap and sec.archives.all():
                archivesmap[secid] = []
            for arch in sec.archives.all():
                archivesmap[sec.id].append(arch)
        return (treemap, archivesmap)

    def create_child_archive(self, *, file: File, user:User, perms: list[str], fields: Dict[str, str | int]) -> "Archive":
        """
        Crea un archivo hijo de la seccion actual, agregando solo
        accesos para el usuario que lo creo.
        No se toca nada de grupos, la intencion es que un administrador
        agregue los permisos a un archivo de manera grupal.
        """
        assert file and user and perms
        fullname = str(file.name)
        filename, extension = os.path.splitext(fullname)
        arch = self.archives.create(
                fullname = file.name,
                name = filename,
                extension = extension,
                file = file,
                **fields
            )
        perm_entities = Permission.objects.filter(codename__in=perms)
        uap = arch.userarchivepermission_set.create(user=user)
        uap.permissions.set(perm_entities)
        return arch

    def group_permissions(self, user: User) -> Iterator[Permission]:
        assert user
        groups_perms = self.groupsectionpermission_set \
                .filter(group__in=user.groups.all())
        for gp in groups_perms:
            for perm in gp.permissions.all():
                yield perm

    def user_permissions(self, user: User) -> Iterator[Permission]:
        assert user
        user_perms = self.usersectionpermission_set \
                .filter(user=user) 
        for up in user_perms:
            for perm in up.permissions.all():
                yield perm

@final
class Archive(models.Model, PermissionHolder):
    fullname = models.CharField(max_length=256, null=False)
    name = models.CharField(max_length=256, null=False)
    description = models.CharField(max_length=256, default = "")
    references = models.ManyToManyField("self", symmetrical=False)
    extension = models.CharField(max_length=12, default = "")
    last_time_modified = models.DateField(null=True)
    first_time_upload = models.DateField(auto_now_add=True)
    section = models.ForeignKey(
        Section, 
        on_delete=models.CASCADE,
        null=False,
        related_name="archives"
    )
    file = models.FileField(upload_to="uploads/%Y/%m/%d", null=False)
    uuid = models.CharField(max_length=36, default="")

    def group_permissions(self, user: User) -> Iterator[Permission]:
        assert user
        groups_perms = self.grouparchivepermission_set.filter(group__in=user.groups.all())
        for gp in groups_perms:
            for perm in gp.permissions.all():
                yield perm

    def user_permissions(self, user: User) -> Iterator[Permission]:
        assert user
        user_perms = self.userarchivepermission_set.filter(user=user) 
        for gp in user_perms:
            for perm in gp.permissions.all():
                yield perm

class SectionPermission(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, default=None)
    permissions = models.ManyToManyField(Permission)
    class Meta:
        abstract = True

class ArchivePermission(models.Model):
    archive = models.ForeignKey(Archive, on_delete=models.CASCADE)
    permissions = models.ManyToManyField(Permission)
    class Meta:
        abstract = True
@final
class GroupArchivePermission(ArchivePermission):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

@final
class UserArchivePermission(ArchivePermission):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

@final
class GroupSectionPermission(SectionPermission):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

@final
class UserSectionPermission(SectionPermission):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
