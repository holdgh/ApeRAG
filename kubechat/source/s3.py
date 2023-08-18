import logging
import os
from typing import Dict, Any

import boto3

from kubechat.models import Collection, Document, DocumentStatus
from kubechat.source.base import Source
from kubechat.source.utils import gen_temporary_file
from readers.Readers import DEFAULT_FILE_READER_CLS

logger = logging.getLogger(__name__)


class S3Source(Source):

    def __init__(self, collection: Collection, ctx: Dict[str, Any]):
        super().__init__(ctx)
        self.access_key_id = ctx["access_key_id"]
        self.access_key_secret = ctx["secret_access_key"]
        self.bucket_name = ctx["bucket"]
        self.region = ctx["region"]
        self.dir = ctx.get("dir", "")
        self.collection = collection
        self.bucket = self._connect_bucket()

    def _connect_bucket(self):
        s3 = boto3.resource(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.access_key_secret,
            region_name=self.region,
        )
        return s3.Bucket(self.bucket_name)

    def scan_documents(self):
        documents = []
        for obj in self.bucket.objects.filter(Prefix=self.dir):
            try:
                file_suffix = os.path.splitext(obj.key)[1].lower()
                if file_suffix in DEFAULT_FILE_READER_CLS.keys():
                    document = Document(
                        user=self.collection.user,
                        name=obj.key,
                        status=DocumentStatus.PENDING,
                        size=obj.size,
                        collection=self.collection,
                        metadata=obj.last_modified.strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    documents.append(document)
            except Exception as e:
                logger.error(f"scanning_s3_add_index() {obj.key} error {e}")
                raise e
        return documents

    def prepare_document(self, doc: Document):
        obj = self.bucket.Object(doc.name)
        content = obj.get()["Body"].read()
        temp_file = gen_temporary_file(doc.name)
        temp_file.write(content)
        temp_file.close()
        self.prepare_metadata_file(temp_file.name, doc)
        return temp_file.name

    def close(self):
        pass

    def sync_enabled(self):
        return True
