from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("camille", "0015_customcredentials_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentconfig",
            name="thinking",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Default (recommended)"),
                    ("off", "Off: fastest, no reasoning"),
                    ("low", "Low: quick answers"),
                    ("medium", "Medium: balanced"),
                    ("high", "High: better on complex questions"),
                    ("max", "Maximum: slowest, most thorough"),
                ],
                default="",
                help_text="How much the model thinks before answering. More thinking gives better answers to hard questions, but is slower and costs more. If unsure, keep Default.",
                max_length=16,
                verbose_name="Reasoning",
            ),
        ),
    ]
