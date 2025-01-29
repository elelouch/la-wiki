from wikiapp.models import Menu

class MenuMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user :
            Menu.objects.

        return response

