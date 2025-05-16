from typing import Dict, List
from django.core.files import File
import requests
import json
import logging
import re
from django.conf import settings

# Hacer una clase para abstraer ambos servicios

class ElasticSearchService:
    def __init__(self):
        logger = logging.getLogger(self.__class__.__name__)
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
        assert str and content
        resource = "{index_name}/_search".format(index_name=index)
        url = "{url}/{resource}".format(url=self.url, resource=resource)
        headers = { "Content-Type": "application/json" }
        filters = []
        ext = extra.get("extension")
        if ext: 
            filters.append({
                "term": {
                    "file.extension": ext
                }
            })

        filtered_values = re.sub("[!&@><$#]", "", content)

        body = {
            "query": {
                "query_string": {
                    "query": filtered_values + "~"
                }
            }
        }

        res = self.session.get(url, data=json.dumps(body), headers=headers)
        return json.loads(res.content)

    def delete_document(self, *, index: str, doc_id: str):
        assert index
        if not doc_id:
            return
        try:
            resource = "{index_name}/_doc/{doc_id}".format(index_name=index, doc_id=doc_id)
            url = "{url}/{resource}".format(url=self.url, resource=resource)
            r = self.session.delete(url)
            res = json.loads(r.content)
            if res["result"] == "not_found":
                err_str = "Doc ID:{id} not found in elasticsearch"
                err_str.format(id=doc_id)
                self.logger.warning(err_str)
        except requests.RequestException as exc:
            self.logger.warning("Elasticsearch service might not be available.")
            self.logger.warning(exc.strerror)

    def bulk_delete(self, *, index: str, docs_id: List[str]):
        """
        filter_path=items.*.error muestra solo aquellos que tuvieron errores
        """
        assert index
        try:
            resource = "_bulk?pretty=true&filter_path=items.*.error"
            url = "{url}/{resource}".format(url=self.url, resource=resource)
            bulk = [{"delete": {"_index": index, "_id": id}} for id in docs_id]
            headers = {"Content-Type": "application/json"}
            bulk_str = "\n".join(json.dumps(item) for item in bulk) + "\n"
            r = self.session.post(url, data=bulk_str, headers=headers)
            res = json.loads(r.content)
            if res:
                err_str = "Errors during bulk delete, list used:{docs_id} "
                err_str_formatted = err_str.format(docs_id=docs_id)
                self.logger.warning(err_str_formatted)
                self.logger.warning(r.content)
        except requests.RequestException as exc:
            self.logger.warning("Elasticsearch service might not be available.")
            self.logger.warning(exc.strerror)

elastic_service = ElasticSearchService()

class FsCrawlerService:
    def __init__(self):
        logger = logging.getLogger(self.__class__.__name__)
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
        try:
            res = self.session.get(self.url)
            return json.loads(res.content)
        except requests.RequestException as re: 
            self.logger.error(re.strerror)
            raise 

    def test_upload_file(self, *, file: File) -> Dict:
        url = "{}/{}".format(self.url, "_document?debug=true&simulate=true&id=_auto_")
        filemap = {
            "file": file.file
        }
        res = self.session.post(url, files=filemap)
        return json.loads(res.content)

    def __upload_file(self, *, file: File) -> Dict:
        """
        Carga un archivo a elasticsearch utilizando el servicio de FsCrawler 
        para usar el OCR de Tika.
        """
        assert file
        url = "{}/{}".format(self.url, "_document?id=_auto_")
        filemap = {
            "file": file.file
        }
        res = self.session.post(url, files=filemap)
        return json.loads(res.content)

    def upload_file(self, *, file: File) -> str:
        assert file
        try:
            fsc_res = self.__upload_file(file=file)
            if not fsc_res.get("ok"):
                err = "Couldn't upload {doc} document to Elasticsearch through FsCrawler"
                err.format(doc=file.name)
                self.logger.info(err)
                return ""
            url = fsc_res["url"]
            archive_uuid = url.split("/")[-1]
            return archive_uuid
        except requests.RequestException as err:
            self.logger.warning("FsCrawler service not available")
            self.logger.warning(err.strerror)
            return ""

fscrawler_service = FsCrawlerService()
