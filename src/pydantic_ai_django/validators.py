from typing import Any

from django.core.exceptions import ValidationError


def validate_is_dict(value: Any):
    if not isinstance(value, dict):
        raise ValidationError("Value must be a dictionary.")
