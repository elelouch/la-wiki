from django.db.models import SET_NULL, ForeignKey
from itertools import chain
from functools import reduce
from django.db import models
from typing import final
from django.contrib.auth.models import AbstractUser, Group, Permission
import os

from django.db.models.query import RawQuerySet

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
                AND cs.id NOT IN (
                    SELECT nacc.section_id 
                    FROM core_negativeaccess nacc
                    WHERE nacc.user_id = %s
                )
            ) SELECT * FROM ancestors;
            """, [self.id, user.id])

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

    def all_children_map_reduce(self, user: User) -> dict:
        """
        Experimental (Se puede borrar)
        Obtiene la lista de secciones hijas
        """
        def aux(child_sec, tree_map):
            pid = child_sec.parent_id
            if child_sec.parent_id not in tree_map:
                tree_map[pid] = []
            tree_map[pid].append(child_sec)
        return reduce(aux, self.all_children(user), {})

    def children_available(self, user: User):
        """
        Experimental (Se puede borrar).
        """
        assert user 
        return Section.objects.raw(
                """
                SELECT * FROM core_section cs
                WHERE cs.parent_id = %s AND cs.id NOT IN (
                    SELECT nacc.section_id 
                    FROM core_negativeaccess nacc
                    WHERE nacc.user_id = %s);
                """, [self.id, user.id])

    def create_children_archive(self, file, user:User, perms: list[Permission]):
        """
        Crea un archivo hijo de la seccion actual, agregando solo
        accesos para el usuario.
        No se toca nada de grupos, ya que la intencion es que un administrador
        agregue los permisos a un archivo, a mano.
        """
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

    def group_permissions(self, user: User) -> list[Permission]:
        assert user
        groups_perms = self.groupsectionpermission_set \
                .filter(group__in=user.groups.all())
        return [gp.permissions.all() for gp in groups_perms]


    def user_permissions(self, user: User) -> list[Permission]:
        assert user
        user_perms = self.usersectionpermission_set \
                .filter(user=user) 
        return [up.permissions.all() for up in user_perms]

    def all_permissions(self, user: User) -> list[Permission]:
        assert user and str
        return list(chain(self.user_permissions(user), self.group_permissions(user)))

    def find_permission(self, user: User, perm_str: str) -> bool:
        return any(p.name == perm_str for p in self.all_permissions(user))

@final
class Archive(models.Model):
    fullname = models.CharField(max_length=256, default="")
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=256, default = "")
    references = models.ManyToManyField("self")
    extension = models.CharField(max_length=12, default = "")
    last_time_modified = models.DateField(null=True)
    first_time_upload = models.DateField(auto_now_add=True)
    section = models.ForeignKey(
            Section, 
            on_delete=models.CASCADE,
            null=True,
            related_name="archives"
            )
    # setup name if necessary through current_archive.file.name when saving
    file = models.FileField(upload_to="uploads/%Y/%m/%d", blank=True)

class SectionPermission(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
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
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null = True)

@final
class UserArchivePermission(ArchivePermission):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null = True)

@final
class GroupSectionPermission(SectionPermission):
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null = True)

@final
class UserSectionPermission(SectionPermission):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null = True)

@final
class NegativeAccess(models.Model):
    user = ForeignKey(User, on_delete=models.CASCADE, null=True)
    section = ForeignKey(Section, on_delete=models.CASCADE, null=True)
