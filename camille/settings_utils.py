# Camille - An AI assistant
# Copyright (C) 2024 Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os
from pathlib import Path

from django.conf import settings


def get_settings(key, **kwargs):
    # In order of precedence:
    # - docker secret
    # - environment variable
    # - settings.py
    # - default value
    # - raise error
    can_split = False
    try:
        val = os.environ[key]
        can_split = True
    except KeyError:
        try:
            secret_key = os.environ[f"{key}_FILE"]
            val = Path(secret_key).read_text()
            can_split = True
        except KeyError:
            try:
                if kwargs.get("dont_use_settings", False):
                    raise AttributeError

                val = getattr(settings, key)
                can_split = False
            except AttributeError:
                try:
                    val = kwargs["default"]
                    can_split = False
                except KeyError:
                    raise RuntimeError(
                        f"settings key {key} is not defined and no default value was provided"
                    )
    if can_split:
        separator = kwargs.get("separator", None)
        if separator is not None:
            return val.split(separator)

    return val
