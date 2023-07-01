import json
import logging
import os
import time

from celery import Task
from config.celery import app
from kubechat.utils.db import query_collection, query_documents
from readers.Readers import DEFAULT_FILE_READER_CLS
from kubechat.tasks.index import add_index_for_document, remove_index
# app.conf.beat_schedule = {
#     'add-every-60-seconds': {
#         'task': 'blog.tasks.add',
#         'schedule': 60,
#         'args': (16, 16),
#     },
#     'schedule_minus': {
#         'task': 'blog.tasks.minus',
#         'schedule': crontab(minute=5, hour=2),
#         'args': (12, 24),
#     },
# }
cron_collection_metadata = list[dict]
logger = logging.getLogger(__name__)


class filestat():
    def __init__(self, latest_time="", file_size=0):
        self.latest_time = latest_time
        self.file_size = file_size


@app.task
def update_index_cron_job(add_index_for_document=None):
    for metadata in cron_collection_metadata:
        collection = query_collection(user=metadata["user"], collection_id=metadata["id"])
        # scan the directory
        config = json.loads(collection.config)
        docments_in_direct = dict[str:filestat]
        docments_in_db = dict[str:int]
        docments_in_direct = scan_local_direct(config["path"])  # full_filename to file info
        # scan the db
        documents = query_documents(collection.user, collection.id)
        for i, doc in enumerate(documents):
            docments_in_db[doc.name] = i

        for filename in docments_in_direct.keys():
            if filename not in docments_in_db:
                # for added
                add_index_for_document.delay()
                # read from local direct
            else:
                # for update
                if
        # for delete
        for filename in docments_in_direct.keys():
            if filename not in docments_in_direct:
                remove_index.delay()


def scan_local_direct(direct) -> (bool, dict[str:filestat]):
    result = dict[str:filestat]
    try:
        for root, dirs, files in os.walk(direct):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.splitext(file_path)[1].lower() in DEFAULT_FILE_READER_CLS.keys():
                    file_stat = os.stat(file_path)
                    result[file_path] = filestat(
                        latest_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_stat.st_mtime)),
                        file_size=file_stat.st_size)
        return True, result
    except Exception as e:
        logger.error(f"scan_local_direct(): error{e}")
        return False, None
