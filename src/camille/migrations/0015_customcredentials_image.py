import encrypted_fields.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("camille", "0014_agentconfig_model_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customcredentials",
            name="url",
            field=models.URLField(
                default="http://localhost:11434/v1",
                help_text="OpenAI-compatible endpoint used by the LLM model.",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="customcredentials",
            name="image_url",
            field=models.URLField(
                blank=True,
                help_text="OpenAI-compatible endpoint used by the image model. Leave empty to use the same endpoint and API key as the LLM model.",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="customcredentials",
            name="image_api_key",
            field=encrypted_fields.fields.EncryptedCharField(
                blank=True, max_length=255, null=True
            ),
        ),
    ]
