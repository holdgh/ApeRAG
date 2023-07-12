import logging
import os
import time
from typing import Dict, Any

from kubechat.models import Collection, Document, DocumentStatus
from kubechat.source.base import Source
from readers.Readers import DEFAULT_FILE_READER_CLS

logger = logging.getLogger(__name__)


class LocalSource(Source):

    def __init__(self, collection: Collection, ctx: Dict[str, Any]):
        super().__init__(ctx)
        self.path = ctx["path"]
        self.collection = collection

    def scan_documents(self):
        if not os.path.isdir(self.path):
            logger.error(f"{self.path} is not a dir")
            return

        documents = []
        logger.debug(f"phrase dir is {self.path}")
        for root, dirs, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                if (
                        os.path.splitext(file_path)[1].lower()
                        in DEFAULT_FILE_READER_CLS.keys()
                ):
                    # maybe add a field to record the local file ref rather than upload local file
                    try:
                        file_stat = os.stat(file_path)
                        document = Document(
                            user=self.collection.user,
                            name=file_path,
                            status=DocumentStatus.PENDING,
                            size=file_stat.st_size,
                            collection=self.collection,
                            metadata=time.strftime(
                                "%Y-%m-%d %H:%M:%S", time.localtime(file_stat.st_mtime)
                            ),
                        )
                        documents.append(document)
                    except Exception as e:
                        logger.error(f"scanning local source {file_path} error {e}")
        return documents

    def prepare_document(self, doc: Document):
        return doc.name

    def cleanup_document(self, file_path: str, doc: Document):
        pass

    def close(self):
        pass
