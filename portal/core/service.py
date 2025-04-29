from typing import Dict
import requests
import json
import logging
from django.conf import settings

# Make a simpler service that can a Generic Rest Service 

class ElasticSearchService:
    def __init__(self):
        logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(filename='myapp.log', level=logging.INFO)
        session = requests.Session()
        # setup CA/Cert
        # session.verify = "ca/cert/path"
        session.trust_env = False # False - no proxy; True - use proxy
        api_key = settings.ELASTIC_KEY
        if api_key:
            logger.info("API KEY available, using Bearer header")
            headers = {"Authorization": "Bearer {}".format(api_key)} 
            session.headers.update(headers)
        else:
            logger.info("API KEY not availabe, using Basic header")
            password = settings.ELASTIC_PASSWORD
            session.auth = ("elastic", password)

        self.logger = logger
        self.session = session
        self.url = settings.ELASTIC_URL

    def test_service(self) -> Dict:
        res = self.session.get(self.url)
        return json.loads(res.content)

elastic_service = ElasticSearchService()

class FsCrawlerService:
    def __init__(self):
        logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(filename='myapp.log', level=logging.INFO)
        session = requests.Session()
        # setup CA/Cert
        # session.verify = "ca/cert/path"
        session.trust_env = False # False - no proxy; True - use proxy
        api_key = settings.FSCRAWLER_KEY
        if api_key:
            logger.info("API KEY found, using Bearer header")
            headers = {"Authorization": "Bearer {}".format(api_key)} 
            session.headers.update(headers)
        else:
            logger.info("API KEY not found, using Basic header")
            session.auth = ("", "")

        self.logger = logger
        self.session = session
        self.url = settings.FSCRAWLER_URL

    def test_service(self) -> Dict:
        res = self.session.get(self.url)
        return json.loads(res.content)

fscrawler_service = FsCrawlerService()
