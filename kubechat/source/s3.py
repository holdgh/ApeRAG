import boto3
import os
import time
import tempfile

from kubechat.tasks.index import add_index_for_document
from kubechat.models import Document, DocumentStatus, CollectionStatus
from kubechat.tasks.local_directory_task import cron_collection_metadata
from readers.Readers import DEFAULT_FILE_READER_CLS

import logging
logger = logging.getLogger(__name__)


def connect_to_s3(access_key_id, access_key_secret, bucket_name, region):
    s3 = boto3.resource('s3',
                        aws_access_key_id=access_key_id,
                        aws_secret_access_key=access_key_secret,
                        region_name=region)
    bucket = s3.Bucket(bucket_name)
    return bucket


def list_files(bucket):
    for obj in bucket.objects.all():
        print(obj.key)


def scanning_s3_add_index(bucket_name, access_key_id, access_key_secret, region, collection):
    collection.status = CollectionStatus.INACTIVE
    collection.save()
    bucket = connect_to_s3(access_key_id, access_key_secret, bucket_name, region)

    try:
        for obj in bucket.objects.all():
            file_suffix = os.path.splitext(obj.key)[1].lower()
            if file_suffix in DEFAULT_FILE_READER_CLS.keys():
                file_content = obj.get()["Body"].read()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix)
                temp_file.write(file_content)
                temp_file.close()
                document_instance = Document(
                    user=collection.user,
                    name=obj.key,
                    status=DocumentStatus.PENDING,
                    size=obj.size,
                    collection=collection,
                    # metadata=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(obj.last_modified))
                )
                document_instance.save()
                add_index_for_document.delay(document_instance.id, temp_file.name)
    except Exception as e:
        logger.error(f"scanning_s3_add_index() error {e}")

    collection.status = CollectionStatus.ACTIVE
    collection.save()

    cron_collection_metadata.append({"user": collection.user, "id": collection.id})