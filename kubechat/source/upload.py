import os
from typing import Dict, Any

from kubechat.models import Document, Collection
from kubechat.source.base import Source
from kubechat.source.utils import gen_temporary_file


class UploadSource(Source):

    def __init__(self, collection: Collection, ctx: Dict[str, Any]):
        super().__init__(ctx)

    def scan_documents(self):
        return []

    def prepare_document(self, doc: Document):
        with doc.file.open("rb") as f:
            content = f.read()
        temp_file = gen_temporary_file(doc.name)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def cleanup_document(self, file_path: str, doc: Document):
        os.remove(file_path)

    def close(self):
        pass
