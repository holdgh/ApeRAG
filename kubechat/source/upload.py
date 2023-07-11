import os
import tempfile
from typing import Dict, Any

from kubechat.models import Document, Collection
from kubechat.source.base import Source


class UploadSource(Source):

    def __init__(self, collection: Collection, ctx: Dict[str, Any]):
        super().__init__(ctx)

    def scan_documents(self):
        return []

    def prepare_document(self, doc: Document):
        suffix = os.path.splitext(doc.name)[1].lower()
        with doc.file.open("rb") as f:
            content = f.read()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def cleanup_document(self, file_path: str, doc: Document):
        os.remove(file_path)

    def close(self):
        pass
