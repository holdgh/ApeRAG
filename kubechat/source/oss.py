import logging
import os
import time
from typing import Dict, Any

import oss2

from kubechat.models import Collection, Document, DocumentStatus
from kubechat.source.base import Source
from kubechat.source.utils import gen_temporary_file
from readers.Readers import DEFAULT_FILE_READER_CLS

logger = logging.getLogger(__name__)


class OSSSource(Source):

    def __init__(self, collection: Collection, ctx: Dict[str, Any]):
        super().__init__(ctx)
        self.access_key_id = ctx["access_key_id"]
        self.access_key_secret = ctx["secret_access_key"]
        self.bucket_name = ctx["bucket"]
        self.endpoint = ctx["region"]
        self.dir = ctx.get("dir", "")
        self.collection = collection
        self.bucket = self._connect_bucket()

    def _connect_bucket(self):
        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
        return bucket

    def scan_documents(self):
        documents = []
        for obj in oss2.ObjectIterator(self.bucket, prefix=self.dir):  # get file in given directory
            try:
                file_suffix = os.path.splitext(obj.key)[1].lower()
                if file_suffix in DEFAULT_FILE_READER_CLS.keys():
                    document = Document(
                        user=self.collection.user,
                        name=obj.key,
                        status=DocumentStatus.PENDING,
                        size=obj.size,
                        collection=self.collection,
                        metadata=time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(obj.last_modified)
                        ),
                    )
                    documents.append(document)
            except Exception as e:
                logger.error(f"scanning_oss_add_index() {obj.key} error {e}")
                raise e
        return documents

    def prepare_document(self, doc: Document):
        content = self.bucket.get_object(doc.name).read()
        temp_file = gen_temporary_file(doc.name)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def cleanup_document(self, file_path: str, doc: Document):
        os.remove(file_path)

    def close(self):
        pass
