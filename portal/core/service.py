from typing import Dict
from django.core.files import File
import requests
import json
import logging
from django.conf import settings

# Hacer una clase para abstraer ambos servicios

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

    def search_by_content(self, *, index: str, content: str, extra: dict):
        resource = "{index_name}/_search".format(index_name=index)
        url = "{url}/{resource}".format(url=self.url, resource=resource)
        headers = {
            "Content-Type": "application/json"
        }

        filters = []
        ext = extra.get("extension")
        if ext: 
            filters.append({
                "term": {
                    "file.extension": ext
                }
            })

        body = {
            "query": {
                "query_string": {
                    "query": content
                }
            }
        }
        res = self.session.get(url, data=json.dumps(body), headers=headers)
        return json.loads(res.content)

    def delete_document(self, *, index: str, doc_id: str):
        resource = "{index_name}/_doc/{doc_id}".format(index_name=index, doc_id=doc_id)
        url = "{url}/{resource}".format(url=self.url, resource=resource)
        r = self.session.delete(url)
        return json.loads(r.content)

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

    def test_upload_file(self, *, file: File) -> Dict:
        url = "{}/{}".format(self.url, "_document?debug=true&simulate=true&id=_auto_")
        filemap = {
            "file": file.file
        }
        res = self.session.post(url, files=filemap)
        return json.loads(res.content)

    def upload_file(self, *, file: File) -> Dict:
        """
        Carga un archivo a elasticsearch utilizando el servicio de FsCrawler 
        para usar el OCR de Tika.
        """
        url = "{}/{}".format(self.url, "_document?id=_auto_")
        filemap = {
            "file": file.file
        }
        res = self.session.post(url, files=filemap)
        return json.loads(res.content)

fscrawler_service = FsCrawlerService()
