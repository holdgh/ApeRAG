import json

from config.celery import app
from kubechat.models import Collection, CollectionType, CollectionStatus
from .index import CustomLoadDocumentTask


@app.task(base=CustomLoadDocumentTask, time_limit=300, soft_time_limit=180)
def scan_collection(collection_id):
    collection = Collection.objects.get(id=collection_id)

    config = json.loads(collection.config)

    if config["source"] == "system":
        pass
    elif config["source"] == "local":
        from kubechat.source.local import scanning_dir_add_index
        scanning_dir_add_index(config["path"], collection)
    elif config["source"] == "s3":
        from kubechat.source.s3 import scanning_s3_add_index
        scanning_s3_add_index(config["bucket"], config["access_key_id"], config["secret_access_key"],
                              config["region"], collection)
    elif config["source"] == "oss":
        from kubechat.source.oss import scanning_oss_add_index
        scanning_oss_add_index(config["bucket"], config["access_key_id"], config["secret_access_key"],
                               config["region"], collection)
    elif config["source"] == "ftp":
        from kubechat.source.ftp import scanning_dir_add_index_from_ftp
        scanning_dir_add_index_from_ftp(config["path"], config["host"], config["username"], config["password"],
                                        collection)
    elif config["source"] == "email":
        pass
