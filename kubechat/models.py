from django.db import models
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.utils import timezone


def upload_document_path(document, filename):
    user = document.user.replace("|", "-")
    return "documents/user-{0}/collection-{1}/{2}".format(
        user, document.collection.id, filename
    )


def ssl_temp_file_path(filename):
    return "ssl_file/upload_temp/{}".format(filename) if filename is not None else None


def ssl_file_path(instance, filename):
    user = instance.user.replace("|", "-")
    return "ssl_file/user-{0}/collection-{1}/{2}".format(user, instance.id, filename)


class CollectionStatus(models.TextChoices):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class CollectionType(models.TextChoices):
    DOCUMENT = "document"
    DATABASE = "database"
    CODE = "code"


class DocumentStatus(models.TextChoices):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    DELETED = "DELETED"


class ChatStatus(models.TextChoices):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class BotStatus(models.TextChoices):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class CodeChatType(models.TextChoices):
    DEFAULT = "DEFAULT"
    BENCHMARK = "BENCHMARK"
    SIMPLE = "SIMPLE"
    TDD = "TDD"
    TDD_PLUS = "TDD+"
    CLARIFY = "CLARIFY"
    RESPEC = "RESPEC"
    EXECUTE_ONLY = "EXECUTE_ONLY"
    EVALUATE = "EVALUATE"
    USE_FEEDBACK = "USE_FEEDBACK"


class VerifyWay(models.TextChoices):
    PREFERRED = "prefered"
    CAONLY = "ca_only"
    FULL = "full"


class Collection(models.Model):
    title = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    user = models.CharField(max_length=256)
    status = models.CharField(max_length=16, choices=CollectionStatus.choices)
    type = models.CharField(max_length=16, choices=CollectionType.choices)
    config = models.TextField()
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_updated = models.DateTimeField(auto_now=True)
    gmt_deleted = models.DateTimeField(null=True, blank=True)

    def view(self, bot_ids=None):
        if not bot_ids:
            bot_ids = []
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "type": self.type,
            "bot_ids": bot_ids,
            "config": self.config,
            "created": self.gmt_created.isoformat(),
            "updated": self.gmt_updated.isoformat(),
        }


class Document(models.Model):
    name = models.CharField(max_length=1024)
    user = models.CharField(max_length=256)
    config = models.TextField(null=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=DocumentStatus.choices)
    size = models.BigIntegerField()
    file = models.FileField(upload_to=upload_document_path)
    relate_ids = models.TextField()
    metadata = models.TextField(default="{}")
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_updated = models.DateTimeField(auto_now=True)
    gmt_deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('collection', 'name')

    def view(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "status": self.status,
            "config": self.config,
            "size": self.size,
            "created": self.gmt_created.isoformat(),
            "updated": self.gmt_updated.isoformat(),
        }

    # def collection_id(self):
    #     if self.collection:
    #         matches = re.findall(r'\d+', str(self.collection))
    #         return matches[0] if matches else '-'
    #     else:
    #         return '-'

    def collection_id(self):
        if self.collection:
            return Cast(self.collection, IntegerField())
        else:
            return None

    collection_id.short_description = 'Collection ID'
    collection_id.admin_order_field = 'collection'


class Bot(models.Model):
    user = models.CharField(max_length=256)
    title = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=BotStatus.choices)
    config = models.TextField()
    collections = models.ManyToManyField(Collection)
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_updated = models.DateTimeField(auto_now=True)
    gmt_deleted = models.DateTimeField(null=True, blank=True)

    def view(self, collections=None):
        if collections is None:
            collections = []
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "config": self.config,
            "collections": collections,
            "created": self.gmt_created.isoformat(),
            "updated": self.gmt_updated.isoformat(),
        }


class ChatPeer(models.TextChoices):
    SYSTEM = "system"
    FEISHU = "feishu"


class Chat(models.Model):
    user = models.CharField(max_length=256)
    peer_type = models.CharField(max_length=16, default=ChatPeer.SYSTEM, choices=ChatPeer.choices)
    peer_id = models.CharField(max_length=256, null=True)
    status = models.CharField(max_length=16, choices=ChatStatus.choices)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    summary = models.TextField()
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_updated = models.DateTimeField(auto_now=True)
    gmt_deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('peer_type', 'peer_id')

    def view(self, bot_id, messages=None):
        if messages is None:
            messages = []
        return {
            "id": str(self.id),
            "summary": self.summary,
            "bot_id": bot_id,
            "history": messages,
            "created": self.gmt_created.isoformat(),
            "updated": self.gmt_updated.isoformat(),
        }


class MessageFeedbackStatus(models.TextChoices):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class MessageFeedback(models.Model):
    user = models.CharField(max_length=256)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    message_id = models.CharField(max_length=256)
    upvote = models.IntegerField(default=0)
    downvote = models.IntegerField(default=0)
    relate_ids = models.TextField(null=True)
    question = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=MessageFeedbackStatus.choices, null=True)
    original_answer = models.TextField(null=True, blank=True)
    revised_answer = models.TextField(null=True, blank=True)
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_updated = models.DateTimeField(auto_now=True)
    gmt_deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('chat_id', 'message_id')


class CollectionSyncHistory(models.Model):
    user = models.CharField(max_length=256)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    total_documents = models.PositiveIntegerField()
    new_documents = models.PositiveIntegerField(default=0)
    deleted_documents = models.PositiveIntegerField(default=0)
    modified_documents = models.PositiveIntegerField(default=0)
    processing_documents = models.PositiveIntegerField(default=0)
    failed_documents = models.PositiveIntegerField(default=0)
    successful_documents = models.PositiveIntegerField(default=0)
    total_documents_to_sync = models.PositiveIntegerField(default=0)
    execution_time = models.DurationField(null=True)
    start_time = models.DateTimeField()

    def update_execution_time(self):
        self.refresh_from_db()
        self.execution_time = timezone.now() - self.start_time
        self.save()

    def view(self):
        return {
            "id": str(self.id),
            "user": str(self.user),
            "total_documents": self.total_documents,
            "new_documents": self.new_documents,
            "deleted_documents": self.deleted_documents,
            "processing_documents": self.processing_documents,
            "modified_documents": self.modified_documents,
            "failed_documents": self.failed_documents,
            "successful_documents": self.successful_documents,
            "total_documents_to_sync": self.total_documents_to_sync,
            "start_time": self.start_time,
            "execution_time": self.execution_time
        }
