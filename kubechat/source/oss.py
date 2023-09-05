import logging
from datetime import datetime
from typing import Dict, Any, List

import oss2

from kubechat.source.base import Source, RemoteDocument, LocalDocument
from kubechat.source.utils import gen_temporary_file

logger = logging.getLogger(__name__)


class OSSSource(Source):

    def __init__(self, ctx: Dict[str, Any]):
        super().__init__(ctx)
        self.access_key_id = ctx["access_key_id"]
        self.access_key_secret = ctx["secret_access_key"]
        self.bucket_name = ctx["bucket"]
        self.endpoint = ctx["region"]
        self.dir = ctx.get("dir", "")
        self.bucket = self._connect_bucket()

    def _connect_bucket(self):
        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
        return bucket

    def scan_documents(self) -> List[RemoteDocument]:
        documents = []
        for obj in oss2.ObjectIterator(self.bucket, prefix=self.dir):  # get file in given directory
            try:
                doc = RemoteDocument(
                    name=obj.key,
                    size=obj.size,
                    metadata={
                        "modified_time": datetime.utcfromtimestamp(int(obj.last_modified)),
                    }
                )
                documents.append(doc)
            except Exception as e:
                logger.error(f"scanning_oss_add_index() {obj.key} error {e}")
                raise e
        return documents

    def prepare_document(self, name: str, metadata: Dict[str, Any]) -> LocalDocument:
        content = self.bucket.get_object(name).read()
        temp_file = gen_temporary_file(name)
        temp_file.write(content)
        temp_file.close()
        metadata["name"] = name
        return LocalDocument(name=name, path=temp_file.name, metadata=metadata)

    def sync_enabled(self):
        return True
