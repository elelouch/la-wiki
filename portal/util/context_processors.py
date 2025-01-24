from wikiapp.models import Menu


def sidebar_context(request):
    django
    menus_queryset = Menu.objects.all()
    return { 'menus': menus_queryset,  }
