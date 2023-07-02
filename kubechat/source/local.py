import glob
import logging
import os
import time
from typing import Optional

from kubechat.tasks.index import add_index_for_document
from kubechat.models import Document, DocumentStatus, CollectionStatus, Collection

from readers.Readers import DEFAULT_FILE_READER_CLS

logger = logging.getLogger(__name__)


def scanning_dir_add_index(dir: str, collection: Optional[Collection]):
    if not os.path.isdir(dir):
        logger.error(f"{dir} is not a dir")
        return
    collection.status = CollectionStatus.INACTIVE
    collection.save()

    logger.debug(f"phrase dir is {dir}")
    try:
        for root, dirs, files in os.walk(dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.splitext(file_path)[1].lower() in DEFAULT_FILE_READER_CLS.keys():
                    # maybe add a field to record the local file ref rather than upload local file
                    file_stat = os.stat(file_path)
                    document_instance = Document(
                        user=collection.user,
                        name=file_path,
                        status=DocumentStatus.PENDING,
                        size=file_stat.st_size,
                        collection=collection,
                        metadata=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_stat.st_mtime))
                    )
                    document_instance.save()
                    add_index_for_document.delay(document_instance.id, file_path)

    except Exception as e:
        logger.error(f"scanning_dir_add_index() error {e}")


    collection.status = CollectionStatus.ACTIVE
    collection.save()
