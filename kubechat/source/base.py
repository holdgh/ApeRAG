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

    @abstractmethod
    def cleanup_document(self, file_path: str, doc: Document):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def sync_enabled(self):
        pass


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
