from config import celery

@celery.task
def add_document(document_id):
    pass

