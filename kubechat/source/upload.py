from typing import Dict, Any

from kubechat.models import Document, Collection
from kubechat.source.base import Source


class UploadSource(Source):

    def __init__(self, collection: Collection, ctx: Dict[str, Any]):
        super().__init__(ctx)

    def scan_documents(self):
        return []

    def prepare_document(self, doc: Document):
        return doc.file.name

    def cleanup_document(self, file_path: str, doc: Document):
        pass

    def close(self):
        pass
