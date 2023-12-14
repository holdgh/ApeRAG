from django.apps import AppConfig


class KubechatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kubechat"


class QuotaType:
    MAX_BOT_COUNT = 'max_bot_count'
    MAX_COLLECTION_COUNT = 'max_collection_count'
    MAX_DOCUMENT_COUNT = 'max_document_count'
    MAX_CONVERSATION_COUNT = 'max_conversation_count'


