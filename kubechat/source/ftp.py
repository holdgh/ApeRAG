import logging
import os
import tempfile
import time
from ftplib import FTP, error_perm
from typing import Dict, Any

from datetime import datetime
from kubechat.models import Document, DocumentStatus, Collection
from kubechat.source.base import Source
from readers.Readers import DEFAULT_FILE_READER_CLS

logger = logging.getLogger(__name__)


class FTPSource(Source):

    def __init__(self, collection: Collection, ctx: Dict[str, Any]):
        super().__init__(ctx)
        self.path = ctx["path"]
        self.host = ctx["host"]
        self.port = ctx["port"]
        self.user = ctx["username"]
        self.password = ctx["password"]
        self.collection = collection
        self.ftp = FTP()
        self.ftp.connect(str(self.host), self.port)
        self.ftp.login(self.user, self.password)

    def _deal_the_path(self, ftp, collection, path="/"):
        documents = []
        ftp.cwd(path)  # Switch to the specified path
        files = ftp.nlst()  # Get the list of files in the current path
        for file in files:
            file_path = os.path.join(path, file)  # Build the full file path
            try:
                ftp.cwd(file_path)  # Try to switch to the specified path (if it's a folder)
                results = self._deal_the_path(
                    ftp, collection, file_path
                )  # Recursively process the subdirectory
                documents.extend(results)
            except error_perm:  # If it's not a folder, process the file
                if os.path.splitext(file)[1].lower() in DEFAULT_FILE_READER_CLS.keys():
                    size = ftp.size(file_path)
                    mtime = ftp.sendcmd('MDTM ' + file_path)[4:]
                    modified_time = datetime.strptime(f"{mtime}", "%Y%m%d%H%M%S")
                    document = Document(
                        user=collection.user,
                        name=file_path,
                        status=DocumentStatus.PENDING,
                        size=size,
                        collection=collection,
                        metadata=modified_time.strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    documents.append(document)
        return documents

    def scan_documents(self):
        return self._deal_the_path(self.ftp, self.collection, self.path)

    def prepare_document(self, doc: Document):
        suffix = os.path.splitext(doc.name)[1].lower()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        self.ftp.retrbinary("RETR " + doc.name, temp_file.write)
        temp_file.close()
        return temp_file.name

    def cleanup_document(self, file_path: str, doc: Document):
        os.remove(file_path)

    def close(self):
        self.ftp.quit()
