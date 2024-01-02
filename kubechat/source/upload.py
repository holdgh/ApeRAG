from typing import Any, Dict, Iterator

from minio import Minio
from config import settings
from kubechat.source.base import LocalDocument, RemoteDocument, Source
from kubechat.source.utils import gen_temporary_file


class UploadSource(Source):

    def __init__(self, ctx: Dict[str, Any]):
        super().__init__(ctx)

    def scan_documents(self) -> Iterator[RemoteDocument]:
        return iter([])

    def prepare_document(self, name: str, metadata: Dict[str, Any]) -> LocalDocument:
        bucket_name = metadata.get("bucket_name", "")
        object_name = metadata.get("object_name", "")
        path = metadata.get("path", "")
        if bucket_name and object_name:
            client = Minio(settings.MINIO_ENDPOINT, settings.MINIO_ACCESS_KEY, settings.MINIO_SECRET_KEY)
            try:
                response = client.get_object(bucket_name, object_name)
                content = response.read()
            finally:
                response.close()
                response.release_conn()
        elif path:
            with open(path, "rb") as f:
                content = f.read()
        else:
            raise Exception("failed to prepare uploaded file")
        temp_file = gen_temporary_file(name)
        temp_file.write(content)
        temp_file.close()
        metadata["name"] = name
        return LocalDocument(name=name, path=temp_file.name, metadata=metadata)

    def sync_enabled(self):
        return False
