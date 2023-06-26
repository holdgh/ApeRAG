from django.db import models

# Create your models here.


class CollectionStatus(models.TextChoices):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"


class CollectionType(models.TextChoices):
    DOCUMENT = "document"
    MULTIMEDIA = "multimedia"


class DocumentStatus(models.TextChoices):
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class DocumentType(models.TextChoices):
    PDF = "pdf"
    WORD = "word"
    MARKDOWN = "markdown"


class Collection(models.Model):
    title = models.CharField(max_length=256)
    description = models.TextField()
    user = models.BigIntegerField()
    status = models.CharField(max_length=16, choices=CollectionStatus.choices)
    type = models.CharField(max_length=16, choices=CollectionType.choices)
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_updated = models.DateTimeField(auto_now=True)
    gmt_deleted = models.DateTimeField()


class Document(models.Model):
    name = models.CharField(max_length=64)
    user = models.BigIntegerField()
    type = models.CharField(max_length=16, choices=DocumentType.choices)
    status = models.CharField(max_length=16, choices=DocumentStatus.choices)
    size = models.BigIntegerField()
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_deleted = models.DateTimeField()


class Chat(models.Model):
    name = models.CharField(max_length=64)
    user = models.BigIntegerField()
    gmt_created = models.DateTimeField(auto_now_add=True)
    gmt_updated = models.DateTimeField(auto_now=True)
    gmt_deleted = models.DateTimeField()


class User(models.Model):
    name = models.CharField(max_length=256)


class Settings(models.Model):
    key = models.CharField(max_length=512)
    value = models.TextField()
