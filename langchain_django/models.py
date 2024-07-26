from django.db import models


class DjCheckpoint(models.Model):
    thread_id = models.TextField()
    thread_ts = models.TextField()
    parent_ts = models.TextField(null=True, blank=True, default=None)
    checkpoint = models.BinaryField()
    metadata = models.BinaryField()

    class Meta:
        unique_together = (("thread_id", "thread_ts"),)


class DjWrite(models.Model):
    thread_id = models.TextField()
    thread_ts = models.TextField()
    task_id = models.TextField()
    idx = models.IntegerField()
    channel = models.TextField()
    value = models.BinaryField(null=True, blank=True, default=None)

    class Meta:
        unique_together = (("thread_id", "thread_ts", "task_id", "idx"),)
