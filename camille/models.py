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
from django.db import models

from camille.llm import LLMModel


class XMPPChannel(models.Model):
    # Could be an user or a muc
    jid = models.CharField(max_length=255, unique=True)
    prompt = models.TextField(default="", blank=True)
    llm_model = models.CharField(
        max_length=64,
        choices=LLMModel.choices,
        default=LLMModel.GEMINI_FLASH,
    )

    def __str__(self):
        return self.jid
