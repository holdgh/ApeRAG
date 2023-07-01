import boto3
import os
from datetime import datetime
import logging

from kubechat.tasks.index import add_index_for_document
from kubechat.models import Document, DocumentStatus, CollectionStatus
from kubechat.tasks.local_directory_task import cron_collection_metadata
from readers.Readers import DEFAULT_FILE_READER_CLS

logger = logging.getLogger(__name__)


def connect_to_s3(access_key_id, access_key_secret, region_name):
    session = boto3.Session(aws_access_key_id=access_key_id,
                            aws_secret_access_key=access_key_secret,
                            region_name=region_name)
    s3 = session.client("s3")
    return s3


# download all s3 file in the bucket
# in Kubechat/documents/s3/[your_bucket_name]
# which is in .gitignore
def download_file(s3, file_name, bucket_name):
    current_path = os.path.dirname(os.path.abspath(__file__))
    parent_path = os.path.dirname(os.path.dirname(current_path))
    bucket_path = os.path.join(parent_path, "documents", "s3", bucket_name)
    if not os.path.exists(bucket_path):
        os.makedirs(bucket_path)
    file_path = os.path.join(bucket_path, file_name)
    s3.download_file(bucket_name, file_name, file_path)
    return file_path


def scanning_s3_add_index(bucket_name, access_key_id, access_key_secret, region, collection):
    collection.status = CollectionStatus.INACTIVE
    collection.save()
    s3 = connect_to_s3(access_key_id, access_key_secret, region)
    response = s3.list_objects_v2(
        Bucket=bucket_name,
    )
    objs = response['Contents']
    try:
        for obj in objs:
            if os.path.splitext(obj['Key'])[1].lower() in DEFAULT_FILE_READER_CLS.keys():
                document_instance = Document(
                    user=collection.user,
                    name=obj['Key'],
                    status=DocumentStatus.PENDING,
                    size=obj['Size'],
                    collection=collection,
                    metadata=obj['LastModified'].strftime("%Y-%m-%d %H:%M:%S")
                )
                document_instance.save()
                file_path = download_file(s3, obj['Key'], bucket_name)
                add_index_for_document.delay(document_instance.id, file_path)
    except Exception as e:
        logger.error(f"scanning_s3_add_index() error {e}")

    collection.status = CollectionStatus.ACTIVE
    collection.save()

    cron_collection_metadata.append({"user": collection.user, "id": collection.id})
