from django.contrib.auth.models import User
from django.db import models


class MattermostBinding(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="mm_binding"
    )
    mm_id = models.CharField(max_length=64, unique=True)
