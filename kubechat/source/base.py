import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any

from kubechat.models import Document


class Source(ABC):
    def __init__(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    @abstractmethod
    def scan_documents(self):
        pass

    @abstractmethod
    def prepare_document(self, doc: Document):
        pass

    def cleanup_document(self, file_path: str, doc: Document):
        os.remove(file_path)
        os.remove(f"{file_path}.metadata")

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def sync_enabled(self):
        pass

    @staticmethod
    def get_metadata(file_path: str):
        metadata_file = f"{file_path}.metadata"
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                return json.loads(f.read())
        return {}

    @staticmethod
    def prepare_metadata_file(file_path: str, doc: Document, metadata: Dict[str, Any] = None):
        if not metadata:
            metadata = {}

        if doc.config:
            config = json.loads(doc.config)
            result = ["%s=%s" % (item["key"], item["value"]) for item in config["labels"] if item["key"] and item["value"]]
            metadata["labels"] = ' '.join(result)

        file_path = f"{file_path}.metadata"
        with open(file_path, "w") as f:
            f.write(json.dumps(metadata))


def get_source(collection, ctx: Dict[str, Any]):
    source = None
    match ctx["source"]:
        case "system":
            from kubechat.source.upload import UploadSource
            source = UploadSource(collection, ctx)
        case "local":
            from kubechat.source.local import LocalSource
            source = LocalSource(collection, ctx)
        case "s3":
            from kubechat.source.s3 import S3Source
            source = S3Source(collection, ctx)
        case "oss":
            from kubechat.source.oss import OSSSource
            source = OSSSource(collection, ctx)
        case "feishu":
            from kubechat.source.feishu import FeishuSource
            source = FeishuSource(collection, ctx)
        case "ftp":
            from kubechat.source.ftp import FTPSource
            source = FTPSource(collection, ctx)
        case "email":
            from kubechat.source.Email import EmailSource
            source = EmailSource(collection, ctx)
    return source
