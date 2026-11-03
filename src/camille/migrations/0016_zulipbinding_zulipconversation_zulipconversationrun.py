# Camille - An AI assistant
# Copyright (C) Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("camille", "0015_customcredentials_image"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ZulipBinding",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("zulip_id", models.CharField(max_length=64, unique=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="zulip_binding",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ZulipConversation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(max_length=512, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="ZulipConversationRun",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("messages_json", models.BinaryField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="runs",
                        to="camille.zulipconversation",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
