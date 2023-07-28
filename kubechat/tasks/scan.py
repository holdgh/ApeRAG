import json

from config.celery import app
from kubechat.models import Collection, CollectionStatus

from .index import CustomLoadDocumentTask
from .local_directory_task import update_local_directory_index
from kubechat.tasks.index import add_index_for_document
from kubechat.source.base import Source, get_source


@app.task(base=CustomLoadDocumentTask, time_limit=14400, soft_time_limit=7200)
def scan_collection(collection_id):
    collection = Collection.objects.get(id=collection_id)
    collection.status = CollectionStatus.INACTIVE
    collection.save()

    source = get_source(collection, json.loads(collection.config))
    if source is None:
        return

    for document in source.scan_documents():
        document.save()
        add_index_for_document.delay(document.id)
    source.close()

    collection.status = CollectionStatus.ACTIVE
    collection.save()


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
