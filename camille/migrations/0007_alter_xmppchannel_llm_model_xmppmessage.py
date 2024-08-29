# Generated by Django 5.1 on 2024-08-27 15:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("camille", "0006_xmppchannel_llm_model"),
    ]

    operations = [
        migrations.AlterField(
            model_name="xmppchannel",
            name="llm_model",
            field=models.CharField(
                choices=[
                    ("gemini-1.5-flash-latest", "Gemini Flash"),
                    ("gemini-1.5-pro-latest", "Gemini Pro"),
                    ("gemma2", "Gemma 2"),
                ],
                default="gemini-1.5-flash-latest",
                max_length=64,
            ),
        ),
        migrations.CreateModel(
            name="XMPPMessage",
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
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("sender", models.CharField(max_length=255)),
                ("is_agent", models.BooleanField(default=False)),
                ("body", models.TextField()),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="camille.xmppchannel",
                    ),
                ),
            ],
        ),
    ]