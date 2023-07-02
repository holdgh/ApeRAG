import glob
import os
import time

from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile

from kubechat.tasks.index import add_index_for_document
from kubechat.models import Document, DocumentStatus, CollectionStatus

from readers.Readers import DEFAULT_FILE_READER_CLS

import logging
import oss2

logger = logging.getLogger(__name__)


def connect_to_oss(access_key_id, access_key_secret, bucket_name, endpoint):
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    return bucket


def list_files(bucket):  # 可能没有用
    for obj in oss2.ObjectIterator(bucket):
        print(obj.key)


def read_file(bucket, filename):
    try:
        file_content = bucket.get_object(filename).read()
        return file_content
    except Exception as e:
        logger.error(f"Error in reading file {filename} from OSS: {e}")
        return None


def scanning_oss_add_index(b_name: str, id, secret, ep, collection):

    collection.status = CollectionStatus.INACTIVE
    collection.save()
    bucket = connect_to_oss(access_key_id=id, access_key_secret=secret, bucket_name=b_name, endpoint=ep)

    try:
        for obj in oss2.ObjectIterator(bucket):
            if os.path.splitext(obj.key)[1].lower() in DEFAULT_FILE_READER_CLS.keys():
                document_instance = Document(
                    user=collection.user,
                    name=obj.key,
                    status=DocumentStatus.PENDING,
                    size=obj.size,
                    collection=collection,
                    metadata=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(obj.last_modified))
                )
                document_instance.save()
                add_index_for_document.delay(document_instance.id)
    except Exception as e:
        logger.error(f"scanning_oss_add_index() error {e}")

    collection.status = CollectionStatus.ACTIVE
    collection.save()





