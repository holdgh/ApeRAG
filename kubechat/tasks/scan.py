import json

from celery import Task

from config.celery import app
from kubechat.models import Collection, CollectionStatus

from .local_directory_task import update_local_directory_index
from kubechat.tasks.index import add_index_for_document
from kubechat.source.base import Source, get_source


class CustomScanTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        collection_id = args[0]
        collection = Collection.objects.get(id=collection_id)
        collection.status = CollectionStatus.ACTIVE
        collection.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # todo: when scan fail we should do something
        raise exc
        # collection_id = args[0]
        # collection = Collection.objects.get(id=collection_id)
        # collection.status = CollectionStatus.INACTIVE
        # collection.save()


@app.task(base=CustomScanTask, bind=True, ignore_result=True)
def scan_collection(self, collection_id):
    collection = Collection.objects.get(id=collection_id)
    collection.status = CollectionStatus.INACTIVE
    collection.save()
    source = get_source(collection, json.loads(collection.config))
    if source is None:
        return
    try:
        documents = source.scan_documents()
    except Exception as e:
        raise self.retry(exc=e, countdown=5, max_retries=3)

    for document in documents:
        document.save()
        add_index_for_document.delay(document.id)
    source.close()


@app.task()
def get_collections_cron_job():
    collections = Collection.objects.all()
    for collection in collections:
        # todo: need User Balanced Solutions to make sure that tasks are not filled with large users
        config = json.loads(collection.config)
        if config["source"] == "system":
            config
        if config["source"] == "local":
            update_local_directory_index.delay(collection.user, collection.id)
