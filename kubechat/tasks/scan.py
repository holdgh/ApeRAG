import json

from config.celery import app
from kubechat.models import Collection

from .index import CustomLoadDocumentTask
from .local_directory_task import update_local_directory_index


@app.task(base=CustomLoadDocumentTask, time_limit=300, soft_time_limit=180)
def scan_collection(collection_id):
    collection = Collection.objects.get(id=collection_id)

    config = json.loads(collection.config)

    match config["source"]:
        case "system":
            pass
        case "local":
            from kubechat.source.local import scanning_dir_add_index

            scanning_dir_add_index(config["path"], collection)
        case "s3":
            from kubechat.source.s3 import scanning_s3_add_index

            scanning_s3_add_index(
                config["bucket"],
                config["access_key_id"],
                config["secret_access_key"],
                config["region"],
                collection,
            )
        case "oss":
            from kubechat.source.oss import scanning_oss_add_index

            scanning_oss_add_index(
                config["bucket"],
                config["access_key_id"],
                config["secret_access_key"],
                config["region"],
                config["dir"],
                collection,
            )
        case "ftp":
            from kubechat.source.ftp import scanning_ftp_add_index

            scanning_ftp_add_index(
                config["path"],
                config["host"],
                config["port"],
                config["username"],
                config["password"],
                collection,
            )
        case "email":
            from kubechat.source.email import scanning_email_add_index

            scanning_email_add_index(
                config["pop_server"],
                config["port"],
                config["email_address"],
                config["email_password"],
                collection,
            )


@app.task(base=CustomLoadDocumentTask)
def get_collections_cron_job():
    collections = Collection.objects.all()
    for collection in collections:
        # todo: need User Balanced Solutions to make sure that tasks are not filled with large users
        config = json.loads(collection.config)
        if config["source"] == "system":
            config
        if config["source"] == "local":
            update_local_directory_index.delay(collection.user, collection.id)
