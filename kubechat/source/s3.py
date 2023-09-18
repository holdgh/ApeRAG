import logging
from datetime import datetime
from typing import Dict, Any, List, Iterator

import boto3

from kubechat.source.base import Source, RemoteDocument, LocalDocument
from kubechat.source.utils import gen_temporary_file

logger = logging.getLogger(__name__)


class S3Source(Source):

    def __init__(self, ctx: Dict[str, Any]):
        super().__init__(ctx)
        self.access_key_id = ctx["access_key_id"]
        self.access_key_secret = ctx["secret_access_key"]
        self.bucket_name = ctx["bucket"]
        self.region = ctx["region"]
        self.dir = ctx.get("dir", "")
        self.bucket = self._connect_bucket()

    def _connect_bucket(self):
        s3 = boto3.resource(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.access_key_secret,
            region_name=self.region,
        )
        return s3.Bucket(self.bucket_name)

    def scan_documents(self) -> Iterator[RemoteDocument]:
        for obj in self.bucket.objects.filter(Prefix=self.dir):
            try:
                doc = RemoteDocument(
                    name=obj.key,
                    size=obj.size,
                    metadata={
                        "modified_time": datetime.utcfromtimestamp(int(obj.last_modified)),
                    }
                )
                yield doc
            except Exception as e:
                logger.error(f"scanning_s3_add_index() {obj.key} error {e}")
                raise e

    def prepare_document(self, name: str, metadata: Dict[str, Any]) -> LocalDocument:
        obj = self.bucket.Object(name)
        content = obj.get()["Body"].read()
        temp_file = gen_temporary_file(name)
        temp_file.write(content)
        temp_file.close()
        metadata["name"] = name
        return LocalDocument(name=name, path=temp_file.name, metadata=metadata)

    def sync_enabled(self):
        return True
