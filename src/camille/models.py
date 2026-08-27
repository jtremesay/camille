from uuid import uuid7

from django.db import models


# Create your models here.
class Organization(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    name = models.CharField(max_length=255)
