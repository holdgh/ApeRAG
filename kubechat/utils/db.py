from kubechat.models import Collection, CollectionStatus, Document, DocumentStatus, Chat, ChatStatus


def query_collection(user, collection_id: str):
    return Collection.objects.exclude(status=CollectionStatus.DELETED).get(user=user, pk=collection_id)


def query_collections(user):
    return Collection.objects.exclude(status=CollectionStatus.DELETED).filter(user=user)


def query_document(user, collection_id: str, document_id: str):
    return Document.objects.exclude(status=DocumentStatus.DELETED).get(user=user, collection_id=collection_id,
                                                                       pk=document_id)


def query_documents(user, collection_id: str):
    return Document.objects.exclude(status=DocumentStatus.DELETED).filter(user=user, collection_id=collection_id)


def query_chat(user, collection_id: str, chat_id: str):
    return Chat.objects.exclude(status=DocumentStatus.DELETED).get(user=user, collection_id=collection_id, pk=chat_id)


def query_chats(user, collection_id: str):
    return Chat.objects.exclude(status=DocumentStatus.DELETED).filter(user=user, collection_id=collection_id)

