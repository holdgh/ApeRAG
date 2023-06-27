from config import celery


@celery.app.task
def add_document(collection_id):
    pass
