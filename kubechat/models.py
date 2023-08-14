from django.db import models
from django.contrib import admin
from django.utils.html import format_html
import re
from django.db.models import IntegerField
from django.db.models.functions import Cast


def user_document_path(instance, filename):
    user = instance.user.replace("|", "-")
    return "documents/user-{0}/collection-{1}/{2}".format(
        user, instance.collection.id, filename
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

    # for code-generate
    CLARIFYING = "CLARIFYING"
    CLARIFIED = "CLARIFIED"
    FINISHED = "FINISHED"
    UPLOADED = "UPLOADED"


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

    def view(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "type": self.type,
            "config": self.config,
            "created": self.gmt_created.isoformat(),
            "updated": self.gmt_updated.isoformat(),
        }


class Document(models.Model):
    name = models.CharField(max_length=1024)
    user = models.CharField(max_length=256)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=DocumentStatus.choices)
    size = models.BigIntegerField()
    file = models.FileField(upload_to=user_document_path)
    relate_ids = models.TextField()
    metadata = models.TextField()
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_updated = models.DateTimeField(auto_now=True)
    gmt_deleted = models.DateTimeField(null=True, blank=True)

    def view(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "status": self.status,
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

class Chat(models.Model):
    user = models.CharField(max_length=256)
    status = models.CharField(max_length=16, choices=ChatStatus.choices)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    # currently, we use the first message in the history as summary
    codetype = models.CharField(max_length=16, choices=CodeChatType.choices)
    summary = models.TextField()
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_updated = models.DateTimeField(auto_now=True)
    gmt_finished = models.DateTimeField(null=True, blank=True)
    gmt_deleted = models.DateTimeField(null=True, blank=True)

    def view(self, collection_id, messages=None):
        if messages is None:
            messages = []
        return {
            "id": str(self.id),
            "summary": self.summary,
            "collection_id": collection_id,
            "history": messages,
            "created": self.gmt_created.isoformat(),
            "updated": self.gmt_updated.isoformat(),
        }


# class CodeChat(models.Model):
#     user = models.CharField(max_length=256)
#     title = models.CharField(max_length=32)
#     type = models.CharField(max_length=16, choices=CodeChatType.choices)
#     status = models.CharField(max_length=16, choices=CodeChatStatus.choices)
#     summary = models.TextField()
#     gmt_created = models.DateTimeField(auto_now_add=True)
#     gmt_finished = models.DateTimeField(null=True, blank=True)
#     gmt_deleted = models.DateTimeField(null=True, blank=True)
#
#     def view(self, history=None):
#         if history is None:
#             history = []
#         return {
#             "id": str(self.id),
#             "summary": self.summary,
#             "history": history,
#             "created": self.gmt_created.isoformat(),
#             "finished:": self.gmt_finished.isoformat(),
#         }


class Settings(models.Model):
    key = models.CharField(max_length=512)
    value = models.TextField()
