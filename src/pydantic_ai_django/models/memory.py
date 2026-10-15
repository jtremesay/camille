from django.db import models


class DjangoMemoryOperation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    fingerprint = models.CharField(max_length=64)
    version = models.TextField(null=True, blank=True)
    existed = models.BooleanField()


class DjangoMemoryFile(models.Model):
    path = models.TextField(unique=True)
    content = models.TextField()
    version = models.BigIntegerField()
    last_operation_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
    )


class DjangoMemoryGeneration(models.Model):
    pass
