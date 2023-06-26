from django.db import models


def user_document_path(instance, filename):
    return "documents/user-{0}/collection-{1}/{2}".format(instance.user.id, instance.collection.id, filename)


class CollectionStatus(models.TextChoices):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class CollectionType(models.TextChoices):
    DOCUMENT = "document"
    MULTIMEDIA = "multimedia"


class DocumentStatus(models.TextChoices):
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    DELETED = "DELETED"


class Collection(models.Model):
    title = models.CharField(max_length=256)
    description = models.TextField()
    user = models.CharField(max_length=256)
    status = models.CharField(max_length=16, choices=CollectionStatus.choices)
    type = models.CharField(max_length=16, choices=CollectionType.choices)
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_updated = models.DateTimeField(auto_now=True)
    gmt_deleted = models.DateTimeField(null=True, blank=True)


class Document(models.Model):
    name = models.CharField(max_length=64)
    user = models.CharField(max_length=256)
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE
    )
    status = models.CharField(max_length=16, choices=DocumentStatus.choices)
    size = models.BigIntegerField()
    file = models.FileField(upload_to=user_document_path)
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_deleted = models.DateTimeField()


class Chat(models.Model):
    name = models.CharField(max_length=64)
    user = models.CharField(max_length=256)
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE
    )
    history = models.TextField()
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_updated = models.DateTimeField(auto_now=True)
    gmt_deleted = models.DateTimeField()


class Settings(models.Model):
    key = models.CharField(max_length=512)
    value = models.TextField()
