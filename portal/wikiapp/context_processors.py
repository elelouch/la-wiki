from django.http import HttpRequest
from wikiapp.models import Menu


def available_menus(request: HttpRequest):
    user = request.user
    if user :
        available_menus = Menu.objects.filter(groups__user__id=user.id)
        return {"available_menus": available_menus}

    return {}
