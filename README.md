# La Wiki

## Introduccion
Proyecto incompleto para organizar archivos internos.

### Objetivos del proyecto
- Busqueda por PDF escaneados.
- Busqueda por nombres de archivos.
- Organizacion de la informacion por jerarquias.

### Herramientas utilizadas
- [Django](https://docs.djangoproject.com/en/dev/)
- [HTMX](https://htmx.org/docs/)
- [AlpineJS](https://alpinejs.dev/start-here/)
- [Tailwind](https://tailwindcss.com/docs/)

## Como encarar el proyecto
El proyecto es intuitivo, se puede tomar si se posee algun conocimiento de desarrollo y experiencia.

En caso contrario, se asume que el lector tiene una minima base de programacion y se sugiere:
- Tener conceptos basicos de base de datos: 
    - Concepto de entidades.
    - Relaciones: OneToMany (implementacion por tabla intermedia o foreign key), ManyToOne. Partes dominantes.
    - Conocimiento de SQL: INNER y LEFT JOINS, Consultas recursivas.
- Leer la documentacion de Django para entender algunos conceptos claves:
    - Gestion del proyecto mediante ./manage.py (manage.py {shell,runserver,etc...}
    - Division de tareas mediante apps.
    - Vistas basadas en clases (Class based views). 
    - Mixins: clases auxiliares para extender la utilidad de las vistas.
    - Modelos.
    - Django ORM: Querysets (Realizar joins, busquedas sencillas por propiedad de una entidad), entender el parametro related\_name en una ForeignKey esto es, una lista de los registros que apuntan al lado no dominante.
    - Ciclo de una request: Obtener parametros mediante el diccionario **request.METODO** donde METODO puede ser GET, POST, DELETE,... y envio de respuesta renderizando un **template** HTML con HttpResponse, render(...), etc.
- Entender el protocolo HTTP.
    - Cuando utilizar POST, GET, DELETE, PUT, etc...
- Tener conocimientos de Docker:
    - docker run
    - compose
- Inspeccionar las tablas utilizando el [administrador de bases de datos (Adminer).](#runproyect)

Todas estas herramientas fueron utilizadas durante el desarrollo y son parte del proyecto.
Lo que no quiere decir que estas esten limitadas a esto (Django es un framework bastante extenso, la teoria de base de datos puede llevar conceptos como normalizacion, SQL tiene un millon de cosas para aprender, HTTP es muy extenso, etc).

## Prerequisitos
- Docker
- Interprete de Python >= 3.10.12
- NodeJS
- Modulo de entorno virtual (venv), en apt esto se puede descargar mediante
```
    apt install python3-venv
```
### Trabajo bajo proxy
Al trabajar con algun derivado de Unix, solo es suficiente el siguiente comando.
```
    export http_proxy=URL_PROXY
    export https_proxy=URL_PROXY
```
donde URL\_PROXY generalmente tiene la forma
```
    http://USUARIO:CONTRASENA@proxyespecial.svc.rosario.gov.ar:3128

```
Los administradores de paquetes generalmente utilizan esta variable antes de descargar todo.
Puede llegar a tener algun problema al trabajar con WSL.


## Como correr el proyecto
Se asume que DIRECTORIO\_REPOSITORIO es el directorio de este proyecto.
### Asegurarse de tener el entorno virtual con dependencias
Esto se realiza mediante el siguiente comando.
```
    cd DIRECTORIO_REPOSITORIO
    python3 -m venv .
    source bin/activate
    pip install -r requirements.txt
```
La lista de dependencias puede ser vista en el archivo requirements.txt.
Ademas, si se necesitara actualizarla, tal vez luego de utilizar pip install con una libreria nueva.
**RECORDAR QUE CADA pip install DEBERA SER EJECUTADO TENIENDO EL ENTORNO VIRTUAL ACTIVADO**, caso contrario, tal vez nisiquiera este disponible.

### Asegurarse que el frontend tenga sus dependencias
```
    cd DIRECTORIO_REPOSITORIO/theme/static_src
    npm i
```

### <a id="runproyect"></a>Correr el proyecto
En el directorio del proyecto, abrir una terminal y utilizar el siguiente comando
```
    docker compose -f ./pwd.yml up
```
Esto levantara el servicio de base de datos(MariaDB)(:33060) junto a un administrador de base de datos (Adminer)(:8081).
Abrir otra terminal, activar el entorno virtual (con source bin/activate, alternativamente, . bin/activate)
```
    ./portal/manage.py runserver
```
Abrir otra terminal con el entorno virtual
```
    ./portal/manage.py tailwind start
```
Esto comenzara el servidor de NodeJS encargado de gestionar tailwind.

Alternativamente se puede utilizar el script run.sh en el proyecto.
```
    sh run.sh
```

## Organizacion del proyecto
```
./portal
├── core/
├── manage.py
├── media/
├── theme/
├── wiki/
└── wikiapp/
```

Este tiene por nombre generico "portal/wiki", este directorio contiene.
El proyecto, de momento. Esta organizado en las siguientes aplicaciones:
- wikiapp: Nombre generico de la aplicacion. Esta de momento, solo contiene la gestion de los menues. Estos menues son dinamicos y se pueden agregar al navbar agregando las entidad correspondientes. **Queda pendiente gestionar la visibilidad por permisos del grupo/usuario**.
- core: Implementacion base de la gestion de la wiki.
- theme: **Frontend** principalmente. Posee contenido estatico
- media
A su vez, el proyecto posee 'portal' posee dos directorios mas. 
Cada aplicacion, posee su conjunto de endpoints en los archivos **urls.py**. Por ejemplo, para el caso de 'core', tenemos core/urls.py, o para 'wikiapp', wikiapp/urls.py

## Ideas (Para alcanzar objetivos)
- El servicio del contenido estatico deberia ser delegada a un servidor http como NGINX o Apache.
- La busqueda y organizacion de los archivos se pueden realizar mediante Elastic Search, esta herramienta es generalmente deployada utilizando contenedores y docker. Posee un diseno RESTful por lo que se podria llegar a integrar a este proyecto.
- Se pueden utilizar librerias como PyMuPdf para leer PDFs de manera eficiente, y PyTesseract para escaneado de PDFs.

## Que fue implementado
- Jerarquia de secciones/archivos con ABMs modulares. Permisos por usuarios y grupos a cada instancia de la entidad.
- Menues dinamicos (Se pueden ir agregando en la base de datos).
- Frontend dinamico con HTMX y AlpineJS.

## Como agregar permisos a cada seccion
En este ejemplo, se agrega el permiso para la seccion de id=1, para que el usuario "admin01" pueda agregar
mas secciones en este.

### Por usuario
Para entender esto, es necesario entender que las foreign keys(ManyToOne) del lado no dominante resultan en una lista.
Este seria el flujo si utilizariamos la herramienta (manage.py shell).
```
from core.models import Section, User
from django.contrib.auth.models import Permission

admin = User.objects.get(username="admin01")
section = Section.objects.get(id=1)
add_section_perm = Permission.objects.get(codename="add_section")
user_perm = admin.usersectionpermission_set.create(user=user,)
user_perm.permissions.add(add_section_perm)
```
### Por grupo
```
from core.models import Section, Group
from django.contrib.auth.models import Permission

group = Group.objects.get(name="admin")
section = Section.objects.get(id=1)
add_section_perm = Permissions.objects.get(codename="add_section")
user_perm = group.groupsectionpermission_set.create(group=group, section=section)
user_perm.permissions.add(add_section_perm)
```
