from config import celery


@celery.task
def remove_document(document_id):
    pass