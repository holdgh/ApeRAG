import sys

from django.apps import AppConfig
import asyncio

from django.db import transaction
from asgiref.sync import sync_to_async


class KubechatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kubechat"

    def ready(self):
        # if manage.py is running, this might be a migration, so we don't need to load quotas
        if "manage.py" in sys.argv:
            return

        if asyncio.get_event_loop().is_running():
            # call load_quotas() asynchronously in uvicorn
            asyncio.create_task(sync_to_async(load_quotas)())
        else:
            # call load_quotas() after the commit transaction in celery
            transaction.on_commit(load_quotas)


class DefaultQuota:
    MAX_BOT_COUNT = None
    MAX_COLLECTION_COUNT = None
    MAX_DOCUMENT_COUNT = None
    MAX_CONVERSATION_COUNT = None


class QuotaType:
    MAX_BOT_COUNT = 'max_bot_count'
    MAX_COLLECTION_COUNT = 'max_collection_count'
    MAX_DOCUMENT_COUNT = 'max_document_count'
    MAX_CONVERSATION_COUNT = 'max_conversation_count'


def load_quotas():
    from kubechat.db.ops import query_quota

    DefaultQuota.MAX_BOT_COUNT = query_quota(QuotaType.MAX_BOT_COUNT)
    DefaultQuota.MAX_COLLECTION_COUNT = query_quota(QuotaType.MAX_COLLECTION_COUNT)
    DefaultQuota.MAX_DOCUMENT_COUNT = query_quota(QuotaType.MAX_DOCUMENT_COUNT)
    DefaultQuota.MAX_CONVERSATION_COUNT = query_quota(QuotaType.MAX_CONVERSATION_COUNT)
