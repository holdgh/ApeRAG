from config import celery
from ..models import Collection, CollectionStatus, Document, DocumentStatus


@celery.app.task
def add_document(collection_id):
    pass
