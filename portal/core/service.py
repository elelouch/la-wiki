import requests
import json
from django.conf import settings

class ElasticSearchService:
    def __init__(self):
        session = requests.Session()
        # setup CA/Cert
        # session.verify = "/ca/cert/path"

        # False - No proxy, True - proxy
        session.trust_env = False
        self.url = settings.ES_URL
        api_key = settings.ES_APIKEY
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = "Bearer {}".format()
        else:
            session.auth = ("elastic", settings.ES_PASSWORD)

    def test_service(self):
        r = requests.get(self.url, headers=self.headers)
        content = r.content
        return json.loads(content)