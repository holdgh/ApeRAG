from config import celery


@celery.app.task
def remove_document(document_id):
    pass